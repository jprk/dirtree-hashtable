#!/usr/bin/python

import os
import sys
import hashlib
import pickle
import filecmp
from collections import defaultdict

blocksize = 2**20
MAX_LEN   = 16

def compute_hash ( filepath ):
    md = hashlib.md5()
    f = open(filepath, 'rb')
    try:
        while True :
            chunk = f.read(blocksize)
            if not chunk : break
            md.update ( chunk )
    except IOError as ioe :
        print 'ERROR: Cannot compute hash for {0}: {1}'.format(filepath,e.strerror)
    finally:
        f.close()
    return md.digest()
    
# Check command line parameters
if len ( sys.argv ) < 3 or sys.argv[1] == '-h':
    sys.exit ( 'Usage: {0} pickle_file_name directory_name'.format ( sys.argv[0] ))

if not os.path.exists ( sys.argv[1] ):
    sys.exit ( 'ERROR: Pickle file `{0}` not found!'.format ( sys.argv[1] ))

if not os.path.exists ( sys.argv[2] ):
    sys.exit ( 'ERROR: Directory `{0}` not found!'.format ( sys.argv[2] ))

print "Loading hashtable data ..."
f = open ( sys.argv[1], 'rb' )
listtable = pickle.load ( f )
print listtable[8]
f.close()

print "Constructing hashtable and file path info ..."
hashtable = {}
origpaths = {}
for filesize in listtable.keys() :
    hashes = defaultdict(list)
    files  = defaultdict(list)
    filedata = listtable[filesize]
    for fullpath in filedata.keys() :
        # There might be the same files with different file names
        # (usually .svn or TeX support files or different versions of
        # figures and texts)
        filehash = filedata[fullpath][1]
        filepath, filename = os.path.split ( fullpath )
        hashes[filehash].append ( filename )
        files[filehash].append ( fullpath )
    hashtable[filesize] = hashes
    origpaths[filesize] = files

# print hashtable[22016]
# print origpaths[22016]

# rootdir = 'D:\\Honza\\iFolder'
# rootdir = 'D:\\K611'

rootdir = sys.argv[2]

hashtable_keys = hashtable.keys()

print 'Comparing hashtable data with files in `{0}` ...'.format(rootdir)
for basedir, dirs, files in os.walk ( rootdir ) :
    for filename in files :
        print '----------'
        fullpath = os.path.join ( basedir, filename )
        filesize = os.path.getsize ( fullpath )
        # Unconditional delete of zero-sized files
        if filesize == 0 :
            print 'file {0} has zero size, removing'.format ( filename )
            os.remove(fullpath)
            continue
        filehash = compute_hash ( fullpath )
        if filesize in hashtable_keys :
            if filehash in hashtable[filesize].keys() :
                orignames = hashtable[filesize][filehash]
                print 'removal candidate: `{0}` ({1:d} bytes)'.format(fullpath,filesize)
                if len(orignames) > MAX_LEN :
                    print 'keep: (too many filenames to list)'
                else :
                    print 'keep:   ',orignames
                do_delete = False
                if not filename in orignames :
                # if filename != origname :
                    print 'filename {0} is not in the list, comparing byte-by-byte ...'.format(filename)
                    for origpath in origpaths[filesize][filehash] :
                        if filecmp.cmp ( fullpath, origpath, False ) :
                            print 'file is identical to', origpath
                            do_delete = True
                            break
                    if not do_delete :
                        print 'file is unique, keeping it'
                    #a = raw_input ( 'filenames differ, really delete [y/n]?' )
                    #if len(a) > 0 and a.upper()[0] == 'N' :
                    #    do_delete = False
                    #    print 'file will not be deleted'
                else :
                    do_delete = True
                if do_delete :
                    os.remove(fullpath)
                    print 'file deleted'
            else :
                print 'unique hash of file', fullpath
        else :
            print 'unique size of file', fullpath

                        


        


