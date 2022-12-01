#!/usr/bin/env python

import click
from setup import make_config, setup_logger
from parse import main_parse
from report import main_report
from tools.db_functions import create_control_types

logger = setup_logger()

modes = list(make_config()['modes'].keys())
# Have to make copy to avoid append being applied to modes
modes_all = modes.copy()
modes_all.append("all")


@click.group()
@click.option("-v", "--verbose", is_flag=True, default=False, help="Set logging level to DEBUG if true.")
@click.option("-c", "--config", type=click.Path(exists=True), help="Path to config.yml. If blank defaults to first found of ~/.config/controls/config.yml, ~/.controls/config.yml or controls/config.yml")
@click.pass_context
def cli(ctx, verbose, config):    
    click.echo(f"Verbose: {verbose}")
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config
    ctx.obj['settings'] = make_config(ctx.obj)
    click.echo(f"Context: {ctx.obj}")
    

@cli.command("parse")
@click.pass_context
@click.option("-s", "--storage", type=click.Path(exists=True), help="Folder for storage of fastq files. Overwrites config.yml path.")
# TODO: Possibly load in modes from config.yml 
@click.option('--mode', type=click.Choice(modes_all), default="all", help="Refseq_masher mode to be run. Defaults to 'both'.")
def parse(ctx, storage, mode):
    """Pulls fastq files from Irida, runs refseq_masher and stores results."""
    if storage != None:
        ctx.obj['settings']['irida']['storage'] = storage
    if mode == "all":
        ctx.obj['settings']['mode'] = modes
    else:
        ctx.obj['settings']['mode'] = [mode]
    # click.echo(ctx.obj['settings'])
    main_parse(ctx.obj['settings'])
    click.echo("The parse run has finished.")
    

@cli.command("report")
@click.pass_context
@click.option("-o", "--output_dir", type=click.Path(exists=True), help="Folder for storage of reports. Overwrites config.yml path.")
def report(ctx, output_dir):
    """Generates html and xlsx reports."""
    if output_dir != None:
        ctx.obj['settings']['folder']['output'] = output_dir
    main_report(ctx.obj['settings'])
    click.echo("The reports run has finished.")


@cli.command("DBinit")
@click.pass_context
def DBinit(ctx):
    create_control_types(settings=ctx.obj['settings'])

if __name__ == "__main__":
    cli()
    