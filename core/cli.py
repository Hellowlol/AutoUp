import click
import core.autoup
import os
from core import CURRENT_PATH, USERDATA_PATH, initialize, CONFIG


@click.group(context_settings={'max_content_width': 100},
             epilog='This tool was a made for education purposes, use on your own risk \n https://github.com/Hellowlol/AutoUp')
@click.option('-w', '--webserver', required=False, is_flag=True)
@click.option('--debug', is_flag=True, default=False, help='Print useful information for debugging autoup and for reporting bugs.')
@click.option('-c', '--config', required=False, type=click.Path())
@click.option('-report', required=False, default=False)
@click.option('-dr', '--dry_run', required=False, default=False, is_flag=True)
@click.option('--enabled_sites', type=click.Choice(['all', 'norbits']))
@click.option('--watched_paths', required=False, default=None)
@click.option('--comment', required=False, default=None)
@click.pass_context
def cli(ctx, webserver, debug, config, report, dry_run, enabled_sites, watched_paths, comment):
    # make a new config if it dont exist
    if config is None:
        if not os.path.isfile(os.path.join(USERDATA_PATH, 'config.ini')):
            config = initialize(os.path.join(USERDATA_PATH, 'config.ini'))
        else:
            config = initialize(os.path.join(USERDATA_PATH, 'config.ini'))

    if isinstance(enabled_sites, str):
        enabled_sites = enabled_sites.split()

    if isinstance(watched_paths, str):
        watched_paths = watched_paths.split()

    lvl = 'debug' if debug else 'info'

    ctx.obj = core.autoup.Autoup(config_file=config,
                                 enabled_sites=enabled_sites,
                                 watched_paths=watched_paths,
                                 loglevel=lvl,
                                 dry_run=dry_run,
                                 report=report,
                                 comment=comment)


@cli.command()
@click.argument('path', required=False, default=None)
@click.pass_obj
def upload(ctx, path):
    """ """
    ctx.upload(path)


@cli.command()
@click.argument('path', required=False)
@click.pass_obj
def watch(ctx, path):
    """ """
    print('orginal watch %s' % path)
    print ctx.watch()


@cli.command()
@click.option('-h', '--host', required=False, default='0.0.0.0')
@click.option('-p', '--port', required=False, default='8080')
@click.pass_obj
def webserver(ctx, host, port):
    ctx.webserver('%s:%s' % (host, port))


#if __name__ == '__main__':
    #cli()