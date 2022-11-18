import sys
import pprint
import click

from . import config
from . import metadata
from .color import vprint, vvprint
from .keywords import keywords_to_hash, hash_to_acdsee
from .util import remove_duplicates

pp = pprint.PrettyPrinter(indent=4)

options = {
    'dry_run': False,
    'verbose': 0,
    'color': 0,
    'config_file': None,
    'keyword_file': None,
}


def build_options(dry_run, verbose, no_color, config_file, keyword_file):
    if dry_run is not None:
        options['dry_run'] = dry_run
    if verbose is not None:
        options['verbose'] = verbose
    if no_color is not None:
        options['no_color'] = no_color
    if config_file is not None:
        options['config_file'] = config_file
    if keyword_file is not None:
        options['keyword_file'] = keyword_file


class CommonCommand(click.Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params.insert(0, click.core.Option(('-k', '--keyword-file'), required=False,
                           help="Keywords list exported from ACDSee"))
        self.params.insert(0, click.core.Option(('-c', '--config-file'), required=False,
                           help="Program configuration file"))
        self.params.insert(0, click.core.Option(("-n", "--no-color"), default=False, is_flag=True,
                           help="Turn on or off the colors"))
        self.params.insert(0, click.core.Option(("-v", "--verbose"), count=True,
                           help="Be chatty. More is more chatty!"))
        self.params.insert(0, click.core.Option(('-d', '--dry-run'), default=False, is_flag=True,
                           help="Don't really do the work"))


@click.group()
def cli():
    pass


@cli.command(cls=CommonCommand)
@click.option("-G", "--no-geo", default=False, is_flag=True,
              help="Disable GPS to  location look up")
@click.argument('filenames', required=True, nargs=-1)
def fix(dry_run, verbose, no_color, config_file, keyword_file, filenames, no_geo):
    build_options(dry_run, verbose, no_color, config_file, keyword_file)
    c = config.HelperConfig(options)

    for file in filenames:
        m = metadata.MetaData(c, file)
        m.fix_up_start()
        m.fix_up()
        if no_geo:
            vvprint('skipping GPS to location lookup')
        else:
            m.fix_up_geo()
        m.write_changes()
        m.fix_up_finished()


@cli.command(cls=CommonCommand)
@click.option("-E", "--no-exif", default=False, is_flag=True,
              help="Only dump exif information")
@click.option("-X", "--no-xmp", default=False, is_flag=True,
              help="Only dump xmp information")
@click.argument('filenames', required=True, nargs=-1)
def dump(dry_run, verbose, no_color, config_file, keyword_file, filenames, no_exif, no_xmp):
    build_options(dry_run, verbose, no_color, config_file, keyword_file)
    c = config.HelperConfig(options)

    for file in filenames:
        m = metadata.MetaData(c, file)
        m.fix_up_start()
        if not no_xmp:
            m.dump_xmp()
        if not no_exif:
            m.dump_exif()


@cli.command(cls=CommonCommand)
@click.argument('filenames', required=True, nargs=-1)
def keywords(dry_run, verbose, no_color, config_file, keyword_file, filenames):
    build_options(dry_run, verbose, no_color, config_file, keyword_file)
    c = config.HelperConfig(options)
    c.dump()

    all_keywords = []
    for file in filenames:
        m = metadata.MetaData(c, file)
        m.fix_up_start()
        m.fix_up()
        m.fix_up_geo()
        all_keywords = all_keywords + m.get_all_keywords

    khash = keywords_to_hash(all_keywords)
    print('here')
    pp.pprint(khash)
    print("\n".join(hash_to_acdsee(khash)))
    # hash_to_acdsee(khash)
