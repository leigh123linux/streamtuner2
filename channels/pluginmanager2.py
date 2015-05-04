# encoding: UTF-8
# api: streamtuner2
# title: User Plugin Manager Ⅱ
# description: Downloads new plugins, or updates them.
# version: 0.2
# type: hook
# category: config
# depends: uikit >= 1.9, config >= 2.7, streamtuner2 >= 2.1.8, pluginconf < 1.0
# config:
#   { name: plugin_repos, type: text, value: "http://fossil.include-once.org/repo.json/streamtuner2/contrib/*.py, http://fossil.include-once.org/repo.json/streamtuner2/channels/*.py", description: "Plugin repository JSON source references." }
#   { name: plugin_auto, type: boolean, value: 1, description: Apply plugin activation/disabling without restart. }
# priority: extra
# support: experimental
#
# Scans for new plugins from the repository server, using
# a common-repo.json list. Compares new against installed
# plugins, and permits to update or download new ones.
#
# User plugins go into ~/.config/streamtuner2/channels/
# and will be picked up in favour of system-installed ones.
#
# Further enables direct activation of existing channel
# plugins, often without restarting streamtuner2.
#
# Actually rather trivial. The Gtk interface building just
# makes this handler look complicated.


import imp
import config
import pkgutil
from channels import __path__ as channels__path__
import os
from config import *
from uikit import *
import ahttp
import json
import compat2and3
from xml.sax.saxutils import escape as html_escape


# Plugin manager
class pluginmanager2(object):

    module = "pluginmanager2"
    meta = plugin_meta()
    parent = None
    vbox = None


    # Hook up
    def __init__(self, parent):

        # main references
        self.parent = parent
        conf.add_plugin_defaults(self.meta, self.module)
        
        # config dialog
        parent.hooks["config_load"].append(self.add_config_tab)
        parent.hooks["config_save"].append(self.activate_plugins)
        parent.hooks["config_save"].append(self.clean_config_vboxen)
        
        # prepare user plugin directory
        conf.plugin_dir = conf.dir + "/plugins"
        if not os.path.exists(conf.plugin_dir):
            os.mkdir(conf.plugin_dir)
            open(conf.plugin_dir + "/__init__.py", "w").close()
        
        # Register user config dir "~/.config/streamtuner2/plugins" for module loading
        sys.path.insert(0, conf.dir)
        
        # Let channels.* package load modules from two directories
        channels__path__.insert(0, conf.plugin_dir)


    # Craft new config dialog notebook tab
    def add_config_tab(self, *w):
        if self.vbox:
            return

        # Notebook tab = label, content = vbox in scrolledwindow
        w = self.parent.config_notebook
        self.vbox = gtk.VBox(True, 5)
        vp = gtk.Viewport()
        vp.add(self.vbox)
        sw = gtk.ScrolledWindow()
        sw.add(vp)  # ScrolledWindow → Viewport → VBox
        # label
        label = gtk.EventBox()
        label.add(gtk.Label(" 📦 Add "))
        label.show_all()
        sw.show_all()
        # add page
        tab = w.insert_page_menu(sw, label, label, -1)
        
        # Prepare some text
        self.add_(uikit.label("\n<b><big>Install or update plugins</big></b>", size=520, markup=1))
        self.add_(uikit.label("You can update existing plugins, or install new contrib/ channels. User plugins reside in ~/.config/streamtuner2/plugins/ and can even be modified there (such as setting a custom # color: entry).\n", size=520, markup=1))
        self.add_(self.button("Refresh", stock="gtk-refresh", cb=self.refresh), "Show available plugins from repository\nhttp://fossil.include-once.org/streamtuner2/")
        self.add_(gtk.image_new_from_stock("gtk-info", gtk.ICON_SIZE_LARGE_TOOLBAR), "While plugins are generally compatible across releases, newer versions may also require to update the streamtuner2 core setup.\n Please note that plugin installation is rather experimental. It still requires a restart of ST2 to activate them.")
        for i in range(1,10):
            self.add_(uikit.label(""))


    # Append to vbox
    def add_(self, w, label=None, markup=0):
        w = uikit.wrap(w=w, label=label, align=10, label_size=400, label_markup=1)
        self.vbox.add(w)

    # Create button, connect click signal    
    def button(self, label, stock=None, cb=None):
        b = gtk.Button(label, stock=stock)
        b.connect("clicked", cb)
        return b

    
    # Add plugin list
    def refresh(self, *w):

        # Fetch repository JSON list
        meta = []
        for url in re.split("[\s,]+", conf.plugin_repos.strip()):
            if re.match("https?://", url):
                d = ahttp.get(url, encoding='utf-8') or []
                meta += json.loads(d)
                self.parent.status()
        
        # Clean up placeholders in vbox
        _ = [self.vbox.remove(c) for c in self.vbox.get_children()[3:]]
        
        # Query existing plugins
        dep = dependency()
        # Attach available downloads
        for newpl in meta:
            id = newpl.get("$name")
            # skip __init__.py
            if id.find("__") == 0:
                continue
            # exclude if newer/current version already installed
            if dep.have.get(id) and dep.have[id]["version"] >= newpl.get("version"):
                continue
            # check dependencies
            #newpl["depends"] = "streamtuner2 < 2.2.0, config >= 2.5"
            if not dep.depends(newpl):
                continue
            self.add_plugin(newpl)

        # Readd some filler labels
        _ = [self.add_(uikit.label("")) for i in range(1,3)]


    # Entry for plugin list
    def add_plugin(self, p):
        b = self.button("Install", stock="gtk-save", cb=lambda *w:self.install(p))
        p = self.update_p(p)
        text = "<b>$title</b>, "\
               "<small>version:</small> <span weight='bold' color='orange'>$version</span>, "\
               "<small>type: <i><span color='#559'>$type</span></i> "\
               "category: <i><span color='blue'>$category</span></i></small>\n"\
               "<span variant='smallcaps' color='#333'>$description</span>\n"\
               "<span size='small' color='#532' weight='ultralight'>$extras, <a href='view-source:$file'>view src</a></span>"
        self.add_(b, safe_format(text, **p), markup=1)

        
    # Add placeholder fields
    def update_p(self, p):
        fields = ("status", "priority", "support", "author", "depends")
        extras = ["{}: <b>{}</b>".format(n, html_escape(p[n])) for n in fields if p.get(n)]
        p["extras"] = " ".join(["💁"] + extras)
        p["file"] = p["$file"]
        for field in ("version", "title", "description", "type", "category"):
            p.setdefault(field, "-")
        return p
    

    # Download a plugin
    def install(self, p):
        src = ahttp.get(p["$file"], encoding="utf-8")
        with open("{}/{$name}.py".format(conf.plugin_dir, **p), "w") as f:
            f.write(src)
        self.parent.status("Plugin '{$name}.py' installed.".format(**p))


    # Empty out [channels] and [feature] tab in configdialog, so it rereads them
    def clean_config_vboxen(self, *w):
        self.parent.configwin.first_open = 1
        for vbox in [self.parent.plugin_options, self.parent.feature_options]:
            for c in vbox.get_children()[1:]:
                vbox.remove(c)


    # Activate/deactivate changed plugins
    def activate_plugins(self, *w):
        if not conf.plugin_auto:
            return
        p = self.parent
        for name,act in conf.plugins.items():

            # disable channel plugin
            if not act and name in p.channels:
                p.notebook_channels.remove_page(p.channel_names.index(name))
                del p.channels[name]

            # feature plugins usually have to many hooks
            if not act and name in p.features:
                log.WARN("Cannot disable feature plugin '{}'.".format(name))
                p.status("Disabling feature plugins requires a restart.")

        # just let main load any new plugins
        p.load_plugin_channels()



