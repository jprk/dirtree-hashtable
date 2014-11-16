#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import argparse
import filecmp
from collections import defaultdict
from create_hashtable import compute_hash, load_hash_table

# maximum number of file names of identical filws to list when displaying a list of identical files.
MAX_LEN = 16

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('database', help='database file')
parser.add_argument('root', help='root directory')
parser.add_argument('-d', '--debug', help='switch on debugging output', action='store_true')
parser.add_argument('-n', '--dry-run', help='do not delete anything', action='store_true')
args = parser.parse_args()

# Assign arguments to local variables
pkl_hash_name = args.database
root_dir = args.root

# Check the existence of the database file
if not os.path.exists(pkl_hash_name):
    sys.exit('ERROR: Database file `{0}` not found!'.format(pkl_hash_name))

# Check the existence of the root directory
if not os.path.exists(root_dir):
    sys.exit('ERROR: Root directory `{0}` not found!'.format(root_dir))

# Load the file digest data created by `create_hashtable` run
print 'Loading file digest data ...',
digest_data = load_hash_table(pkl_hash_name)
if not digest_data:
    sys.exit('ERROR: Unable to read file digest data from `{0}'.format(pkl_hash_name))
print 'done.'

# For all different file sizes this variable contains dictionaries of file names indexed by their digests.
hash_table = {}
# For all different file sizes this variable contains dictionaries of file paths indexed by their digests.
original_paths = {}
# In order to effectively compare the new tree with the old digset data we have to reorganise the digest data
# a bit
# TODO: This could be possibly skipped or integrated into a new format of database file
print 'Constructing hash table and file path info ...',
for file_size in digest_data.keys():
    hashes = defaultdict(list)
    files = defaultdict(list)
    # Digest data is indexed by file size, every element being a defaultdict of (mtime, hash) tuples indexed
    # by file name.
    file_data = digest_data[file_size]
    # Go over all files of the same size
    for file_path in file_data.keys():
        # There might be the same files with different file names
        # (usually .svn or TeX support files or different versions of figures and texts)
        file_hash = file_data[file_path][1]
        file_path, file_name = os.path.split(file_path)
        hashes[file_hash].append(file_name)
        files[file_hash].append(file_path)
    hash_table[file_size] = hashes
    original_paths[file_size] = files

hash_table_keys = hash_table.keys()

print 'Comparing hashtable data with files in `{0}` ...'.format(root_dir)
for basedir, dirs, files in os.walk(root_dir):
    for file_name in files:
        print '----------'
        file_path = os.path.join(basedir, file_name)
        file_size = os.path.getsize(file_path)
        # Unconditional delete of zero-sized files
        if file_size == 0:
            print 'file {0} has zero size, removing'.format(file_name)
            os.remove(file_path)
            continue
        # The file path will be used in print statements at different levels below. The path is a unicode string
        # and it may contain characters that cannot be printed using the character encoding used by the terminal.
        # The implicit conversion routine that uses `errors='strict'` would in such a case trigger an exception.
        # We have to convert all the strings manually, and instruct the encoding routine to replace the characters
        # that cannot be printed by '?'.
        file_path_print = file_path.encode(sys.stdout.encoding, errors='replace')
        # If the file size identical to some file in the original directory tree ...
        if file_size in hash_table_keys:
            # ... compute digest of the file contents
            file_hash = compute_hash(file_path)
            # and compare this digest with the stored digests from the original directory tree.
            if file_hash in hash_table[file_size].keys():
                #
                # This file is a likely duplicate of a file that exists in the original tree and hence it is
                # a candidate for removal. The decision about file removal is based on the following logic:
                #
                # (1) we have a list of files that have the same length and produce the same message digest,
                # (2) if the new file name is identical to some of the original ones, we will assume that the
                #     new file is identical (after all, it has a same file size and the same message digest,
                #     and the chance that this is a hash value collision is quite low),
                # (3) if the new file name is not identical to any of the original files, we will compare the
                #     new file byte-by-byte to all possible candidates and pronounce it identical only in case
                #     that the file comparison returns a match.
                #
                # This is the list of the original files of the same file size and with the same hash.
                original_names = hash_table[file_size][file_hash]
                # A bit of printing to the terminal. Every unicode string has to be encoded so that it can be
                # printed using the given terminal character encoding.
                print 'removal candidate: `{0}` ({1:d} bytes)'.format(file_path_print, file_size)
                if len(original_names) > MAX_LEN:
                    print 'keep: (too many file names to list)'
                else:
                    # Do not forget to encode the file names for the terminal output
                    original_names_print = [x.encode(sys.stdout.encoding, errors='replace') for x in original_names]
                    print 'keep:   ', original_names_print
                # The initial assumption is that the new file is unique and will not be deleted
                do_delete = False
                # Check the condition (2) in the list above
                if not file_name in original_names:
                    # The file name is unique, we have to compare byte-by-byte against all candidates
                    file_name_print = file_name.encode(sys.stdout.encoding, errors='replace')
                    print 'file `{0}` is not in the list, comparing byte-by-byte ...'.format(file_name_print)
                    for orig_path in original_paths[file_size][file_hash]:
                        if filecmp.cmp(file_path, orig_path, False):
                            orig_path_print = file_name.encode(sys.stdout.encoding, errors='replace')
                            print 'file is identical to', orig_path_print
                            do_delete = True
                            break
                    if not do_delete:
                        print 'file is unique, keeping it'
                else:
                    do_delete = True
                if do_delete:
                    if args.dry_run:
                        print 'file would be deleted'
                    else:
                        os.remove(file_path)
                        print 'file deleted'
            else:
                print 'unique hash of file', file_path_print
        else:
            print 'unique size of file', file_path_print