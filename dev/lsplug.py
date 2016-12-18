# encoding: UTF-8
# description: list available plugins for wiki

import os, re
from config import *
from base64 import b64decode
import pluginconf
pluginconf.module_base = "config"
pluginconf.plugin_base = ["channels", "contrib"]#, conf.share+"/channels", conf.dir+"/plugins"]

txt_p = """
### Channels

| Title | Ver | Type | Category | Subdir | Priority | Feat. | Description |
| ----- | --- | ---- | -------- | ------ | -------- | ----- | ----------- |
"""
txt_f = """
### Features

| Title | Ver | Type | Category | Subdir | Priority | Description |
| ----- | --- | ---- | -------- | ------ | -------- | ----------- |
"""

# read out additional plugin info
def get_flags(e, fn):
    flags = ""
    with open(fn, "r") as f:
        src = f.read()
    if re.search("^\s*has_search = True", src, re.M):
        flags += "🔍 "
    mth = e.get("extraction-method", "")
    if re.search("regex", mth):
        flags += "®"
    if re.search("dom|xml", mth):
        flags += "¶"
    if re.search("json", mth):
        flags += "{"
    if re.search("-handler|-hook", mth):
        flags += " ⏳"
    return flags        


all_meta = pluginconf.all_plugin_meta()
for name,e in [(name, all_meta[name]) for name in sorted(all_meta)]:
    

    # print table
    if "title" in e:
        fn = "./channels/%s.py" % e["fn"]
        if os.path.exists(fn):
            e["dir"] = "[**dist** ✔](wiki/channels)"
        else:
            fn = "./contrib/%s.py" % e["fn"]
            e["dir"] = "[contrib/](wiki/contrib)"
        try:
            if e["type"] == "channel":
                e["flags"] = get_flags(e, fn)
                txt_p = txt_p + "| [{title}]({url}) | **{version}** | {type} | {category} | {dir} | *{priority}* | {flags} | {description} |\n".format(**e)
            else:
                txt_f = txt_f + "| {title} | **{version}** | {type} | {category} | {dir} | *{priority}* | {description} |\n".format(**e)
        except Exception, e:
            print "ERROR*** ", name, e
            pass
    
    # extract icon
    if False and "png" in e:
        with open("help/img/%s_%s.png" % (e["type"], name), "wb") as f:
            f.write(b64decode(e["png"]))
            
print txt_p
print "Features: 🔍 search / ® regex / ¶ dom / { json / ⏳ double extraction delay"
print txt_f
