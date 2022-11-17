import os.path
import pprint
import shutil

from . import config
from . import metadata
from .color import vprint

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
            nm = metadata.MetaData(c, new_file)
            nm.set_make_model(mapped_to['make'], mapped_to['model'])

        m.fix_up_finished()
