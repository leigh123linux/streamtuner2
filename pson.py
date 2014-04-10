#
# encoding: UTF-8
# api: python
# type: functions
# title: json emulation
# description: simplify usage of some gtk widgets
# version: 1.7
# author: mario
# license: public domain
#
#
#  This module provides the JSON api. If the python 2.6 module
#  isn't available, it provides an emulation using str() and
#  eval() and Python notation. (The representations are close.)
#
#  Additionally it filters out any left-over objects. Sometimes
#  pygtk-objects crawled into the streams[] lists, because rows
#  might have been queried from the widgets.
#       (Need to find out if that still happens..)
#
#  filter_data should become redundant, as mygtk.columns now
#  converts unicode to str in Py2. And since we depend on Py2.7
#  anway the JSON-like Python serialization should be dropped.
#


#-- reading and writing json (for the config module)  ----------------------------------

import sys
from compat2and3 import unicode

# try to load the system module first
try:
        from json import dump as json_dump, load as json_load
except:
        print("no native Python JSON module")


#except:
    # pseudo-JSON implementation
    # - the basic python data types dict,list,str,int are mostly identical to json
    # - therefore a basic str() conversion is enough for writing
    # - for reading the more bothersome eval() is used
    # - it's however no severe security problem here, because we're just reading
    #   local config files (written by us) and accept no data from outside / web
    # NOTE: This code is only used, if the Python json module (since 2.6) isn't there.


# store object in string representation into filepointer
def dump(obj, fp, indent=0):

        obj = filter_data(obj)
        
        try:
                return json_dump(obj, fp, indent=indent, sort_keys=(indent and indent>0))
        except:
                return fp.write(str(obj))
                # .replace("'}, ", "'},\n ")    # add whitespace
              	# .replace("', ", "',\n "))
              	# .replace("': [{'", "':\n[\n{'")
        pass


# load from filepointer, decode string into dicts/list
def load(fp):
        try:
                #print("try json")
                r = json_load(fp)
#                r = filter_data(r)   # turn unicode() strings back into str() - pygtk does not accept u"strings"
        except:
                #print("fall back on pson")
                fp.seek(0)
                r = eval(fp.read(1<<27))   # max 128 MB
                # print("fake json module: in python variable dump notation")

        if r == None:
                r = {}
        return r


# removes any objects, turns unicode back into str
def filter_data(obj):
        if type(obj) in (int, float, bool, str):
                return obj
#        elif type(obj) == str:   #->str->utf8->str
#                return str(unicode(obj))
        elif type(obj) == unicode:
                return str(obj)
        elif type(obj) in (list, tuple, set):
                obj = list(obj)
                for i,v in enumerate(obj):
                        obj[i] = filter_data(v)
        elif type(obj) == dict:
                for i,v in list(obj.items()):
                        i = filter_data(i)
                        obj[i] = filter_data(v)
        else:
                print("invalid object in data, converting to string: ", type(obj), obj)
                obj = str(obj)
        return obj



