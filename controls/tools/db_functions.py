import json
from tkinter import N
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, engine
from models import *
from pathlib import Path
import logging
from .misc import parse_date


logger = logging.getLogger("controls.tools.db_functions")

def make_engine(settings:dict={}):
    """
    Create engine from db path in settings

    Args:
        settings (dict): settings passed down from click. Defaults to {}.
    """
    if 'db_path' in settings:
        db_path = settings['db_path']
    else:
        db_path = Path(__file__).parent.parent.parent.absolute().joinpath("controls.db").__str__()
    logger.debug(f"db_path={db_path}")
    engine = create_engine(f"sqlite:///{db_path}")
    return engine

def get_all_Control_Sample_names(settings:dict={}, engine:engine=None) -> list:
    """
    Grabs all control sample names from the db.

    Args:
        settings (dict): settings passed down from click. Defaults to {}.

    Returns:
        list: names list
    """
    if engine == None:
        session = Session(make_engine(settings=settings))
    else:
        session = Session(engine)
    samples = session.query(Control).filter(Control.submitted_date.is_not(None)).order_by(Control.submitted_date.desc()).all()
    samples = [sample.name for sample in samples]
    logger.debug(f"Samples: {samples}")
    session.close()
    return samples

def get_all_Control_Sample_names_if_mode_not_empty(mode:str, settings:dict={}, engine:engine=None) -> list:
    """
    Grabs all control sample names from the db if the mode field is not empty.
    Used for eliminating already seen samples from processing.

    Args:
        settings (dict): settings passed down from click. Defaults to {}.

    Returns:
        list: names list
    """    
    if engine == None:
        session = Session(make_engine(settings=settings))
    else:
        session = Session(engine)
    samples = session.query(Control).filter(Control.submitted_date.is_not(None)).order_by(Control.submitted_date.desc()).all()
    samples = [sample.name for sample in samples if not getattr(sample, mode) is None ]
    logger.debug(f"Samples: {samples}")
    session.close()
    return samples


def get_all_Control_Types_names(settings:dict={}, engine:engine=None) -> list:
    """
    Grabs all control type names from db.

    Args:
        settings (dict): settings passed down from click. Defaults to {}.

    Returns:
        list: names list
    """    
    if engine == None:
        session = Session(make_engine(settings=settings))
    else:
        session = Session(engine)
    conTypes = session.query(ControlType).all()
    conTypes = [conType.name for conType in conTypes]
    logger.debug(f"Control Types: {conTypes}")
    session.close()
    return conTypes


def get_control_type_by_name(type_name:str, settings:dict={}, engine:engine=None) -> ControlType:
    """
    Queries for control type based on a string.

    Args:
        type_name (str): string to query against.
        settings (dict): settings passed down from click. Defaults to {}.

    Returns:
        ControlType: Control type as an object.
    """    
    if engine == None:
        session = Session(make_engine(settings=settings))
    else:
        session = Session(engine)
    ct = session.query(ControlType).filter_by(name=type_name).first()
    session.close()
    if ct != None:
        logger.debug(f"Got control type: {ct.name}")
    else:
        logger.error(f"Couldn't get control type from db. Returning None")
        return None
    return ct

def get_control_type_by_id(type_id:int, settings:dict={}, engine:engine=None) -> ControlType:
    """
    Queries for control type based on an integer.

    Args:
        type_name (str): string to query against.
        settings (dict): settings passed down from click. Defaults to {}.

    Returns:
        ControlType: Control type as an object.
    """    
    if engine == None:
        session = Session(make_engine(settings=settings))
    else:
        session = Session(engine)
    ct = session.query(ControlType).filter_by(id=type_id).first()
    session.close()
    if ct != None:
        logger.debug(f"Got control type: {ct.name}")
    else:
        logger.error(f"Couldn't get control type from db. Returning None")
        return None
    return ct