# Do minimal depends: probing
class dependency(object):

    # prepare list of known plugins and versions
    def __init__(self):
        self.have = {name: plugin_meta(module=name) for name in module_list()}
        # dependencies on core modules are somewhat more interesting:
        self.have.update({
            "streamtuner2": plugin_meta(module="st2", plugin_base=["config"]),
            "uikit": plugin_meta(module="uikit", plugin_base=["config"]),
            "config": plugin_meta(module="config", plugin_base=["config"]),
            "action": plugin_meta(module="action", plugin_base=["config"]),
        })
    have = {}

    # depends:    
    def depends(self, plugin):
        if plugin.get("depends"):
            d = self.deps(plugin["depends"])
            if not self.cmp(d, self.have):
                return False
        return True

    # Split trivial "pkg, mod >= 1, uikit < 4.0" list
    def deps(self, dep_str):
        d = []
        for dep in re.split(r"\s*[,;]+\s*", dep_str):
            # skip deb:pkg-name, rpm:name, bin:name etc.
            if not len(dep) or dep.find(":") >= 0:
                continue
            # find comparison and version num
            m = re.search(r"([\w.-]+)\s*([>=<!~]+)\s*([\d.]+([-~.]\w+)*)", dep + " >= 0")
            if m and m.group(2):
                d.append([m.group(i) for i in (1,2,3)])
        return d
    
    # Do actual comparison
    def cmp(self, d, have):
        r = True
        for name, op, ver in d:
            # skip unknown plugins, might be python module references ("depends: re, json")
            if not have.get(name, {}).get("version"):
                continue
            curr = have[name]["version"]
            tbl = {
               ">=": curr >= ver,
               "<=": curr <= ver,
               "==": curr == ver,
               ">":  curr > ver,
               "<":  curr < ver,
               "!=": curr != ver,
            }
            r &= tbl.get(op, True)
        return r


# Alternative to .format(), with keys possibly being absent
from string import Template
def safe_format(str, **kwargs):
    return Template(str).safe_substitute(**kwargs)
