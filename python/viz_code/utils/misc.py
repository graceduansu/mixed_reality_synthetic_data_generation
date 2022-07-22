import logging
import numpy as np
import pickle


logger = logging.getLogger('Ego4DLogger')


def merge_queries_pickle_files(pkl_path_1, pkl_path_2, keys_per_file, output_pkl_path):
    logger.info('Merging two pickle files (usually used for merging pairs from covisibility + retrieval)')
    logger.info('Using {} as keys (this should be pairs retrieved from vlad)'.format(pkl_path_1))
    p1 = pickle.load(open(pkl_path_1, 'rb'))
    p2 = pickle.load(open(pkl_path_2, 'rb'))

    # Assuming both are dictionaries in the form of {q1:[db1, db2, ...], q2:[db1, db3, ...]}
    logger.info('Total of {} keys in p1, {} keys in p2'.format(len(p1.keys()), len(p2.keys())))
    assert len(p1.keys()) >= len(p2.keys())

    final_dict = {}
    for qname in p1:
        # print(qname, len(p1[qname]), len(p2[qname]) if qname in p2 else 0)
        # grab all from p2 (geometric)
        merged_list = p2[qname][:keys_per_file] if qname in p2 else []
        # grab the rest from p1 (visual database)
        p1_list = p1[qname]
        p1_list_not_overlapped = [filename for filename in p1_list if filename not in merged_list][:keys_per_file * 2 - len(merged_list)]
        # final list
        merged_list += p1_list_not_overlapped
        final_dict[qname] = merged_list

    with open(output_pkl_path, 'wb') as f:
        pickle.dump(final_dict, f)



