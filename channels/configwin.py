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
        m = re.search("(?![$(`])\S+", v)
        if m and m.group(0):
            if find_executable(m.group(0)):
                return gtk.STOCK_MEDIA_PLAY
            else:
                return gtk.STOCK_CANCEL
        else:
            return gtk.STOCK_NEW
        


    # iterate over channel and feature plugins
    def add_plugins(self):
        ls = dict([(name, plugin_meta(module=name)) for name in module_list()])
        #for name in module_list():
        #    if name in self.channels:
        #        ls[name] = self.channels[name].meta
        #    elif name in self.features:
        #        ls[name] = self.features[name].meta
        #    else:
        #        ls[name] = plugin_meta(module=name)
        for name,meta in sorted(ls.items(), key=lambda e: e[1]["type"]+e[1]["title"].lower(), reverse=False):
            if not name in conf.plugins:
                conf.plugins[name] = False
            self.add_plg(name, meta)


    # add configuration setting definitions from plugins
    plugin_text = "<span size='larger' weight='heavy'>%s</span> "\
                + "<span style='italic' foreground='slate blue'>(%s/%s)</span> "\
                + "<span weight='bold' foreground='#777777'>%s</span>\n"\
                + "<span size='smaller' stretch='ultraexpanded'>%s</span>"
    def add_plg(self, name, meta):
        # add plugin load entry
        cb = gtk.CheckButton(name)
        cb.set_sensitive(not meta.get("priority") in ("core", "required", "builtin"))
        cb.get_children()[0].set_markup(self.plugin_text % (meta.get("title", name), meta.get("type", "plugin"), meta.get("category", "addon"), meta.get("version", "./."), meta.get("description", "no description")))
        cb.set_tooltip_text(re.sub("(?<=\S) *\n(?! *\n)", " ",meta.get("doc", "")).strip())
        self.add_( "config_plugins_"+name, cb, color=meta.get("color"), image=meta.get("png"))

        # default values are already in conf[] dict (now done in conf.add_plugin_defaults)
        for opt in meta["config"]:
            color = opt.get("color", None)
            # display checkbox
            if opt["type"] == "boolean":
                cb = gtk.CheckButton(opt["description"])
                self.add_( "config_"+opt["name"], cb, color=color )
            # drop down list
            elif opt["type"] == "select":
                cb = ComboBoxText(ComboBoxText.parse_options(opt["select"])) # custom uikit widget
                self.add_( "config_"+opt["name"], cb, opt["description"], color )
            # text entry
            else:
                self.add_( "config_"+opt["name"], gtk.Entry(), opt["description"], color )

        # spacer 
        self.add_( "filler_pl_"+name, gtk.HSeparator() )


    # Put config widgets into config dialog notebook, wrap with label, or background, retain widget id/name
    def add_(self, id=None, w=None, label=None, color=None, image=None):
        if id:
            self.widgets[id] = w
        if label:
            if type(w) is gtk.Entry:
                w.set_width_chars(11)
            w = uikit.hbox(w, uikit.label(label))
        if image:
            pix = gtk.image_new_from_pixbuf(uikit.pixbuf(image))
            if pix:
                w = uikit.hbox(w, pix, exr=False)
        if color:
            w = uikit.bg(w, color)
        self.plugin_options.pack_start(w)
    
    # save config
    def save(self, widget):
        self.save_config(conf.__dict__, "config_")
        self.save_config(conf.plugins, "config_plugins_")
        [callback() for callback in self.hooks["config_save"]]
        conf.save(nice=1)
        self.hide()

