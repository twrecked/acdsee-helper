import pprint

from . import config
from . import metadata

pp = pprint.PrettyPrinter(indent=4)

if __name__ == '__main__':
    c = config.Config()

    for file in c.file_names:
        m = metadata.MetaData(c, file)
        m.fix_up()
        m.fix_up_geo()
        m.dump()
        m.write_changes()
