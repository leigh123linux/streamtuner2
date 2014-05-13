#
# encoding: UTF-8
# api: streamtuner2
# title: Plugin handling
# description: Channels and feature plugins reside in channels/
# api: python
# type: R
# category: core
# priority: core
#
#
#
#
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


# Parse plugin comment blocks.
#
def module_meta():
    meta = {}

    rx_meta = re.compile(r"""^#\s*(\w+):\s*(.+)$""", re.M)

    # Loop through all existing module.py scripts
    for name in module_list():
       meta[name] = dict(title="", type="", description="")

       # Read and regex-extract into dict
       with open("%s/channels/%s.py" % (conf.share, name)) as f:
           for field in re.findall(rx_meta, f.read(1024)):
               meta[name][field[0]] = field[1]

    return meta




