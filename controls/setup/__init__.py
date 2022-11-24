import yaml
import logging
from .custom_loggers import GroupWriteRotatingFileHandler
from pathlib import Path

logger = logging.getLogger("controls.setup")


def join(loader, node) -> str:
    """
    Custom tag handler for joining list of strings in yaml.

    Args:
        loader (_type_): _description_
        node (_type_): _description_

    Returns:
        str: Joined list of parameters
    """    
    seq = loader.construct_sequence(node)
    return ''.join([str(i) for i in seq])

yaml.SafeLoader.add_constructor('!join', join)


def enforce_settings_booleans(settings:dict) -> dict:
    """
    Dumb function in case some settings are strings rather than true booleans

    Args:
        settings (dict): settings passed down from click

    Returns:
        dict: true settings
    """    
    
    for item in settings:
        if settings[item] == "True":
            settings[item] = True
        elif settings[item] == "False":
            settings[item] = False
    return settings



def make_config(click_ctx:dict={}) -> dict:
    """
    Grabs the settings from a config file.

    Args:
        click_ctx (dict): context object from click

    Returns:
        dict: settings from config file.
    """
    
    # if user hasn't defined config path in cli args
    if 'verbose' in click_ctx and click_ctx['verbose']:
        handler = [item for item in logger.parent.handlers if item.name == "Stream"][0]
        handler.setLevel(logging.DEBUG)
    # Had to put this in to handle initial call from main.py when creating modes
    if not 'config' in click_ctx:
        click_ctx['config'] = None
    logger.debug(f"Got {click_ctx['config']} for config file")
    if click_ctx['config'] == None:
        # Check user .config/controls directory
        if Path("~/.config/controls").expanduser().joinpath("config.yml").exists():
            settings_path = Path("~/.config/controls").expanduser().joinpath("config.yml")
        # Check user .controls directory
        elif Path("~/.controls").expanduser().joinpath("config.yml").exists():
            settings_path = Path("~/.controls").expanduser().joinpath("config.yml")
        # finally look in the local config
        else:
            if Path(__file__).absolute().parent.parent.parent.joinpath("config.yml").exists:
                settings_path= Path(__file__).absolute().parent.parent.parent.joinpath("config.yml")
            else:
                logger.warning("No config.yml file found. Using empty dictionary")
                return click_ctx
    else:
        if Path(click_ctx['config']).is_dir():
            settings_path = Path(settings_path).joinpath("config.yml")
        elif Path(click_ctx['config']).is_file:
            settings_path = settings_path
        else:
            logger.warning("No config.yml file found. Using empty dictionary")
            return click_ctx
    logger.debug(f"Using {settings_path} for config file.")
    with open(settings_path, "r") as settings:
        try:
            config = yaml.safe_load(settings)
        except yaml.YAMLError as e:
            logger.error(e)
            config = {}
    return enforce_settings_booleans({**config, **click_ctx})


def setup_logger():
    """
    Applies custom formatting to the logger.

    Returns:
        logger: custom logger
    """    
    logger = logging.getLogger('controls')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = GroupWriteRotatingFileHandler(Path(__file__).absolute().parent.parent.parent.joinpath('controls.log'), mode='a',
                                       maxBytes=100000, backupCount=3, encoding=None, delay=False)
    # fh = GroupWriteRotatingFileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'controls.log'), mode='a',
    #                                    maxBytes=100000, backupCount=3, encoding=None, delay=False)
    fh.setLevel(logging.DEBUG)
    fh.name = "File"
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.name = "Stream"
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    stderr_logger = logging.getLogger('STDERR')
    return logger