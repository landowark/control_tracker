from tools.db_functions import get_all_Control_Types_names, convert_control_to_dict, get_all_samples_by_control_type
from tools.excel_functions import construct_df_from_json
from tools.vis_functions import create_charts, output_figures
import logging
from datetime import datetime

logger = logging.getLogger("controls.report")

def main_report(settings:dict):
    """
    Performs all decision making and function assignment of reports.

    Args:
        settings (dict): Settings passed down from click.
    """        
    # logger.debug(f"REPORT Got settings passed down: {settings}")
    logger.debug(f"Output folder: {settings['folder']['output']}")
    # Get all names of all control types for grouping.
    ct_types = get_all_Control_Types_names(settings=settings)
    logger.debug(f"CT-TYPES: {ct_types}")
    # Construct dictionary assigning all controls of a type to that key.
    by_type = {ct_type: [convert_control_to_dict(sample, settings=settings) for sample in get_all_samples_by_control_type(ct_type)] for ct_type in ct_types}
    # logger.debug(f"By type: {by_type}")
    # Convert dictionaries to dataframes (Also writes xlsx)
    by_type = [construct_df_from_json(settings=settings, group_name=group, group_in=by_type[group], output_dir=settings['folder']['output']) for group in by_type]
    for ct_type in by_type:
        logger.debug(f"Group name: {list(ct_type.keys())[0]}")
        # Grab list name for chart title
        group_name = list(ct_type.keys())[0]
        # Construct stacked bar chart.
        figs = create_charts(settings=settings, df=ct_type[group_name], group_name=group_name)
        # Write bar chart to html file.
        output_figures(settings=settings, figs=figs, group_name=group_name)
    logger.info(f"The REPORT run has ended as {datetime.now()}.")