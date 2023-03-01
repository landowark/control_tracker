from subprocess import check_output, CalledProcessError 
import logging
import sys
from pathlib import Path

logger = logging.getLogger("controls.tools.subprocesses")

def run_refseq_masher(settings:dict, folder:str, mode:str):
    """
    Runs commandline utility to generate contains file using settings from config.yml

    Args:
        settings (dict): the settings dictionary
        folder (str): folder to run refseq masher on

    Returns:
        _type_: str
    """
    logger.debug(f"Attempting refseq_masher on {folder}...")
    verbose = ""
    if settings['verbose']:
        verbose = "--verbose"
    try:
        out = check_output(['refseq_masher', verbose, mode, folder])
        # logger.info(f"Refseq-masher result: {out}")
        return out
    except CalledProcessError as e:
        logger.error(f"There was a problem running refseq_masher for {folder}: {e}.")
#     else:
#         try:
#                 out = check_output(['refseq_masher', mode, folder])
#                 # logger.info(f"Refseq-masher result: {out}")
#                 return out
#         except CalledProcessError as e:
#                 logger.error(f"There was a problem running refseq_masher for {folder}: {e}.")

def run_kraken(settings:dict, folder:str, fastQ_pair:tuple, tsv_file:str="kraken.tsv"):
     logger.debug(f"Running Kraken2 on {fastQ_pair}")
     file1 = fastQ_pair[0]
     file2 = fastQ_pair[1]
     try:
        out = check_output(['kraken2', 
                '--db', 
                settings['kraken2']['db_path'], 
                "--paired", 
                "--report",
                Path(folder).joinpath(tsv_file).absolute().__str__(), 
                file1,
                file2
                ])
        return out
     except CalledProcessError as e:
        logger.error(f"There was a problem running kraken for {folder}: {e}.")



def pull_from_irida(irida_settings:dict):
    """
    Runs commandline utility to pull samples from irida using settings found in config.yml
    See help for irida ngsArchiveLinker.ps1 v1.1.1 below

    Args:
        irida_settings (dict): settings used to communicate with irida.

    Returns:
        _type_: str
    """
    try:    
        out = check_output(['ngsArchiveLinker.pl', '-p', str(irida_settings['project_number']), '-t', 'fastq,assembly', '--username', irida_settings['username'], '--password', irida_settings['password'], '-o', irida_settings['storage'],  '--ignore'])
        logger.info(f"Irida result: {out}")
        return out
    except CalledProcessError as e:
        logger.error(f"There was a problem pulling from Irida: {e}. Nothing worth doing, so exiting.")
        # sys.exit()


'''Usage:
    ngsArchiveLinker.pl -b <API URL> -p <projectId> -o <outputDirectory> [-s
    <sampleId> ...] [-t <filetype>]

Options:
    -p, --projectId [ARG]
            The ID of the project to get data from. (required)

    -o, --output [ARG]
            A directory to output the collection of links. (Default: Current
            working directory)

    -c, --config [ARG]
            The location of the config file. Not required if --baseURL
            option is used. (Default: $HOME/.irida/ngs-archive-linker.conf,
            /etc/irida/ngs-archive-linker.conf)

    -b, --baseURL [ARG]
            The base URL for the NGS Archive REST API. Overrides config file
            setting.

    -s, --sample [ARG]
            A sample id to get sequence files for. Not required. Multiple
            samples may be listed as -s 1 -s 2 -s 3...

    -t, --type [ARG]
            Type of file to link or download. Not required. Available
            options: "fastq", "assembly". Default "fastq". To get both
            types, you can enter --type fastq,assembly

    -i, --ignore
            Ignore creating links for files that already exist.

    -r, --rename
            Rename existing files with _# suffix. Useful for topup runs with
            similar filenames. NOTE: This option overrides the --ignore
            option.

    --flat  Create links or files in a flat directory under the project name
            rather than in sample directories.

    --username
            The username to use for API requests. Note: if this option is
            not entered it will be requested during running of the script.

    --password
            The password to use for API requests. Note: if this option is
            not entered it will be requested during running of the script.

    --download
            Option to download files from the REST API instead of
            softlinking. Note: Files may be quite large. This option is not
            recommended if you have access to the sequencing filesystem.

    -v, --verbose
            Print verbose messages.

    -h, --help
            Display a help message.

    --version
            Print version.

'''

'''
Usage: refseq_masher contains [OPTIONS] INPUT...

  Find the NCBI RefSeq genomes contained in your sequence files using Mash
  Screen

  Input is expected to be one or more FASTA/FASTQ files or one or more
  directories containing FASTA/FASTQ files. Files can be Gzipped.

Options:
  --mash-bin TEXT              Mash binary path (default="mash")
  -o, --output PATH            Output file path (default="-"/stdout)
  --output-type [tab|csv]      Output file type (tab|csv)
  -n, --top-n-results INTEGER  Output top N results sorted by identity in
                               ascending order (default=0/all)
  -i, --min-identity FLOAT     Mash screen min identity to report
                               (default=0.9)
  -v, --max-pvalue FLOAT       Mash screen max p-value to report
                               (default=0.01)
  -p, --parallelism INTEGER    Mash screen parallelism; number of threads to
                               spawn (default=1)
  -h, --help                   Show this message and exit.

'''