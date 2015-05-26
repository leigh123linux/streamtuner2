# api: python
# title: faulthandler
# description: capture fatal errors / memory fauls / Gtk and threading bugs
# version: -1
# type: io
# category: debug
# priority: development
#
# Debug Gtk/glibs/python/threading crashes.
#
# * Gdk:ERROR:/build/buildd/gtk+2.0-2.24.23/gdk/gdkregion-generic.c:1110:miUnionNonO:
#   assertion failed: (y1 < y2)
# * foobar: double free or corruption (fasttop): 0x...


import faulthandler
faulthandler.enable()
   # file=open("/tmp/st2.log", "a+"), all_threads=True

class dev_faulthandler(object):
    def __init__(sefl, *x, **kw):
        pass

