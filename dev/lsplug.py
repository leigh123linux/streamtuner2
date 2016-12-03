# description: list available plugins for wiki

from config import *
from base64 import b64decode
import pluginconf
pluginconf.module_base = "config"
pluginconf.plugin_base = ["channels", "contrib"]#, conf.share+"/channels", conf.dir+"/plugins"]

for name,e in pluginconf.all_plugin_meta().items():

    # print table
    if "title" in e:
        try:
            print "| [{title}]({url}) | **{version}** | {type} | {category} | *{priority}* | {description} |".format(**e)
        except Exception, e:
            print "ERROR*** ", name, e
    
    # extract icon
    if False and "png" in e:
        with open("help/img/%s_%s.png" % (e["type"], name), "wb") as f:
            f.write(b64decode(e["png"]))
    