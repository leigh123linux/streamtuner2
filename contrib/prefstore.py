# encoding: UTF-8
# api: streamtuner2
# title: Config save/import/reset
# description: Allows to store, reimport or delete all preferences
# version: 0.2.1
# type: feature
# category: config
# priority: optional
#
# Adds a context menu "Staton > Extensions > Config ...", which allows
# to save or restore settings, or reset them to defaults.


from config import *
from channels import *
import ahttp
from uikit import uikit, gtk
import action
import re
import json


# hooks three functions to the main extension menu
class prefstore():

    module = 'prefstore'
    meta = plugin_meta()

    # Register callback
    def __init__(self, parent):
        if not parent:
            return
        self.parent = parent
        uikit.add_menu([parent.extensions], "Config save", self.save)
        uikit.add_menu([parent.extensions], "Config restore", self.restore)
        uikit.add_menu([parent.extensions], "Config delete", self.reset)

    # Save conf.
    def save(self, *w):
        fn = uikit.save_file(title="Export streamtuner2 config", fn="streamtuner2.config.json", formats=[("*.json", "*.json")])
        if not fn:
            return
        data = vars(conf)
        del data["args"]
        with open(fn, "w") as f:
            f.write(json.dumps(data, indent=4, sort_keys=True))
        self.parent.status("Settings saved to " + fn)

    # Save conf.
    def restore(self, *w):
        fn = uikit.save_file(title="Import streamtuner2 config", fn="streamtuner2.config.json", formats=[("*.json", "*.json")], action=gtk.FILE_CHOOSER_ACTION_OPEN, action_btn=gtk.STOCK_OPEN)
        if not fn:
            return
        with open(fn, "r") as f:
            conf.update(json.load(f))
        conf.save()
        self.parent.status("Restart streamtuner2 for changes to take effect.")

    # Clean conf.*
    def reset(self, *w):
        # clean up
        for key, value in vars(conf).items():
            if isinstance(value, dict):
                conf[key] = {}
            elif key in ("dir", "share", "args"):
                pass
            else:
                del conf[key]
        # add defs
        conf.defaults()
        for name in module_list():
            if not name in conf.plugins:
                conf.add_plugin_defaults(plugin_meta(module=name), name)
        # show configwin
        self.parent.status('<span background="yellow">Default settings restored. Press [save] to apply them, then restart Streamtuner2.</span>', markup=1)
        self.parent.configwin.open(None)
