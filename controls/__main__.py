#!/usr/bin/env python

import click
from setup import make_config, setup_logger
from parse import main_parse
from report import main_report
from tools.db_functions import create_control_types

logger = setup_logger()

@click.group()
@click.option("-v", "--verbose", is_flag=True, default=False, help="Set logging level to DEBUG if true.")
@click.option("-c", "--config", help="Path to config.yml. If blank defaults to first found of ~/.config/controls/config.yml, ~/.controls/config.yml or controls/config.yml")
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
@click.option("-s", "--storage", help="Folder for storage of fastq files.")
@click.option('--mode', type=click.Choice(['contains', 'matches']), required = True)
def parse(ctx, storage, mode):
    if storage != None:
        ctx.obj['settings']['irida']['storage'] = storage
    ctx.obj['settings']['mode'] = mode
    click.echo(f"Using context: {ctx.obj}")
    main_parse(ctx.obj['settings'])
    

@cli.command("report")
@click.pass_context
@click.option("-o", "--output_dir", type=click.Path(exists=True), help="Folder for storage of reports.")
def report(ctx, output_dir):
    if output_dir != None:
        ctx.obj['settings']['folder']['output'] = output_dir
    main_report(ctx.obj['settings'])


@cli.command("DBinit")
@click.pass_context
def DBinit():
    create_control_types(settings=ctx.obj['settings'])

if __name__ == "__main__":
    cli()
    