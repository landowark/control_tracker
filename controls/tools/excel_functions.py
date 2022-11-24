import pandas as pd
from pandas import DataFrame
import logging
from datetime import date
from pathlib import Path
from collections.abc import MutableMapping
from numpy import array as npa
from io import StringIO

logger = logging.getLogger("controls.tools.excel_functions")

modes = ['contains', 'matches']

def read_tsv(filein: str) -> str:
    """
    Reads a tsv file into string

    Args:
        filein (str): path to the tsv file

    Returns:
        str: tsv file contents as string
    """
    if Path(filein).exists:
        with open(filein, "r") as f:
            text = f.read()
        return text
        # try:
        #     df = pd.read_csv(filein, sep='\t', header=0)
        # except pd.errors.EmptyDataError as e:
        #     logger.error(f"Got an empty contains data file: {filein}, returning None.")
        #     return None
        # except FileNotFoundError as e:
        #     logger.error(f"Somehow a non-existant file {filein} got past my check, returning None.")
        #     return None
    else:
        logger.error(f"Could not find tsv file at {filein}. Returning None.")
        return None
    #     df = DataFrame()
    # logger.debug(f"Dataframe: {df}")
    # # return df.dropna()
    # return df


def read_tsv_string(string_in:str) -> DataFrame:
    """
    Reads tsv string from memory

    Args:
        string_in (str): tsv data.

    Returns:
        DataFrame: data out
    """
    logger.debug(f"TSV string in: {type(string_in)}")
    try:
        string_in = StringIO(string_in)
    except TypeError as e:
        string_in = StringIO(string_in.decode("utf-8"))
    try:
        return pd.read_csv(string_in, sep="\t")
    except pd.errors.EmptyDataError as e:
        logger.error(f"Got empty tsv file. Returning empty dataframe.")
        return DataFrame()

def read_excel(filein: str):
    """
    Reads an xlsx file into a pandas dataframe

    Args:
        filein (str): path to the xslx file

    Returns:
        Dataframe: xlsx file contents as pandas dataframe
    """
    if Path(filein).exists:
        # logger.debug(f"Dataframe: {df}")
        return pd.read_excel(filein, engine="openpyxl", index_col=0).dropna()
    else:
        logger.error(f"Could not find xlsx file at {filein}. Returning None.")
        return None
    

def get_date_from_access(sample_name:str, tblControls_path:str) -> date:
    """
    Reads a submitted date from outside xlsx file.

    Args:
        sample_name (str): sample name for which we want the date.
        tblControls_path (str): location of the external xlsx file.

    Returns:
        date: a datetime date object.
    """    
    if Path(tblControls_path).exists:
        df = read_excel(tblControls_path)
        try:
            sub_date_item = df.loc[df['Control Name'] == sample_name, "Submission Date"].item()
        except ValueError as e:
            logger.error(f"Couldn't find {sample_name} in the table. Returning nothing!")
            return None
        logger.debug(f"Got df date item {sub_date_item}")
        sub_date = sub_date_item.date()
        logger.debug(f"Got df date {sub_date}")
        return sub_date
    else:
        logger.error(f"Path: {tblControls_path} does not exist, returning None.")
        return None


def construct_df_from_json(settings:dict, group_name:str, group_in:dict, output_dir:str) -> dict:
    """
    generates a flat list from all of the keys in each sample's contains or matches section

    Args:
        settings (dict): settings passed down from click
        group_name (str): string denoting control type
        group_in (dict): dictionary to be flattened
        output_dir (str): Where we're storing the dictionary as an xlsx file. 

    Returns:
        dict: _description_
    """    
    # 
    logger.debug(f"Group in: {group_in}")
    targets1 = group_in[0]['controltype']['targets']
    targets2 = [f"{target}*" for target in targets1]
    targets = [val for pair in zip(targets1, targets2) for val in pair]
    for sample in group_in:
        # All should already have the same controltype
        try:
            del sample['controltype']
        except KeyError:
            pass
    # Flatten dictionary.
    group_in = [flatten_dict(sample) for sample in group_in]
    logger.debug(f"Flattened dictionary: {group_in}")
    sorts = ['submitted_date', "genus"]
    sorts[-1:-1] = [f"{mode}_ratio" for mode in modes]
    # Set descending for any columns that have "{mode}" in the header.
    ascending = [False if item.split("_")[0] in modes else True for item in sorts]
    logger.debug(f"Ascending: {list(zip(sorts, ascending))}")
    # create and merge dataframes.
    df = pd.concat(create_df_from_flattened_dict(group_in, targets)) \
        .sort_values(by=sorts, ascending=ascending) \
        .reset_index().drop("index",1)
    df = df.dropna()
    if not "test" in settings:
        logger.debug(f"Writing to: {Path(output_dir).joinpath(group_name)}.xlsx")
        df.to_excel(f"{Path(output_dir).joinpath(group_name)}.xlsx", engine="openpyxl")
    return {group_name: df}


def create_df_from_flattened_dict(flatteneds:list, targets:list) -> list:
    """
    Generate list of dataframes from a list of dictionaries containing all samples of a controltype. 

    Args:
        flatteneds (list): sample dictionaries
        targets (list): the targets of the parent controltype

    Returns:
        list: 
    """    
    dfs = []
    for item in flatteneds:
        df = DataFrame()
        del item['name']
        logger.debug(f"Item we're trying to DFify: {item['submitted_date']}")
        my_date = item.pop("submitted_date")
        df['genus'] = [genus.replace("contains.", "").replace(".contains_hashes", "") for genus in item if ".contains_hashes" in genus]
        df['submitted_date'] = my_date
        df['target'] = df['genus'].apply(lambda x: "Target" if x in targets else "Off-target")
        for mode in modes:
            df[f'{mode}_ratio'] = pd.Series(npa([item[genus] for genus in item if f"{mode}_ratio" in genus]))
            df[f'{mode}_hashes'] = pd.Series(npa([item[genus] for genus in item if f"{mode}_hashes" in genus]))
        columns = ['submitted_date', 'genus', 'target']
        columns[-1:-1] = [item for sublist in [[f"{mode}_ratio", f"{mode}_hashes"] for mode in modes] for item in sublist]
        df = df[columns].fillna("")
        df.drop(df[(df.genus == "") | (df.genus == "NaN")].index, inplace=True)
        dfs.append(df)
    return dfs


def flatten_dict(d: MutableMapping, parent_key: str = '', sep: str ='.') -> MutableMapping:
    """
    Flatten a dictionary to a single level, merging keys.

    Args:
        d (MutableMapping): input dictionary
        parent_key (str, optional): _description_. Defaults to ''.
        sep (str, optional): character to seperate keys when merging. Defaults to '.'.

    Returns:
        MutableMapping: output dictionary.
    """    
    items = []
    for k, v in d.items():
        logger.debug(f"Attempting flatten with {k} as key and {v} as value.")
        try:
            new_key = parent_key + sep + k if parent_key else k
        except TypeError as e:
            logger.error("Got None as key, skipping...")
            continue
        logger.debug(f"Flattening dict using new key: {new_key}")
        if isinstance(v, MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    logger.debug(f"Here is the list of flattened dict: {items}")
    return dict(items)


def get_unique_values_in_df_column(df: DataFrame, column_name: str) -> list:
    """
    _summary_

    Args:
        df (DataFrame): _description_
        column_name (str): _description_

    Returns:
        list: _description_
    """    
    return sorted(df[column_name].unique())
