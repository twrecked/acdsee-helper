import sys
import pprint

from . import config
from . import metadata
from . import keywords
from .util import remove_duplicates

pp = pprint.PrettyPrinter(indent=4)


# def keywords_to_hash(keywords):
#     acdsee = {}
#     keywords = list(set(keywords))
#     keywords.sort()
#     for keyword in keywords:
#         current_hash = acdsee
#         topics = keyword.split('|')
#         for index in range(len(topics)):
#             topic = topics[index]
#             if index == len(topics) - 1:
#                 if topic in current_hash:
#                     pass
#                 else:
#                     current_hash[topic] = None
#             else:
#                 if topic in current_hash:
#                     if type(current_hash[topic]) != dict:
#                         current_hash[topic] = {}
#                 else:
#                     current_hash[topic] = {}
#                 current_hash = current_hash[topic]
#     return acdsee
#
#
# def hash_to_acdsee(keyword_hash, depth=0):
#     for topic, value in keyword_hash.items():
#         print(('\t' * depth) + topic)
#         if value is not None:
#             hash_to_acdsee(value, depth + 1)


# Modes
# fix
# fix + export
# dump
# export
#
if __name__ == '__main__':

    c = config.Config()

    # print(c.name_to_keywords('steve herrell'))
    # c.dump()
    # sys.exit(0)

    all_keywords = []

    for file in c.file_names:
        m = metadata.MetaData(c, file)
        m.fix_up_start()
        if c.mode == 'dump':
            m.dump_xmp()
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
            m.write_changes()
        m.fix_up_finished()

    if c.mode == 'check-keywords':
        khash = keywords.keywords_to_hash(all_keywords)
        print('here')
        pp.pprint(khash)
        print("\n".join(keywords.hash_to_acdsee(khash)))
        # hash_to_acdsee(khash)
