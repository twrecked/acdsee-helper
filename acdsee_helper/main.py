import sys
import pprint

from . import config
from . import metadata
from . import keywords
from .util import remove_duplicates

pp = pprint.PrettyPrinter(indent=4)


# Modes
# fix
# fix + export
# dump
# export
#
if __name__ == '__main__':

    c = config.HelperConfig()

    all_keywords = []

    for file in c.file_names:
        m = metadata.MetaData(c, file)
        m.fix_up_start()
        if c.mode == 'dump':
            #  m.dump_exif()
            m.dump2()
            pp.pprint(m.get_make_model)
        elif c.mode == 'check-keywords':
            # XXX no reprocessing here...
            # m.fix_up()
            # m.fix_up_geo()
            # pp.pprint(m.get_people)
            # pp.pprint(m.get_lr_keywords)
            all_keywords = all_keywords + m.get_all_keywords
        else:
            m.fix_up()
            m.fix_up_geo()
            # m.dump()
            m.write_changes()
        m.fix_up_finished()

    if c.mode == 'check-keywords':
        khash = keywords.keywords_to_hash(all_keywords)
        print('here')
        pp.pprint(khash)
        print("\n".join(keywords.hash_to_acdsee(khash)))
        # hash_to_acdsee(khash)