def add_control_to_db(control:Control, mode:str, settings:dict={}, engine:engine=None):
    """
    Write function for control object.

    Args:
        control (Control): Control object to add to db.
        settings (dict): settings passed down from click. Defaults to {}.
    """    
    if engine == None:
        session = Session(make_engine(settings=settings))
    else:
        session = Session(engine)
    logger.debug(f"Adding {control.name} to database.")
    check = session.query(Control).filter_by(name=control.name).first()
    if check:
        logger.warning(f"Object {check} already exists in database. Running update.")
        setattr(check, mode, getattr(control, mode))
    else:
        local_object = session.merge(control)
        session.add(local_object)
    session.commit()
    session.close()


def get_control_by_name(name:str, settings:dict={}, engine:engine=None) -> Control:
    """
    Queries for a control base on the name string.

    Args:
        name (str): name of the control in the database
        settings (dict): settings passed down from click. Defaults to {}.

    Returns:
        Control: Control object.
    """    
    if engine == None:
        session = Session(make_engine(settings=settings))
    else:
        session = Session(engine)
    control = session.query(Control).filter_by(name=name).first()
    logger.debug(f"Got {control.name} from the db.")
    return control


def convert_control_to_dict(control:Control, settings:dict={}, engine:engine=None) -> dict:
    """
    Parses control object in to a suitable dictionary.

    Args:
        control (Control): Control object to be converted.

    Returns:
        dict: contains everything you need to know about the control in easy to handle dictionary.
    """
    if engine == None:
        engine = make_engine()
    control = control.__dict__
    for mode in ["contains", "matches"]:
        try:
            control[mode] = json.loads(control[mode])
        except TypeError as e:
            logger.error(f"No values in {control[mode]} for {control['name']}")
            control[mode] = {}
    try:
        del control['_sa_instance_state']
    except KeyError:
        pass
    try:
        del control['id']
    except KeyError:
        pass
    control['submitted_date'] = parse_date(control['submitted_date'])
    try:
        control['controltype'] = get_control_type_by_id(type_id=control['parent_id'], engine=engine).__dict__
        del control['controltype']['_sa_instance_state']
        del control['controltype']['id']
        del control['parent_id']
        logger.debug(f"Targets: {control['controltype']['targets']}")
    except AttributeError as e:
        logger.error(f"Control {control['name']} has no control type.")
    except KeyError:
        pass
    return control


def check_samples_against_database(settings:dict, mode:str, engine:engine=None) -> list:
    """
    Checks folder list against database to get new samples.

    Args:
        settings (dict): from click and config

    Returns:
        list: all sample folders whose name not in db.
    """    
    # check if mode column is empty.
    db_samples = get_all_Control_Sample_names_if_mode_not_empty(mode=mode, settings=settings, engine=engine)
    logger.debug(f"Checking against: {db_samples}")
    if 'test' in settings:
        samples_of_interest = [sample for sample in ['test1', 'test2', 'test3', 'test4', 'test5', 'test6'] if sample not in db_samples]
    else:
        project_dir = Path(settings['irida']['storage']).joinpath(settings['irida']['project_name'])
        logger.debug(f"Checked folder names: {[sample.name for sample in project_dir.iterdir() if sample.is_dir()]}")
        samples_of_interest = [sample.__str__() for sample in project_dir.iterdir() if sample.is_dir() and sample.name not in db_samples]
    logger.debug(f'Folders for samples not in db: {samples_of_interest}')
    return samples_of_interest


def get_all_samples_by_control_type(ct_type:str, settings:dict={}, engine:engine=None) -> list:
    """
    Returns a list of control objects that are instances of the input controltype.

    Args:
        ct_type (str): Name of the control type.
        settings (dict, optional): Settings passed down from click. Defaults to {}.

    Returns:
        list: Control instances.
    """
    if engine == None:
        session = Session(make_engine(settings=settings))
    else:
        session = Session(engine)
    thing = session.query(ControlType).filter_by(name=ct_type).first()
    return thing.instances


def create_control_types(settings:dict, engine:engine=None) -> None:
    """
    Creates control types based on config settings

    Args:
        settings (dict): settings passed down from click
    """
    if engine == None:
        session = Session(make_engine(settings=settings))
    else:
        session = Session(engine)
    for item in settings['control_types']:
        logger.debug(f"Creating control type {item}")
        ct = ControlType(name=item, targets=settings['control_types'][item])
        session.add(ct)
    session.commit()
    session.close()
