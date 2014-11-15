#!/usr/bin/python

import os
import os.path
import sys
import hashlib
import pickle
from collections import defaultdict

blocksize = 2**20

def compute_hash ( filepath ):
    md = hashlib.md5()
    f = open(filepath, 'rb')
    try:
        while True :
            chunk = f.read(blocksize)
            if not chunk : break
            md.update ( chunk )
    finally:
        f.close()
    return md.digest()

# Check command line parameters
if len ( sys.argv ) < 3 or sys.argv[1] == '-h':
    sys.exit ( 'Usage: {0} pickle_file_name root_dir_path'.format ( sys.argv[0] ))

# Assign first two to be the pickle file and the root directory
pklname = sys.argv[1]
rootdir = sys.argv[2]

# Check if the root directory exists
if not os.path.exists ( rootdir ) :
    sys.exit ( 'ERROR: Root directory {0} does not exist.'.format(rootdir) )
    
# Check if we shall update the pickle file
do_hash_init = True
if os.path.exists ( pklname ) :
    print 'Loading hashtable data from {0} ...'.format ( pklname ),
    f = open ( pklname, 'rb' )
    try :
        hashtable = pickle.load ( f )
        do_hash_init = False
    except EOFError :
        sys.exit ( 'ERROR: Cannot read hash table: EOF hit.' )
    finally :
        f.close()
    print 'done.'
    print 'Pruning non-existing files from the hashtable ...'
    for filesize in list(hashtable.keys()) :
        for fullpath in list(hashtable[filesize].keys()) :
            if not os.path.exists ( fullpath ) :
                del hashtable[filesize][fullpath]
                print '-',fullpath
    print '... done.'

if do_hash_init :
    print 'Creating new hashtable ...'
    hashtable = defaultdict(lambda: defaultdict(tuple))

for basedir, dirs, files in os.walk ( rootdir ) :
    for file in files :
        fullpath = os.path.join ( basedir, file )
        relpath  = os.path.relpath ( fullpath, rootdir )
        statinfo = os.stat ( fullpath )
        # Default is to compute the hash of the file
        do_hash = True
        # Check for previously stored information, if any
        fileinfo = hashtable[statinfo.st_size][relpath]
        if fileinfo :
            # The file hash has been already computed.
            # Check the file modification time - if it differs from the stored
            # one, we will recompute the hash
            do_hash = ( fileinfo[0] == statinfo.st_mtime )
        # If we compute new hash, we have to update the dictionary as well
        if do_hash :
            filehash = compute_hash ( fullpath )
            fileinfo = ( statinfo.st_mtime, filehash )
            hashtable[statinfo.st_size][relpath] = fileinfo
            print '+',
        else :
            print ' ',
        print fullpath, statinfo.st_size, statinfo.st_mtime

# Convert the hashtable to a normal dict
hashtable = dict(hashtable)

print 'Saving pickle data to {0} ...'.format ( pklname ),
f = open ( pklname, 'wb' )
pickle.dump ( hashtable, f, pickle.HIGHEST_PROTOCOL )
f.close()
print 'done.'


