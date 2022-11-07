import logging
from .excel_functions import get_date_from_access
from .misc import assemble_date_regex, create_date
from pathlib import Path
from datetime import date

logger = logging.getLogger("controls.tools")



def enforce_valid_date(settings:dict, folder:str) -> date:
    """
    Returns a valid date object and an old_db_path for reuse in main function.

    Args:
        folder (str): _description_
        old_db_path (str): _description_

    Returns:
        date: _description_
    """    
    # Okay, we want to hopefully parse the date from the filename.
    logger.debug(f"Running regex on: {folder}")
    date_regex = assemble_date_regex()
    sub_date_raw = date_regex.match(folder)
    if bool(sub_date_raw):
        logger.debug(f"Found date: {sub_date_raw.group()}")
        return create_date(sub_date_raw.group())
    # If that's not possible we want the path to the old_db export containing the date.
    else:
        logger.debug(f"Couldn't find suitable date in path. Attempting to read from access export.")
        if settings['folder']['old_db_path'] == "" or not "old_db_path" in settings['folder']:
            logger.error("No path for old db export, returning None")
            return None
        else:
            logger.debug(f"Attempting to extract date from old database export: {settings['folder']['old_db_path']}")
            if settings['test']:
                folder_name = "MCS-July2022Plate1"
            else:
                folder_name = Path(folder).name
            return get_date_from_access(sample_name=folder_name, tblControls_path=settings['folder']['old_db_path'])
            