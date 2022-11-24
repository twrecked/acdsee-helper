import os
import time
import pprint
import click
from watchdog.observers import Observer

from . import config
from . import metadata
from .color import vprint, vvprint, error
from .keywords import keywords_to_hash, hash_to_acdsee
from . import changes
from .util import file_age, remove_duplicates

pp = pprint.PrettyPrinter(indent=4)

options = {
    'dry_run': False,
    'verbose': 0,
    'no_color': False,
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


def fixup_image(c, file, no_geo):
    try:
        m = metadata.MetaData(c, file)
        m.fix_up_start()
        m.fix_up()
        if no_geo:
            vvprint('skipping GPS to location lookup')
        else:
            m.fix_up_geo()
        m.write_changes()
        m.fix_up_finished()
    except Exception as e:
        error(f"problem reading {file} ({str(e)}")
        return []


def get_keywords(c, file, no_fix, no_geo):
    try:
        m = metadata.MetaData(c, file)
        m.fix_up_start()
        if no_fix:
            vvprint('skipping tag fix')
        else:
            m.fix_up()
        if no_geo:
            vvprint('skipping GPS to location lookup')
        else:
            m.fix_up_geo()
        return m.get_all_keywords
    except Exception as e:
        error(f"problem reading {file} ({str(e)}")
        return []


@click.group()
def cli():
    pass


@cli.command(cls=CommonCommand)
@click.option("-G", "--no-geo", default=False, is_flag=True,
              help="Disable GPS to  location look up")
@click.option("-r", "--recursive", default=False, is_flag=True,
              help="Descend into directories")
@click.argument('files_or_dirs', required=True, nargs=-1)
def fix(dry_run, verbose, no_color, config_file, keyword_file, files_or_dirs, no_geo, recursive):
    build_options(dry_run, verbose, no_color, config_file, keyword_file)
    c = config.ACDSeeConfig(options)

    for file_or_dir in files_or_dirs:
        if os.path.isdir(file_or_dir) and recursive:
            for root, dirs, files in os.walk(file_or_dir):
                for file in files:
                    file = f"{root}/{file}"
                    if c.is_data_file(file):
                        fixup_image(c, file, no_geo)
        else:
            if c.is_data_file(file_or_dir):
                fixup_image(c, file_or_dir, no_geo)


@cli.command(cls=CommonCommand)
@click.option("-E", "--no-exif", default=False, is_flag=True,
              help="Only dump exif information")
@click.option("-X", "--no-xmp", default=False, is_flag=True,
              help="Only dump xmp information")
@click.argument('filenames', required=True, nargs=-1)
def dump(dry_run, verbose, no_color, config_file, keyword_file, filenames, no_exif, no_xmp):
    build_options(dry_run, verbose, no_color, config_file, keyword_file)
    c = config.ACDSeeConfig(options)

    for file in filenames:
        m = metadata.MetaData(c, file)
        if not no_xmp:
            m.dump_xmp()
        if not no_exif:
            m.dump_exif()


@cli.command(cls=CommonCommand)
@click.option("-r", "--recursive", default=False, is_flag=True,
              help="Descend into directories")
@click.argument('files_or_dirs', required=True, nargs=-1)
def keywords(dry_run, verbose, no_color, config_file, keyword_file, recursive, files_or_dirs):
    build_options(dry_run, verbose, no_color, config_file, keyword_file)
    c = config.ACDSeeConfig(options)

    all_keywords = []
    for file_or_dir in files_or_dirs:
        if os.path.isdir(file_or_dir) and recursive:
            for root, dirs, files in os.walk(file_or_dir):
                for file in files:
                    file = f"{root}/{file}"
                    if c.is_data_file(file):
                        all_keywords = remove_duplicates(all_keywords + get_keywords(c, file, False, False))
        else:
            if c.is_data_file(file_or_dir):
                all_keywords = remove_duplicates(all_keywords + get_keywords(c, file_or_dir, False, False))

    # If given current list them merge with it.
    if keyword_file is not None:
        all_keywords = all_keywords + list(c.keywords)

    # Remove duplicates and tidy up then output in ACDSee format.
    all_keywords = remove_duplicates(all_keywords)
    all_keywords.sort()
    khash = keywords_to_hash(all_keywords)
    print("\n".join(hash_to_acdsee(khash)))


@cli.command(cls=CommonCommand)
@click.option("-G", "--no-geo", default=False, is_flag=True,
              help="Disable GPS to  location look up")
@click.argument('base', required=True, nargs=1, default=".")
def watch(dry_run, verbose, no_color, config_file, keyword_file, no_geo, base):
    build_options(dry_run, verbose, no_color, config_file, keyword_file)
    c = config.ACDSeeConfig(options)

    # Add watchers for directories and configuration.
    exif_handler = changes.ExifFileHandler(c)
    config_handler = changes.AnyFileHandler(c)

    observer = Observer()
    observer.schedule(exif_handler, base, recursive=True)
    if c.config_file is not None:
        observer.schedule(config_handler, c.config_file)
    if c.keyword_file is not None:
        observer.schedule(config_handler, c.keyword_file)
    observer.start()

    try:
        while True:
            time.sleep(1)
            too_soon = set()
            with changes.files_lock_:
                files = changes.files_
                changes.files_ = set()

            for file in files:
                try:
                    if file_age(file) < c.update_delay:
                        vvprint(f"{file}: too young")
                        too_soon.add(file)
                        continue

                    if c.is_data_file(file):
                        vprint(f"would check {file}")
                        fixup_image(c, file, no_geo)
                    if c.is_config_file(file):
                        c.load()

                except Exception as e:
                    error(f"{file}: error ({str(e)})")

            with changes.files_lock_:
                changes.files_ = changes.files_.union(too_soon)
    finally:
        observer.stop()
        observer.join()


if __name__ == '__main__':
    cli()
