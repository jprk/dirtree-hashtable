#!/usr/bin/python

import os
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
    
rootdir = 'K:\\Probrat'
#rootdir = 'D:\\temp'
hashtable = defaultdict(list)

for basedir, dirs, files in os.walk ( rootdir ) :
    for file in files :
        fullpath = os.path.join ( basedir, file )
        filesize = os.path.getsize ( fullpath )
        filehash = compute_hash ( fullpath )
        fileinfo = ( fullpath, filehash )
        hashtable[filesize].append(fileinfo)
        print fullpath, filesize
        
print "Saving pickle data ..."
f = open ( 'probrat.pkl', 'wb' )
pickle.dump ( hashtable, f, pickle.HIGHEST_PROTOCOL )
f.close()


