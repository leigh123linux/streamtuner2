#
# encoding: UTF-8
# api: streamtuner2
# title: Plugin handling
# description: Channels and feature plugins reside in channels/
# type: R
# category: core
# priority: core
# pack:
#   file.py, _generic.py, global_key.py, history.py, icast.py,
#   internet_radio.py, itunes.py, jamendo.py, links.py, live365.py,
#   modarchive.py, myoggradio.py, punkcast.py, shoutcast.py,
#   surfmusik.py, tunein.py, timer.py, xiph.py, youtube.py,
#   radiotray.py, *.png
#
#
# Just exports GenericChannel and ChannelPlugin. Makes module
# scanning and meta data parsing available.  Currently just for
# globally-installed /usr/share/streamtuner2/channel/*.py plugins.
#
#

from channels._generic import *

# Only reexport plugin classes
__all__ = [
    "GenericChannel", "ChannelPlugin"
]



# Search through ./channels/ and get module basenames.
# Also order them by conf.channel_order
#
def module_list():

    # find plugin files
    ls = os.listdir(conf.share + "/channels/")
    ls = [fn[:-3] for fn in ls if re.match("^[a-z][\w\d_]+\.py$", fn)]
    
    # resort with tab order
    order = [module.strip() for module in conf.channel_order.lower().replace(".","_").replace("-","_").split(",")]
    ls = [module for module in (order) if (module in ls)] + [module for module in (ls) if (module not in order)]

    return ls

