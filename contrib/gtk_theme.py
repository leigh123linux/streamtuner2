# api: streamtuner2
# title: Gtk theme setting
# description: Gtk theme switching in Streamtuner2. (Beware of crashes!)
# type: feature
# category: ui
# version: 0.2
# config:
#    { name: theme, type: select, select: "default=default", description: "Theme name" }
#    { name: theme_instant, type: bool, value=0, description: "Activate on the fly." }
# priority: experimental
#
# Brings back the theme switching option - for Gtk2 + Gtk3 now.
#
# Note that not all themes can be loaded on the fly. And may hang
# streamtuner2 even. Most require an application restart still.
# Which is why this is not a built-in feature anymore.
#
# Btw, you could alternatively use GTK2_RC_FILES= or GTK_THEME=
# environment variables for this.


import os
from config import *
import uikit
from compat2and3 import *



# register a key
class gtk_theme(object):

    # plugin info
    module = __name__
    meta = plugin_meta()
    theme_dirs = [uikit.gtk.rc_get_theme_dir(), conf.dir + "/themes", conf.share + "/themes"]

    # register
    def __init__(self, parent):
        self.parent = parent
        parent.hooks["config_load"].append(self.list_themes)
        parent.hooks["config_save"].append(self.apply_theme)
        self.apply_theme(True)

    # gtk.rc_parse() called on configwin.save and ST2 startup
    def apply_theme(self, now=False):
        if conf.theme == "default":
            return
        # path depends on version
        if uikit.ver == 2:
            rc = "gtk-2.0/gtkrc"
        else:
            rc = "gtk-3.0/gtk.css"

        # look if theme exists
        for fn in ["%s/%s/%s" % (dir, conf.theme, rc) for dir in self.theme_dirs]:
            if not os.path.exists(fn):
                continue
            log.GTK_THEME_FILE(fn)
            # .GTKRC/Gtk2
            if uikit.ver == 2:
                uikit.gtk.rc_parse(fn)
                if now or conf.theme_instant:
                    uikit.gtk.rc_reparse_all()
            # .CSS/Gtk3
            elif now or conf.theme_instant:
                #ctx = uikit.gtk.StyleContext    # global
                ctx = self.parent.win_streamtuner2.get_style_context() # main window
                screen = uikit.gtk.gdk.Screen.get_default()
                style = uikit.gtk.CssProvider()
                style.load_from_file(fn)
                ctx.add_provider_for_screen(screen, style, uikit.gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

   # list Gtk themes, append to existing dropdown box
    def list_themes(self):
    
        # get ComboBoxText widget (wrapper object)
        cb = self.parent.widgets["config_theme"]
        cb.ls.clear()
        
        # search themes
        themes = []
        for dir in self.theme_dirs:
            if os.path.exists(dir):
                for fn in os.listdir(dir):
                    if os.path.exists("%s/%s/gtk-%s.0" % (dir, fn, uikit.ver)):
                        themes.append(fn)
        themes = ["default"] + sorted(themes)
        
        # add to list
        for t in themes:
            cb.ls.append([t, t])
        if ("theme" in conf) and (conf.theme in themes):
            cb.set_default(conf.theme)
        else:
            cb.set_default("default")

