# api: streamtuner2
# title: Config dialog
# description: Allows to configure players, options, and plugins
# version: 2.5
# type: feature
# category: ui
# config: -
# priority: core
# 
# Configuration dialog for audio applications,
# general settings, and plugin activaiton and
# their options.


from uikit import *
import channels
from config import *
from pluginconf import all_plugin_meta
import re


# Settings window
#
# Interacts with main.* window (gtkBuilder widgets)
# and conf.* dictionary.
#
class configwin (AuxiliaryWindow):

    # control flags
    meta = plugin_meta()


    # Display win_config, pre-fill text fields from global conf. object
    def open(self, widget):
        if self.first_open:
            self.add_plugins()
            self.first_open = 0
            self.win_config.resize(565, 625)
        self.load_config(conf.__dict__, "config_")
        self.load_config(conf.plugins, "config_plugins_")
        [callback() for callback in self.hooks["config_load"]]
        self.win_config.show_all()
    first_open = 1

    # Hide window
    def hide(self, *args):
        self.win_config.hide()
        return True

    
    # Load values from conf. store into gtk widgets
    def load_config(self, config, prefix="config_"):
        for key,val in config.items():
            w = self.main.get_widget(prefix + key)
            if w:
                # input field
                if isinstance(w, gtk.Entry):
                    w.set_text(str(val))
                # checkmark
                elif isinstance(w, gtk.CheckButton):
                    w.set_active(bool(val))
                # dropdown
                elif isinstance(w, ComboBoxText):
                    w.set_default(val)
                # number
                elif isinstance(w, gtk.SpinButton):
                    w.set_value(int(val))
                # list
                elif isinstance(w, gtk.ListStore) and isinstance(val, dict):
                    w.clear()
                    for k,v in val.items():
                        w.append([k, v, uikit.app_bin_check(v)])
                    w.append(["", "", gtk.STOCK_NEW])
            #log.CONF("config load", prefix+key, val, type(w))

    # Store gtk widget valus back into conf. dict
    def save_config(self, config, prefix="config_", save=0):
        for key,val in config.items():
            w = self.main.get_widget(prefix + key)
            if w:
                # text
                if isinstance(w, gtk.Entry):
                    config[key] = w.get_text()
                # pre-defined text
                elif isinstance(w, ComboBoxText):
                    config[key] = w.get_active_text()
                # boolean
                elif isinstance(w, gtk.CheckButton):
                    config[key] = w.get_active()
                # int
                elif isinstance(w, gtk.SpinButton):
                    config[key] = int(w.get_value(val))
                # dict
                elif isinstance(w, gtk.ListStore):
                    config[key] = {}
                    for row in w:
                        if row[0] and row[1]:
                            config[key][row[0]] = row[1]
            log.CONF("config save", prefix+key, val)
    

    # iterate over channel and feature plugins
    def add_plugins(self):
        ls = all_plugin_meta()
        for name,meta in sorted(ls.items(), key=lambda e: e[1]["type"]+e[1]["title"].lower(), reverse=False):
            if not name in conf.plugins:
                conf.plugins[name] = False
            add_ = self.add_channels if meta.get("type") == "channel" else self.add_features
            self.add_plg(name, meta, add_)
        pass

    # Description text
    plugin_text = "<span size='larger' weight='heavy'>{title}</span> "\
                + "<span style='italic' foreground='slate blue'>({type}/{category})</span> "\
                + "<span weight='bold' foreground='#777777'>{version}</span>\n"\
                + "<span size='smaller' stretch='ultraexpanded'>{description}</span>"

    # Add [x] plugin setting, and its configuration definitions, set defaults from conf.*
    def add_plg(self, name, meta, add_):

        # Plugin enable button
        cb = gtk.CheckButton(name)
        cb.set_sensitive(not meta.get("priority") in ("core", "required", "builtin"))
        cb.get_children()[0].set_markup(self.plugin_text.format(**meta))
        cb.set_tooltip_text(self._tooltip(meta))
        add_( "config_plugins_"+name, cb, color=meta.get("color"), image=meta.get("png"), align=0)

        # Default values are already in conf[] dict
        # (now done in conf.add_plugin_defaults)
        for opt in meta["config"]:
            color = opt.get("color", None)
            type = opt.get("type", "str")
            description = opt.get("description", "./.")
            
            # hidden
            if opt.get("hidden"):
                continue 

            # display checkbox
            elif opt["type"] in ("bool", "boolean"):
                cb = gtk.CheckButton(opt["description"])
                description = None

            # drop down list
            elif opt["type"] in ("select", "choose", "options"):
                cb = ComboBoxText(ComboBoxText.parse_options(opt["select"])) # custom uikit widget

            # numeric
            elif opt["type"] in ("int", "integer", "numeric"):
                adj = gtk.Adjustment(0, 0, 5000, 1, 10, 0)
                if ver == 2:
                    cb = gtk.SpinButton(adj, 1.0, 0)
                else:
                    cb = gtk.SpinButton()
                    cb.set_adjustment(adj)
                    cb.set_digits(0)

            # ListView
            elif opt["type"] in ("list", "table", "array", "dict"):
                cb, ls = uikit.config_treeview(opt, opt.get("columns", "Key,Value").split(","))
                add_("cfgui_tv", cb, "", None)
                self.widgets["config_" + opt["name"]] = ls
                add_({}, uikit.label("<small>%s</small>" % description, markup=True, size=455))
                continue

            # text field
            else:
                cb = gtk.Entry()
           
            add_( "config_"+opt["name"], cb, description, color )

        # Spacer between plugins
        add_( None, gtk.HSeparator() )

    # Reformat `doc` linebreaks for gtk.tooltip
    def _tooltip(self, meta):
        doc = meta.get("doc", "").strip()
        if ver < 3:
            doc = re.sub("(?<=\S) *\n(?! *\n)", " ", doc)
        return doc

    # Put config widgets into channels/features configwin notebooks
    def add_channels(self, id=None, w=None, label=None, color=None, image=None, align=20):
        self.plugin_options.pack_start(uikit.wrap(self.widgets, id, w, label, color, image, align, label_markup=1))

    # Separate tab for non-channel plugins
    def add_features(self, id=None, w=None, label=None, color=None, image=None, align=20):
        self.feature_options.pack_start(uikit.wrap(self.widgets, id, w, label, color, image, align, label_markup=1))


    # save config
    def save(self, widget):
        self.save_config(conf.__dict__, "config_")
        self.save_config(conf.plugins, "config_plugins_")
        [callback() for callback in self.hooks["config_save"]]
        conf.save(nice=1)
        self.hide()

