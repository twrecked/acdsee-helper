
import time
import pprint
import click
from watchdog.observers import Observer

from . import config
from . import metadata
from .color import vprint, vvprint, error, info
from .keywords import keywords_to_hash, hash_to_acdsee
from . import changes
from .util import file_age, remove_duplicates, walk


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


pp = pprint.PrettyPrinter(indent=4)

options = {
    'dry_run': False,
    'verbose': 0,
    'no_color': False,
    'config_file': None,
    'keyword_file': None,
    'recursive': False,
}


def _build_options(dry_run, verbose, no_color, config_file, keyword_file, recursive=None):
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
    if recursive is not None:
        options['recursive'] = recursive


def _tidy_unknown_people(cfg, keywords):
    tidy_keywords = []
    known_people = set()
    unknown_people = []
    for keyword in keywords:
        topics = keyword.split('|')
        pp.pprint(topics)
        if topics[0].lower() == cfg.people_prefix.lower():
            if topics[1].lower() == cfg.people_unknown_prefix.lower():
                unknown_people.append(keyword)
            else:
                tidy_keywords.append(keyword)
                known_people.add(topics[-1])
        else:
            tidy_keywords.append(keyword)

    for unknown in unknown_people:
        topics = unknown.split('|')
        if topics[-1] not in known_people:
            tidy_keywords.append(unknown)

    return sorted(tidy_keywords)


def _fixup_image(cfg, file, no_geo):
    try:
        m = metadata.MetaData(cfg, file)
        m.fix_up_start()
        if no_geo:
            vvprint('skipping GPS to location lookup')
        else:
            m.fix_up_geo()
        m.fix_up()
        m.write_changes()
        m.fix_up_finished()
    except Exception as e:
        error(f"problem reading {file} ({str(e)}")


def _dump_image(cfg, file, no_exif, no_xmp):
    try:
        m = metadata.MetaData(cfg, file)
        info(f"{file}:", style='bold')
        if not no_xmp:
            m.dump_xmp()
        if not no_exif:
            m.dump_exif()
    except Exception as e:
        error(f"problem reading {file} ({str(e)}")


def _get_keywords(cfg, file, no_fix, no_geo, all_keywords):
    try:
        m = metadata.MetaData(cfg, file)
        m.fix_up_start()
        if no_geo:
            vvprint('skipping GPS to location lookup')
        else:
            m.fix_up_geo()
        if no_fix:
            vvprint('skipping tag fix')
        else:
            m.fix_up()
        all_keywords[:] = remove_duplicates(all_keywords + m.get_all_keywords)
    except Exception as e:
        error(f"problem reading {file} ({str(e)}")


def _find_keyword(cfg, file, keyword, no_fix, no_geo, found_in):
    try:
        m = metadata.MetaData(cfg, file)
        m.fix_up_start()
        if no_geo:
            vvprint('skipping GPS to location lookup')
        else:
            m.fix_up_geo()
        if no_fix:
            vvprint('skipping tag fix')
        else:
            m.fix_up()
        for possible_keyword in m.get_all_keywords:
            if keyword in possible_keyword:
                found_in.add(file)
                return
    except Exception as e:
        error(f"problem reading {file} ({str(e)}")
    return


@click.group()
def cli():
    pass


@cli.command(cls=CommonCommand)
def cfg(dry_run, verbose, no_color, config_file, keyword_file):
    _build_options(dry_run, verbose, no_color, config_file, keyword_file)
    cfg = config.ACDSeeConfig(options)
    cfg.dump()


@cli.command(cls=CommonCommand)
@click.option("-G", "--no-geo", default=False, is_flag=True,
              help="Disable GPS to  location look up")
@click.option("-r", "--recursive", default=False, is_flag=True,
              help="Descend into directories")
@click.argument('files_or_dirs', required=True, nargs=-1)
def fix(dry_run, verbose, no_color, config_file, keyword_file, files_or_dirs, no_geo, recursive):
    _build_options(dry_run, verbose, no_color, config_file, keyword_file, recursive)
    cfg = config.ACDSeeConfig(options)

    walk(cfg, files_or_dirs, _fixup_image, no_geo=no_geo)


