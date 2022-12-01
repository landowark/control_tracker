from tools import enforce_valid_date
from tools.excel_functions import read_tsv_string, read_tsv
from tools.db_functions import get_control_type_by_name, add_control_to_db, check_samples_against_database
from tools.misc import write_output, parse_control_type_from_name, parse_sample_json, alter_genera_names, get_relevant_fastq_files
from tools.subprocesses import run_refseq_masher, pull_from_irida, run_kraken
from models import Control
import logging
from pathlib import Path
from datetime import datetime
import json


logger = logging.getLogger("controls.parse")

def main_parse(settings:dict):
    """
    Performs decision making and function assignment for parsing input data.

    Args:
        settings (dict): settings passed down from click.
    """        
    logger.debug(f"PARSE Got settings passed down: {settings}")
    
    logger.debug(f"Storage = {settings['irida']['storage']}")
    # Perform new pull from irida
    logger.debug(f"Pulling from irida with settings: {settings['irida']}")
    pull_from_irida(settings['irida'])
    # loop through for each mode being run
    for mode in settings['mode']:
        logger.debug(f"Running parse for {mode}")
        # compare storage after pull to samples already in the database and remove any that are the same.
        samples_of_interest = check_samples_against_database(settings=settings, mode=mode)
        # Perform parsing of any new control samples.
        for folder in samples_of_interest:
            sample_name = Path(folder).name
            newControl = Control(name=sample_name)
            tsv_file = Path(folder).joinpath(f"{sample_name}_{mode}.tsv")
            # Get the control type from the database.
            ct_name = parse_control_type_from_name(settings=settings, control_name=sample_name)
            if ct_name == None:
                logger.error(f"Couldn't get control type name from {sample_name}.")
            try:
                ct_name = ct_name.replace("_", "-")
            except  AttributeError as e:
                logger.error(f"Control type name is NONE, skipping this sample.")
                continue
            logger.debug(f"Control Type Name: {ct_name}")
            # We need to get the object in order to get the targets
            ct_type = get_control_type_by_name(ct_name, settings=settings)
            newControl.controltype = ct_type
            # if a tsv_file already exists...
            if Path(tsv_file).exists():
                logger.debug(f"Existing tsv file: {tsv_file}, reading...")
                tsv_text = read_tsv(tsv_file)
            elif Path(folder).joinpath(f"{mode}.tsv").exists():
                tsv_text = read_tsv(Path(folder).joinpath(f"{mode}.tsv"))
                write_output(tsv_file, tsv_text)
            # if no tsv file already exists...
            else:
                logger.debug(f"No existing tsv file: {tsv_file}, running analysis subprocess for {mode}")
# TODO: More stuff like this, for the json parser.
                # setting parse function based on the mode
                if mode == "contains" or mode == "matches":
                    func = function_map["process_refseq_masher"]
                else:
                    func = function_map[f"process_{mode}"]
                tsv_text = func(settings=settings, folder=folder.__str__(), mode=mode, tsv_file=tsv_file)
            # If there's an error running refseq we're going make some dummy data from the test files with headers only to fill in the gap
            if tsv_text == None:
                logger.error(f"Failed to write {mode}.tsv file due to error, Using dummy data.")
                # Set tsv_text to column headers only.
                dummy_path = Path(__file__).absolute().parent.parent.joinpath("dummy.tsv")
                if dummy_path.exists():
                    logger.debug(f"Dummy path {dummy_path} exists, grabbing dummy data.")
                    with open(dummy_path.__str__(), "r") as f:
                        tsv_text = f.readlines()[0]
            # create dataframe from the text of tsv or directly from refseq_masher
            try:
                reads_json = read_tsv_string(tsv_text).T.to_dict()
            except AttributeError as e:
                logger.warning(f"The {mode} file for {folder} must have been empty. Using empty dict.")
                reads_json = {}
            # pare down data to only include most relevant results sorted by genus
            reads_json = parse_sample_json(reads_json, mode=mode)
            if reads_json == None:
                logger.warning(f"JSON for {Path(folder).name} was NONE. Using empty dict instead.")
                reads_json = {}
            # Insert data into Control object 'mode' (contains or matches) column
            logger.debug(f"Attempting to find date with format (YYYY-MM-DD) in folder path.")
            # Uses the old_db_path -- if it's set -- to avoid having to input it for each sample.
            newControl.submitted_date, got_fastq_date = enforce_valid_date(settings=settings, inpath=Path(folder))
            if got_fastq_date and reads_json != {}:
                logger.warning(f"Got date from fastq file, adding asterisks to genera names.")
                reads_json = alter_genera_names(reads_json)
            setattr(newControl, mode, json.dumps(reads_json))
            if getattr(newControl, mode) == json.dumps({}) and newControl.submitted_date == None:
                logger.warning(f"Sample {newControl.name} has no {settings['mode']} or date. Skipping")
                continue
            else:
                add_control_to_db(newControl, mode=mode, settings=settings)
    logger.info(f"The PARSE run has ended at {datetime.now()}.")


# Below this point are the individual parsing functions. They must be named "parse_{mode name}" and
# take only settings, folder, mode and tsv_file in order to hook into the main function


def process_refseq_masher(settings:dict, folder:str, mode:str, tsv_file:Path) -> str:
    """
    Gets refseq masher results.

    Args:
        settings (dict): settings passed down from click
        folder (str): folder to be run
        mode (str): 'contains' or 'matches' from main parser.
        tsv_file (Path): filepath to check for already existing results.

    Returns:
        str: output from process
    """    
    tsv_text = run_refseq_masher(settings=settings, folder=folder.__str__(), mode=mode)
    logger.debug(f"Writing refseq_masher results to tsv_file: {tsv_file}")
    try:
        write_output(tsv_file, tsv_text)
    except:
        logger.error("No tsv text found, using NONE")
        tsv_text = None
    return tsv_text


def process_kraken(settings:dict, folder:str, tsv_file:Path, mode:str='kraken') -> str:
    """
    _summary_

    Args:
        settings (dict): settings passed down from click
        folder (str): folder to be run
        tsv_file (Path): _description_
        mode (str, optional): from main parser. Defaults to 'kraken'.

    Returns:
        str: output from process
    """    
    run_kraken(settings=settings, folder=folder.__str__(), fastQ_pair=get_relevant_fastq_files(Path(folder)), tsv_file=tsv_file)
    return read_tsv(tsv_file)


########This must be at bottom of module###########

function_map = {}
for item in dict(locals().items()):
    try:
        if dict(locals().items())[item].__module__ == __name__:
            try:
                function_map[item] = dict(locals().items())[item]
            except KeyError:
                pass
    except AttributeError:
        pass
###################################################