import csv
import gzip
import os
import pickle


def pickle_file(obj, filename, gzipfile=False):
    """

    :param obj:
    :param filename: Filename, without the extension
    :param gzipfile:
    :return:
    """
    if gzipfile:
        gfile = gzip.open('%s.pklzip' % filename, 'wb')
    else:
        gfile = open('%s.pkl' % filename, 'wb')
    pickle.dump(obj, gfile)
    gfile.close()


def unpickle_file(filename):
    extension = os.path.splitext(filename)[1]
    if extension == '.pklzip':
        gfile = gzip.open(filename, 'rb')
    else:
        gfile = open(filename, 'rb')
    return pickle.load(gfile)


def save_dict_to_csv(data, filename):
    with open(filename, 'wb') as cfile:
        writer = csv.DictWriter(cfile, data[0].keys())
        writer.writeheader()
        writer.writerows(data)
