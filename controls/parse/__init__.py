from ..tools import enforce_valid_date
from ..tools.excel_functions import read_tsv_string
from ..tools.db_functions import get_control_type_by_name, add_control_to_db, check_samples_against_database
from ..tools.misc import write_output, parse_control_type_from_name, parse_sample_json
from ..tools.subprocesses import run_refseq_masher, pull_from_irida
from ..models import Control
import logging
from pathlib import Path

import json


logger = logging.getLogger("controls.parse")

def main_parse(settings):
    logger.debug(f"PARSE Got settings passed down: {settings}")
    logger.debug(f"Storage = {settings['irida']['storage']}")
    # Perform new pull from irida
    logger.debug(f"Pulling from irida with settings: {settings['irida']}")
    pull_from_irida(settings['irida'])
    # compare storage after pull to samples already in the database and remove any that are the same.
    samples_of_interest = check_samples_against_database(settings=settings)
    if Path(settings['folder']['old_db_path']).exists():
        old_db_path = settings['folder']['old_db_path']
    else:
        old_db_path = ""
    # Perform parsing of any new control samples.
    for folder in samples_of_interest:
        newControl = Control(name=Path(folder).name)
        tsv_file = Path(folder).joinpath(f"{settings['mode']}.tsv")
        sample_name = Path(folder).name
        # if a tsv_file already exists...
        if Path(tsv_file).exists():
            logger.debug(f"Existing tsv file: {tsv_file}, reading...")
            with open(tsv_file, "r") as f:
                tsv_text = f.read()
        # if no tsv file already exists...
        else:
            logger.debug(f"No existing tsv file: {tsv_file}, running refseq_masher for {settings['mode']}")
            tsv_text = run_refseq_masher(settings=settings, folder=folder.__str__())
            logger.debug(f"Writing refseq_masher results to tsv_file: {tsv_file}")
            write_output(tsv_file, tsv_text)
        # If there's an error running refseq we're going make some dummy data from the test files with headers only to fill in the gap
        if tsv_text == None:
            logger.error(f"Failed to write {settings['mode']}.tsv file due to error, Using dummy data.")
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
            logger.warning(f"The {settings['mode']} file for {folder} must have been empty. Using empty dict.")
            reads_json = {}
        # pare down data to only include most relevant results sorted by genus
        reads_json = parse_sample_json(reads_json, settings['mode'])
        if reads_json == None:
            logger.warning(f"JSON for {Path(folder).name} was NONE. Using empty dict instead.")
            reads_json = {}
        # Insert data into Control object 'mode' (contains or matches) column
        setattr(newControl, settings['mode'], json.dumps(reads_json))
        if settings['mode'] != "matches":
            logger.debug(f"{settings['mode']} for {Path(folder).name}: {getattr(newControl, settings['mode'])}")
        logger.debug(f"Attempting to find date with format (YYYY-MM-DD) in folder path.")
        # Uses the old_db_path -- if it's set -- to avoid having to input it for each sample.
        submitted_date = enforce_valid_date(settings, folder=folder.__str__())
        if submitted_date != None:
            newControl.submitted_date = submitted_date
        else:
            logger.error(f"There was no date available for {Path(folder).name}.")
            newControl.submitted_date = None
        # Use regex to determine the control type
        ct_name = parse_control_type_from_name(settings=settings, control_name=sample_name)
        if ct_name == None:
            logger.error(f"Couldn't get control type name from {sample_name}.")
        try:
            ct_name = ct_name.replace("_", "-")
        except  AttributeError as e:
            logger.error(f"Control type name is NONE.")
        logger.debug(f"Control Type Name: {ct_name}")
        # We need to get the object in order to get the targets
        ct_type = get_control_type_by_name(ct_name, settings=settings)
        newControl.controltype = ct_type
        # No sense adding to db if nothing to add.
        if getattr(newControl, settings['mode']) == json.dumps({}) and newControl.submitted_date == None:
            logger.warning(f"Sample {newControl.name} has no {settings['mode']} or date. Skipping")
            continue
        else:
            add_control_to_db(newControl, settings=settings)
    logger.info("The PARSE run has ended.")
