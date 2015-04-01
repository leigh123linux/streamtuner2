# encoding: UTF-8
# api: python 
# type: functions
# title: Python2 and Python3 compatibility
# version: 0.1
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
    from urllib import urlencode
    import urlparse
    import cookielib
    
    # filesys
    from StringIO import StringIO


# Python 3
else:

    # version tags
    PY2 = 0
    PY3 = 1

    # basic functions
    xrange = range
    unicode = str

    # urllib modules
    import urllib.request as urllib
    import urllib.request as urllib2
    from urllib.parse import urlencode
    import urllib.parse as urlparse
    from http import cookiejar as cookielib
    
    # filesys
    from io import StringIO

    