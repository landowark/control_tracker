import logging
from .excel_functions import get_date_from_access
from .misc import get_date_from_filepath, get_date_from_file_ctime
from pathlib import Path
from datetime import date
from typing import Tuple

logger = logging.getLogger("controls.tools")



def enforce_valid_date(settings:dict, inpath:Path) -> Tuple[date, bool]:
    """
    Returns a valid date object and how it was obtained.

    Args:
        settings (dict): settings passed down from click
        inpath (Path): path with relevant files to obtain date from.

    Returns:
        Tuple[date, bool]: Date and if it was obtained using file creation time.
    """    
    # Okay, we want to hopefully parse the date from the filename.
    logger.debug(f"Running regex on: {inpath.absolute().__str__()}")
    got_fastq_date = False
    sub_date = get_date_from_filepath(inpath=inpath)
    # If that's not possible we want the path to the old_db export containing the date.
    if sub_date == None:
        if "old_db_path" in settings['folder'] and settings['folder']['old_db_path'] != "":
            logger.debug(f"Attempting to extract date from old database export: {settings['folder']['old_db_path']}")
            folder_name = Path(inpath).name
            sub_date = get_date_from_access(sample_name=folder_name, tblControls_path=settings['folder']['old_db_path'])
        else:
            sub_date = None
    if sub_date == None:
        logger.debug(f"Old date methods failed. Falling back to fast creation time.")
        sub_date = get_date_from_file_ctime(inpath=inpath, filetype="fastq")
        got_fastq_date = True
    return (sub_date, got_fastq_date)
    
    
    
    
    # else:
    #     logger.debug(f"Couldn't find suitable date in path. Attempting to read from access export.")
    #     if settings['folder']['old_db_path'] == "" or not "old_db_path" in settings['folder']:
    #         relevant_file = list(inpath.glob('*.fastq'))[0]
    #         logger.warning(f"Failed to find date. Falling back to fastq creation time of {relevant_file}.")
    #         return datetime.fromtimestamp(relevant_file.stat().st_ctime).date()
    #     else:
            