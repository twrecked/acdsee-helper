import os.path
import pprint
import shutil

from . import config
from . import metadata
from .color import color, vprint

pp = pprint.PrettyPrinter(indent=4)

if __name__ == '__main__':

    c = config.DxoConfig()
    c.dump()

    for file in c.file_names:
        m = metadata.MetaData(c, file)
        m.fix_up_start()

        make, model = m.get_make_model
        for mapped_model, mapped_to in c.models.items():
            if model.lower() != mapped_model.lower():
                continue

            dirname = os.path.dirname(file)
            basename = os.path.basename(file)
            new_dir = f'{dirname}/{c.fake_dir}'
            new_file = f'{new_dir}/{basename}'

            if c.dry_run:
                vprint(color(f" would copy {file} to {new_file}", fg='green'))
                vprint(color(f" and replace {model} with {mapped_to}", fg='green'))
                continue

            if not os.path.exists(new_file):
                vprint(color(f" creating {new_dir}", fg='green'))
                os.makedirs(new_dir, exist_ok=True)

            if os.path.exists(new_file):
                vprint(color(f" copying {file} over {new_file}", fg='green'))
                os.remove(new_file)
            else:
                vprint(color(f" copying {file} to {new_file}", fg='green'))
            shutil.copy(file, new_file)

            vprint(color(f" and replacing '{model}' with '{mapped_to['model']}'", fg='green'))
            nm = metadata.MetaData(c, new_file)
            nm.set_make_model(mapped_to['make'], mapped_to['model'])

        m.fix_up_finished()
