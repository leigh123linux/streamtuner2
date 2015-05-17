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
                if type(w) is gtk.Entry:
                    w.set_text(str(val))
                # checkmark
                elif type(w) is gtk.CheckButton:
                    w.set_active(bool(val))
                # dropdown
                elif type(w) is ComboBoxText:
                    w.set_default(val)
                # list
                elif type(w) is gtk.ListStore:
                    w.clear()
                    for k,v in val.items():
                        w.append([k, v, True, self.app_bin_check(v)])
                    w.append(["", "", True, gtk.STOCK_NEW])
            #log.CONF("config load", prefix+key, val, type(w))

    # Store gtk widget valus back into conf. dict
    def save_config(self, config, prefix="config_", save=0):
        for key,val in config.items():
            w = self.main.get_widget(prefix + key)
            if w:
                # text
                if type(w) is gtk.Entry:
                    config[key] = w.get_text()
                # pre-defined text
                elif type(w) is ComboBoxText:
                    config[key] = w.get_active_text()
                # boolean
                elif type(w) is gtk.CheckButton:
                    config[key] = w.get_active()
                # dict
                elif type(w) is gtk.ListStore:
                    config[key] = {}
                    for row in w:
                        if row[0] and row[1]:
                            config[key][row[0]] = row[1]
            log.CONF("config save", prefix+key, val)
    
    
    # Generic Gtk callback to update ListStore when entries get edited.
    # (The main signal_connect() dict prepares individual lambda funcs
    # for each ListStore column id.)
    def list_edit(self, liststore, path, column, new_text):
        liststore[path][column] = new_text
        liststore[path][3] = self.app_bin_check(new_text)

    # return OK or CANCEL depending on availability of app
    def app_bin_check(self, v):
        bin = re.findall(r"(?<![$(`%-])\b(\w+(?:-\w+)*)", v)
        if bin:
            bin = [find_executable(bin) for bin in bin]
            if not None in bin:
                return gtk.STOCK_MEDIA_PLAY
            else:
                return gtk.STOCK_CANCEL
        else:
            return gtk.STOCK_NEW
        


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
            
            # hidden
            if opt.get("hidden"):
                continue 

            # display checkbox
            elif opt["type"] in ("bool", "boolean"):
                cb = gtk.CheckButton(opt["description"])
                add_( "config_"+opt["name"], cb, color=color )

            # drop down list
            elif opt["type"] in ("select", "choose", "options"):
                cb = ComboBoxText(ComboBoxText.parse_options(opt["select"])) # custom uikit widget
                add_( "config_"+opt["name"], cb, opt["description"], color )

            # text entry
            else:
                add_( "config_"+opt["name"], gtk.Entry(), opt["description"], color )

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
        self.plugin_options.pack_start(uikit.wrap(self.widgets, id, w, label, color, image, align))

    # Separate tab for non-channel plugins
    def add_features(self, id=None, w=None, label=None, color=None, image=None, align=20):
        self.feature_options.pack_start(uikit.wrap(self.widgets, id, w, label, color, image, align))


    # save config
    def save(self, widget):
        self.save_config(conf.__dict__, "config_")
        self.save_config(conf.plugins, "config_plugins_")
        [callback() for callback in self.hooks["config_save"]]
        conf.save(nice=1)
        self.hide()

