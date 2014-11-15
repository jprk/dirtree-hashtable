#!/usr/bin/python

import os
import sys

def deletedir ( root, message ) :
  print message
  try :
    os.rmdir ( root )
  except WindowsError as w :
    print '  - cannot delete file: {0}'.format ( w.strerror )
    sys.exit( 'Cannot delete file')

TREE_ROOT = '.'

for root, dirs, files in os.walk ( TREE_ROOT, topdown=False):
  # Check that the `root` is a leaf directory
  if len(files) == 0 :
    # No files in `root` ...
    if len(dirs) == 0 and root <> TREE_ROOT :
      # ... and no subdirectories in `root`. It is indeed empty.
      # print root, dirs, files
      deletedir ( root, 'Deleting empty leaf directory `{0}`'.format ( root ))
    else :
      # No files in `root`, but there seem to be some subdirectories.
      # However, these subdirs may have been buffered during the traversal to
      # the leaves of the directory tree and may represent the empty leaf
      # directories of the tree that have been deleted already. We will check
      # the real contents of the direstory using os.listdir() and if the list
      # comes out empty, we will delete also this `root`.
      list = os.listdir ( root )
      if len ( list ) == 0 and root <> TREE_ROOT :
        deletedir ( root, 'Tree pruning created an empty leaf `{0}`, deleting it'.format( root ))
