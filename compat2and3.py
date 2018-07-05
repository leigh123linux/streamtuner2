# encoding: UTF-8
# api: python 
# type: functions
# title: Python2 and Python3 compatibility
# version: 0.2
#
# Renames some Python3 modules into their Py2 equivalent.
# Slim local alternative to `six` module.


import sys


# Python 2
if sys.version_info < (3,0):

    # version tags
    PY2 = 1
    PY3 = 0

    # basic functions
    xrange = xrange
    range = xrange
    unicode = unicode

    # urllib modules
    import urllib
    import urllib2
    from urllib import quote_plus as urlencode, unquote as urldecode, quote as urlquote
    import urlparse
    import cookielib
    
    # filesys
    from StringIO import StringIO
    from gzip import GzipFile
    def gzip_decode(bytes):
        return GzipFile(fileobj=StringIO(bytes)).read()
        # return zlib.decompress(bytes, 16 + zlib.MAX_WBITS)    # not fully compatible


# Python 3
else:

    # version tags
    PY2 = 0
    PY3 = 1

    # basic functions
    xrange = range
    unicode = str
    unichr = chr

    # urllib modules
    import urllib.request as urllib
    import urllib.request as urllib2
    from urllib.parse import quote_plus as urlencode, unquote as urldecode, quote as urlquote
    import urllib.parse as urlparse
    from http import cookiejar as cookielib
    
    # filesys
    from io import StringIO
    from gzip import decompress as gzip_decode


# Both

# find_executable() is only needed by channels/configwin
try:
    from distutils.spawn import find_executable
except:
    import os
    def find_executable(bin):
        exists = [os.path.exists(dir+"/"+bin) for dir in os.environ.get("PATH").split(":")+["/"]]
        return exists[0] if len(exists) else None

    
