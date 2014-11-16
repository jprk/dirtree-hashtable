#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import os.path
import sys
import hashlib
import pickle
import time
import argparse
from collections import defaultdict

BLOCK_SIZE = 2 ** 20
SAVE_PERIOD = 60

def compute_hash(file_path):
    """Compute MD5 hash of a file specified as argument.

    :type file_path: str
    :param file_path:
    :return: MD5 digest as a string
    """
    md = hashlib.md5()
    f = open(file_path, 'rb')
    try:
        while True:
            chunk = f.read(BLOCK_SIZE)
            if not chunk: break
            md.update(chunk)
    finally:
        f.close()
    return md.digest()


def create_tuple_dd():
    """This module function makes defaultdict(lambda: defaultdict(tuple)) pickable.
    See http://stackoverflow.com/questions/16439301/cant-pickle-defaultdict"""
    return defaultdict(tuple)


def save_hashtable(pkl_name, hash_data):
    # Convert the hashtable defaultdict to a normal dict
    # hash_data = dict(hashtable)
    print 'Saving pickle data to {0} ...'.format(pkl_name),
    f = open(pkl_name, 'wb')
    pickle.dump(hash_data, f, pickle.HIGHEST_PROTOCOL)
    f.close()
    print 'done.'


# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('database', help='database file')
parser.add_argument('root', help='root directory')
parser.add_argument('-a', '--append', help='append to existing history data', action='store_true')
parser.add_argument('-d', '--debug', help='switch on debugging output', action='store_true')
args = parser.parse_args()

# Assign arguments to local variables
pkl_hash_name = args.database
root_dir = args.root

# Check if the root directory exists
if not os.path.exists(root_dir):
    sys.exit('ERROR: Root directory {0} does not exist.'.format(root_dir))

print 'Stdout encoding is', sys.stdout.encoding

# Check if we shall update the pickle file
hash_table = None
if os.path.exists(pkl_hash_name):
    print 'Loading hash table data from {0} ...'.format(pkl_hash_name),
    f = open(pkl_hash_name, 'rb')
    try:
        hash_table = pickle.load(f)
    except EOFError:
        sys.exit('ERROR: Cannot read hash table: EOF hit.')
    finally:
        f.close()
    print 'done.'
    # Do not access the hash table in case that the read failed
    if  hash_table:
        # A default would be to verify that the file information stored in the database is up-to-date.
        # However this could take a while and sometimes (after a crash, computer shutdown etc.) we
        # are reasonably sure that the data is up-to-date and we want to skip the initial verification
        # phase.
        if not args.append:
            print 'Pruning non-existing files from the hash table ...'
            for filesize in list(hash_table.keys()):
                for full_path in list(hash_table[filesize].keys()):
                    abs_path = os.path.join(root_dir,full_path)
                    if not os.path.exists(abs_path):
                        del hash_table[filesize][full_path]
                        out_str = u'- ({0}){1}{2}'.format(root_dir, os.path.sep, full_path)
                        print out_str.encode(sys.stdout.encoding, errors='replace')
            print '... done.'
        else:
            print 'Skipping hash table verification as requested'

# If there was no hash table to read, create an empty one
if not hash_table:
    print 'Creating a new hash table ...'
    # No lambda can be used here to construct the second level of the defaultdict: we need the
    # database to be pickable. See `create_tuple_dd()` function above.
    hash_table = defaultdict(create_tuple_dd)

# Save the data at least once
do_save_data = True

# Initialise the time trigger for saving the data
save_data_time = time.time() + SAVE_PERIOD

# Walk the directory tree that starts at `root_dir`. The directory and file names shall be in
# Unicode, otherwise we will get into all kind of trouble when trying to stat() the files.
# Unfortunately the Unicode strings have to be reencoded for terminal output and care has to be
# taken to filter out characters that cannot be displayed using the terminal character encoding.
for basedir, dirs, files in os.walk(unicode(root_dir)):
    # We are interested only in files
    for file in files:
        # In order to access the file, an absolute path is needed
        full_path = os.path.join(basedir, file)
        # Only relative path is stored in the database though (so that the whole tree can be
        # relocated to different place without the need to collect the file information again).
        rel_path = os.path.relpath(full_path, root_dir)
        # Get the file information
        stat_info = os.stat(full_path)
        # Default is to compute the hash of the file
        do_hash = True
        # Check for previously stored information, if any
        file_info = hash_table[stat_info.st_size][rel_path]
        if file_info:
            # The file hash has been already computed.
            # Check the file modification time - if it differs from the stored
            # one, we will recompute the hash
            do_hash = ( file_info[0] != stat_info.st_mtime )
        # If we compute new hash, we have to update the dictionary as well
        if do_hash:
            file_hash = compute_hash(full_path)
            file_info = ( stat_info.st_mtime, file_hash )
            hash_table[stat_info.st_size][rel_path] = file_info
            do_save_data = True
            print '+',
        else:
            print ' ',
        # Convert st_mtime into a meaningful time information
        if stat_info.st_mtime < 0:
            # TODO: Consider some trickery with datetime.datetime()
            # Currently a timestamp -255601696.0 which represents Windows date 2097-12-23 23:00:00 results
            # in the following:
            # >>> epo = datetime.datetime(1970, 1, 1)
            # >>> delta = datetime.timedelta(seconds=(-255601696))
            # >>> epo+delta
            # datetime.datetime(1961, 11, 25, 15, 31, 44)
            mtime_str = '(value out of range)'
        else:
            mtime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat_info.st_mtime))
        # Convert the full_path string into something that can be printed on terminal
        full_path = full_path.encode(sys.stdout.encoding, errors='replace')
        print full_path, stat_info.st_size, mtime_str
        # Optionally save the current hash table
        if time.time() > save_data_time and do_save_data:
            save_hashtable(pkl_hash_name, hash_table)
            save_data_time = time.time() + SAVE_PERIOD
            do_save_data = False

if do_save_data:
    save_hashtable(pkl_hash_name, hash_table)


