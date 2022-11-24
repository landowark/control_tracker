import logging
import re
from datetime import datetime, date
from pathlib import Path
from difflib import get_close_matches
from typing import Tuple


logger = logging.getLogger("controls.tools.misc")


def write_output(filename:Path, output:str):
    """
    Writes to file. Takes care of decoding.

    Args:
        filename (Path): File to write to.
        output (str): Content to write.
    """    
    with open(filename.__str__(), "w") as f:
        logger.debug(f"Writing to {filename}")
        try:
            output = output.decode("utf-8")
        except AttributeError as e:
            logger.error(f"Output string was not byteslike object.")
        f.write(output)


def assemble_date_regex() -> re.Pattern:
    """
    Creates regex pattern for common date formats.

    Returns:
        re.Pattern: compiled pattern.
    """    
    return re.compile(r"20\d{2}-?\d{2}-?\d{2}")


def create_date(raw_date:str) -> date:
    """
    Creates date object from string. Handles '-' presence/absence

    Args:
        raw_date (str): _description_

    Returns:
        date: _description_
    """    
    if "-" in raw_date:
        return datetime.strptime(raw_date, "%Y-%m-%d").date()
    else:
        return datetime.strptime(raw_date, "%Y%m%d").date()
        

def parse_control_type_from_name(settings:dict, control_name:str) -> str:
    """
    Checks for control type in string. Uses joined ct_type_regexes defined in config.yml and pulled into settings. 

    Args:
        settings (dict): Settings passed down from click.
        control_name (str): Sample name

    Returns:
        str: Parsed control type.
    """
    if 'ct_type_regexes' in settings:
        regexes = [fr"{item}" for item in settings['ct_type_regexes']]
        temp = '(?:% s)' % '|'.join(regexes)
        # Note: matches here does not refer to the mode matches, but regex pattern matches.
        matches = re.match(temp, control_name)
        logger.debug(f"Regex matches: {matches}")
        try:
            ct_type = [item for item in matches.groupdict().keys() if matches.groupdict()[item] != None][0]
        except AttributeError as e:
            return None
        return ct_type
    else:
        logger.warning(f"No control regexes found, going to return closest match to list of control types.")
        types = list(settings['control_types'].keys())
        return get_close_matches(control_name, types)[0]
    


def parse_date(in_date:date) -> str:
    """
    Creates date string from date object

    Args:
        in_date (date): input date object

    Returns:
        str: string in the format %Y-%m-%d
    """        
    try:
        return in_date.strftime("%Y-%m-%d")
    except AttributeError as e:
        return None


def parse_sample_json(json_in:dict, mode:str) -> dict:
    """
    Converts sample dictionary into more convenient organization. Constructs hash ratios, sheds extraneous data.

    Args:
        json_in (dict): sample data from tsv in
        mode (str): "contains" or "matches" for proper parsing of column names.

    Returns:
        dict: flattened dictionary.
    """
    logger.debug(f"Parsing sample json: {mode}") 
    if mode == "contains" or mode == "matches":
        new_dict = process_refseq_dict(json_in=json_in, mode=mode)
    elif mode == "kraken":
        new_dict = process_kraken_dict(json_in=json_in)
    return new_dict


def process_refseq_dict(json_in:dict, mode:str) -> dict:
    new_dict = {}
    for top_key in json_in.keys():
        genus = json_in[top_key]['taxonomic_genus']
        if mode == "contains":
            hashes = json_in[top_key]['shared_hashes']
        if mode == "matches":
            hashes = json_in[top_key]['matching']
        split_ratio = int(hashes.split("/")[0]) / int(hashes.split("/")[1])
        if genus in new_dict.keys():
            if f"{mode}_ratio" in new_dict[genus]:
                if  split_ratio > new_dict[genus][f'{mode}_ratio']:
                    new_dict[genus][f'{mode}_ratio'] = split_ratio
                    new_dict[genus][f'{mode}_hashes'] = hashes
            else:
                new_dict[genus][f'{mode}_ratio'] = split_ratio
                new_dict[genus][f'{mode}_hashes'] = hashes
        else:
            new_dict[genus] = {}
            new_dict[genus][f'{mode}_hashes'] = hashes
            new_dict[genus][f'{mode}_ratio'] = split_ratio
    return new_dict


def process_kraken_dict(json_in:dict, mode:str="kraken") -> dict:
    new_dict = {}
    for top_key in json_in.keys():
        if json_in[top_key]["U"] == "G":
            genus = json_in[top_key]["unclassified"].strip()
            new_dict[genus] = {}
            for ii, (k, v) in enumerate(json_in[top_key].items()):
                # Due to varying number of whitespaces in json, have to fall back to string contains.
                # logger.debug(f"Key {ii} in json_in: {k.strip()}")
                if ii == 0:
                    new_dict[genus]['percent_reads'] = v
                elif ii == 1:
                    new_dict[genus]['number_reads'] = v
    return new_dict



def get_date_from_filepath(inpath:Path) -> date:
    """
    Returns a valid date from filepath if found.

    Args:
        inpath (Path): directory being parsed

    Returns:
        date: Submission date.
    """    
    # Okay, we want to hopefully parse the date from the filename.
    logger.debug(f"Running regex on: {inpath.absolute().__str__()}")
    date_regex = assemble_date_regex()
    sub_date_raw = date_regex.search(inpath.absolute().__str__())
    print(inpath.absolute().__str__(), sub_date_raw)
    if bool(sub_date_raw):
        logger.debug(f"Found date: {sub_date_raw.group()}")
        return create_date(sub_date_raw.group())
    else:
        return None
        
        
def get_date_from_file_ctime(inpath: Path, filetype:str="") -> date:
    """
    Returns a valid date from fastq creation time

    Args:
        inpath (Path): file being parsed. If file is a directory, takes most recent file.

    Returns:
        date: submitted date.
    """
    if inpath.is_dir():
        relevant_file = get_most_recent_file(list(inpath.glob(f'*.{filetype}')))
    else:
        relevant_file = inpath
    logger.warning(f"Finding date from fastq creation time of {relevant_file}.")
    try:
        return datetime.fromtimestamp(relevant_file.stat().st_ctime).date()
    except:
        return None

    
def get_most_recent_file(infiles:list) -> Path:
    print([f"{file}: {datetime.fromtimestamp(file.stat().st_ctime).date()}" for file in infiles])
    most_recent_date = max([datetime.fromtimestamp(file.stat().st_ctime).date() for file in infiles])
    most_recent_file = [file for file in infiles if get_date_from_file_ctime(file) == most_recent_date][0]
    return most_recent_file


def alter_genera_names(input_dict:dict) -> dict:
    """
    Adds an asterisk to all key names in input dictionary

    Args:
        input_dict (dict): input dictionary

    Returns:
        dict: output dictionary
    """    
    return {f"{k}*":v for k,v in input_dict.items() if k != 'nan'}


def get_relevant_fastq_files(folder:Path) -> Tuple[Path, Path]:
    fastqs = list(folder.glob('*.fastq'))
    if len(fastqs) == 2:
        return tuple(fastqs)
    elif len(fastqs) > 2:
        logger.debug(f"Got more than 2 fastq files in {folder.__str__()}. Attempting to pare down pairs.")
        most_recent = get_date_from_file_ctime(get_most_recent_file(fastqs))
        fastqs = [item.absolute().__str__() for item in fastqs if get_date_from_file_ctime(item) == most_recent]
        return tuple(fastqs)
    else:
        logger.error("Non-standard number of fastq ")