@cli.command(cls=CommonCommand)
@click.option("-E", "--no-exif", default=False, is_flag=True,
              help="Only dump exif information")
@click.option("-X", "--no-xmp", default=False, is_flag=True,
              help="Only dump xmp information")
@click.option("-r", "--recursive", default=False, is_flag=True,
              help="Descend into directories")
@click.argument('files_or_dirs', required=True, nargs=-1)
def dump(dry_run, verbose, no_color, config_file, keyword_file, files_or_dirs, recursive, no_exif, no_xmp):
    _build_options(dry_run, verbose, no_color, config_file, keyword_file, recursive)
    cfg = config.ACDSeeConfig(options)

    walk(cfg, files_or_dirs, _dump_image, no_exif=no_exif, no_xmp=no_xmp)


@cli.command(cls=CommonCommand)
@click.option("-F", "--no-fix", default=False, is_flag=True,
              help="Use keywords as they are.")
@click.option("-G", "--no-geo", default=False, is_flag=True,
              help="Disable GPS to location look up.")
@click.option("-r", "--recursive", default=False, is_flag=True,
              help="Descend into directories")
@click.argument('files_or_dirs', required=True, nargs=-1)
def keywords(dry_run, verbose, no_color, config_file, keyword_file, no_fix, no_geo, recursive, files_or_dirs):
    _build_options(dry_run, verbose, no_color, config_file, keyword_file, recursive)
    cfg = config.ACDSeeConfig(options)

    all_keywords = []
    walk(cfg, files_or_dirs, _get_keywords, no_fix=no_fix, no_geo=no_geo, all_keywords=all_keywords)

    # If given current list them merge with it.
    if keyword_file is not None:
        all_keywords = all_keywords + list(cfg.keywords)

    # Remove duplicates and tidy up then output in ACDSee format.
    all_keywords = remove_duplicates(all_keywords)
    all_keywords = _tidy_unknown_people(cfg, all_keywords)
    khash = keywords_to_hash(all_keywords)
    print("\n".join(hash_to_acdsee(khash)))


@cli.command(cls=CommonCommand)
@click.option("-r", "--recursive", default=False, is_flag=True,
              help="Descend into directories")
@click.argument('keyword', required=True, nargs=1)
@click.argument('files_or_dirs', required=True, nargs=-1)
def find(dry_run, verbose, no_color, config_file, keyword_file, recursive, keyword, files_or_dirs):
    _build_options(dry_run, verbose, no_color, config_file, keyword_file, recursive)
    cfg = config.ACDSeeConfig(options)

    found_in = set()
    walk(cfg, files_or_dirs, _find_keyword, no_fix=False, no_geo=False, keyword=keyword, found_in=found_in)

    if found_in:
        print("Keyword found in the following files:")
        for file in found_in:
            print(f"  {file}")
    else:
        print("Keyword not found any files.")


@cli.command(cls=CommonCommand)
@click.option("-G", "--no-geo", default=False, is_flag=True,
              help="Disable GPS to  location look up")
@click.argument('base', required=True, nargs=1, default=".")
def watch(dry_run, verbose, no_color, config_file, keyword_file, no_geo, base):
    _build_options(dry_run, verbose, no_color, config_file, keyword_file)
    cfg = config.ACDSeeConfig(options)

    # Add watchers for directories and configuration.
    exif_handler = changes.ExifFileHandler(cfg)
    config_handler = changes.AnyFileHandler(cfg)

    observer = Observer()
    observer.schedule(exif_handler, base, recursive=True)
    if cfg.config_file is not None:
        observer.schedule(config_handler, cfg.config_file)
    if cfg.keyword_file is not None:
        observer.schedule(config_handler, cfg.keyword_file)
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
                    if file_age(file) < cfg.update_delay:
                        vvprint(f"{file}: too young")
                        too_soon.add(file)
                        continue

                    if cfg.is_data_file(file):
                        vprint(f"would check {file}")
                        _fixup_image(cfg, file, no_geo)
                    if cfg.is_config_file(file):
                        cfg.load()

                except Exception as e:
                    error(f"{file}: error ({str(e)})")

            with changes.files_lock_:
                changes.files_ = changes.files_.union(too_soon)
    finally:
        observer.stop()
        observer.join()


if __name__ == '__main__':
    cli()
