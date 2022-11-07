import logging
import re
from datetime import datetime, date
from pathlib import Path


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
    regexes = [fr"{item}" for item in settings['ct_type_regexes']]
    temp = '(?:% s)' % '|'.join(regexes)
    matches = re.match(temp, control_name)
    logger.debug(f"Regex matches: {matches}")
    try:
        ct_type = [item for item in matches.groupdict().keys() if matches.groupdict()[item] != None][0]
    except AttributeError as e:
        return None
    return ct_type


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
    new_dict = {}
    # logger.debug(f"Parsing sample json: {json_in}")
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

# def split_json_into_cts(json_in:dict, ct_types:list) -> dict:
#     """
#     Sorts dictionary of samples into control types.
#     ***Depreciated with creation of sqlalchemy query for controltype instances***

#     Args:
#         json_in (dict): dictionary of all samples
#         ct_types (list): 

#     Returns:
#         dict: _description_
#     """    
#     logger.debug(f"Using ct_types: {ct_types}")
#     out_dict = {}
#     for typ in ct_types:
#         new_list = []
#         for sample in json_in:
#             logger.debug(f"Sample: {sample.keys()}")
#             try:
#                 if sample['controltype']['name'] == typ:
#                     new_list.append(sample)
#             except KeyError:
#                 continue
#         out_dict[typ] = new_list
#     return out_dict


# def get_user_input_date(old_db_path):
#     """
#     Gets user input for either a date or path to the excel file where the date is kept.
#     ***Depreciated since we can't have user input while running sbatch.***

#     Returns:
#         tuple: 0: Contains date, 1: contains file path
#     """    
#     user_input = input("I couldn't find the submission date in the folder name. Please input the date (YYYY-MM-DD) or the path to the old database export: ")
#     date_regex = assemble_date_regex()
#     sub_date_raw = date_regex.match(user_input)
#     if bool(sub_date_raw):
#         logger.debug(f"Found date from user input: {sub_date_raw.group()}")
#         return (create_date(sub_date_raw.group()), old_db_path)
#     elif Path(user_input).exists:
#         logger.debug(f"Found file for {user_input}.")
#         return (None, user_input)
#     else:
#         logger.error(f"Couldn't get db_path or date from input")
#         return (None, old_db_path)
