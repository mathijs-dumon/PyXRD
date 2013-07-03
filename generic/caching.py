# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

#based on : https://github.com/yosinski/python-numpy-cache/blob/master/cache.py
import hashlib
import marshal
from numpy import *
import types
import inspect

import settings

if settings.CACHE == "FILE":
    #best choice for numpy stuff:
    print "Using joblib cache"
    from joblib import Memory
    from tempfile import mkdtemp
    from generic.io import get_size, sizeof_fmt
    
    cachedir = settings.DATA_REG.get_directory_path("CACHE_DIR")
    verbose = 1 if settings.DEBUG else 0
    memory = Memory(verbose=verbose, cachedir=cachedir, compress=True)

    def cache(maxsize, cache=None, timeout=None):
        return memory.cache

    def check_cache_size(verbose=False):
        size = get_size(memory.cachedir)
        if verbose: print "Cache size is:", sizeof_fmt(size)
        if size > settings.CACHE_SIZE:
            memory.clear()

elif settings.CACHE == "MEMORY":
    print "Using in-memory cache... (NOT RECOMMENDED)"
    from generic.cache_collection import cache
elif settings.CACHE == None:
    print "Not using cache"
    def cache(maxsize, cache=None, timeout=None):
        def dummy(func):
            func.func = func
            return func
        return dummy
else:
    raise ValueError, "Unkown value for CACHE in settings.py!"