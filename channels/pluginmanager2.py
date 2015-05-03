# encoding: UTF-8
# api: streamtuner2
# title: User Plugin Manager Ⅱ
# description: Downloads new plugins, or updates them.
# version: 0.1
# type: hook
# category: config
# depends: uikit, config, pluginconf
# config:
#   { name: plugin_repos, type: text, value: "http://fossil.include-once.org/plugins.php/streamtuner2/contrib/*.py, http://fossil.include-once.org/plugins.php/streamtuner2/channels/*.py", description: "Plugin sources (common-repo.json)" }
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
# Further enables direct activation of existing plugins
# without restarting streamtuner2.
#


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
        
        # prepare user plugin directory
        conf.plugin_dir = conf.dir + "/plugins"
        if not os.path.exists(conf.plugin_dir):
            os.mkdir(conf.plugin_dir)
            open(conf.plugin_dir + "/__init__.py", "w").close()
        
        # register config dir for module loading
        sys.path.insert(0, conf.dir)
        channels__path__.insert(0, conf.plugin_dir)
        # config.plugin_base.append("plugins")
        # = pkgutil.extend_path(config.__path__, config.__name__)


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

        # fetch plugins
        meta = []
        for url in re.split("[\s,]+", conf.plugin_repos.strip()):
            if re.match("https?://", url):
                d = ahttp.get(url, encoding='utf-8') or []
                meta += json.loads(d)
                self.parent.status()
        
        # clean up vbox
        vbox = self.vbox
        for i,c in enumerate(vbox.get_children()):
            if i>=3:
                vbox.remove(c)
        
        # query existing plugins
        have = {name: plugin_meta(module=name) for name in module_list()}
        # add plugins
        for p in meta:
            id = p.get("$name")
            if id.find("__") == 0:   # skip __init__.py
                continue
            if have.get(id):
                if p.get("version") == have[id]["version"]:
                    continue;
            self.add_plugin(p)
        # some filler
        for i in range(1,3):
            self.add_(uikit.label(""))


    # Entry for plugin list
    def add_plugin(self, p):
        b = self.button("Install", stock="gtk-save", cb=lambda *w:self.install(p))
        text = "<b>{title}</b> <small>{version}</small>\n<small>{description}</small>\n{type}/{category}".format(**p)
        self.add_(b, text, markup=1)
    

    # Download a plugin
    def install(self, p):
        src = ahttp.get(p["$file"], encoding="utf-8")
        with open("{}/{$name}.py".format(conf.plugin_dir, **p), "w") as f:
            f.write(src)
        self.parent.status("Plugin '{$name}.py' installed.".format(**p))


    # Activate/deactivate changed plugins
    def activate_plugins(self, *w):
        pass



