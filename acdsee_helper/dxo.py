import os.path
import pprint
import shutil
import click

from . import config
from . import metadata
from .color import vprint
from .util import walk


class CommonCommand(click.Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
    'recursive': False,
}


def build_options(dry_run, verbose, no_color, config_file, recursive=None):
    if dry_run is not None:
        options['dry_run'] = dry_run
    if verbose is not None:
        options['verbose'] = verbose
    if no_color is not None:
        options['no_color'] = no_color
    if config_file is not None:
        options['config_file'] = config_file
    if recursive is not None:
        options['recursive'] = recursive


def _fixup_image(cfg, file):
    print(file)
    m = metadata.MetaData(cfg, file)
    m.fix_up_start()

    make, model = m.get_make_model
    for mapped_model, mapped_to in cfg.models.items():
        if model.lower() != mapped_model.lower():
            continue

        dirname = os.path.dirname(file)
        basename = os.path.basename(file)
        new_dir = f'{dirname}/{cfg.fake_dir}'
        new_file = f'{new_dir}/{basename}'

        if cfg.dry_run:
            vprint(f" would copy {file} to {new_file}")
            vprint(f" and replace {model} with {mapped_to}")
            continue

        if not os.path.exists(new_file):
            vprint(f" creating {new_dir}")
            os.makedirs(new_dir, exist_ok=True)

        if os.path.exists(new_file):
            vprint(f" copying {file} over {new_file}")
            os.remove(new_file)
        else:
            vprint(f" copying {file} to {new_file}")
        shutil.copy(file, new_file)

        vprint(f" and replacing '{model}' with '{mapped_to['model']}'")
        nm = metadata.MetaData(cfg, new_file)
        nm.set_make_model(mapped_to['make'], mapped_to['model'])

    m.fix_up_finished()


@click.group()
def cli():
    pass


@cli.command(cls=CommonCommand)
@click.option("-r", "--recursive", default=False, is_flag=True,
              help="Descend into directories")
@click.argument('files_or_dirs', required=True, nargs=-1)
def fake(dry_run, verbose, no_color, config_file, files_or_dirs, recursive):
    build_options(dry_run, verbose, no_color, config_file, recursive)
    cfg = config.DxoConfig(options)

    walk(cfg, files_or_dirs, _fixup_image)
    #
    # for file_or_dir in files_or_dirs:
    #     if os.path.isdir(file_or_dir) and recursive:
    #         for root, dirs, files in os.walk(file_or_dir):
    #             for file in files:
    #                 file = f"{root}/{file}"
    #                 if cfg.is_data_file(file):
    #                     fixup_image(cfg, file)
    #     else:
    #         if cfg.is_data_file(file_or_dir):
    #             fixup_image(cfg, file_or_dir)


if __name__ == '__main__':
    cli()
