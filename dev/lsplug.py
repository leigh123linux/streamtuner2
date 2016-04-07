# description: list available plugins for wiki

from config import *
import pluginconf
pluginconf.module_base = "config"
pluginconf.plugin_base = ["channels", "contrib"]#, conf.share+"/channels", conf.dir+"/plugins"]

for name,e in pluginconf.all_plugin_meta().items():
    if "title" in e:
        try:
            print "| {title} | {version} | {category} | {url} | {description} |".format(**e)
        except:
            None