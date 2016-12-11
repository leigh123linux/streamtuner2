# encoding: utf-8
# title: Spec buttons for apps
# description: Adds configurable mini toolbar buttons
# version: 0.8
# depends: streamtuner2 >= 2.2.0
# type: feature
# category: ui
# config:
#    { name: specbutton_rows, value: 2, max: 4, type: int, description: "Number of rows to arrange buttons in." }
#    { name: specbuttons, type: dict, columns: "Icon,Command", description: "Icons can be `<a href='http://www.pygtk.org/pygtk2reference/gtk-stock-items.html'>gtk-xyz</a>` internal names. Else use `/usr/share/icon/*.png` file names. Icon file basenames will be expanded into full paths." }
# documentation:
#    http://fossil.include-once.org/streamtuner2/info/43b36ed35b1488d5
#
# Adds the mini/extra buttons in the toolbar, which allow to control your
# audio player or run other system commands.
#
#  [Icon]  [Cmd]
#
#  volume  pavucontrol
#
#  up      amixer sset Master 5%+
#
#  kill    pkill vlc
#
# Icons can be gtk-xyz icon names or /usr/share/icon/* PNG files.
# Each command may use streamtuner2 placeholders like %g or %url and $title.


import os.path
import subprocess
import math
import re
from config import conf, log, plugin_meta
import action
from uikit import gtk


# Extra/mini buttons in toolbar
class specbuttons(object):
    meta = plugin_meta()
    module = __name__

    # Hook toolbar label
    def __init__(self, parent):
        if not parent:
            return
        self.parent = parent
        conf.add_plugin_defaults(self.meta, self.module)
        self.specbuttons = parent.get_widget("specbuttons")
        parent.hooks["init"].append(self.update_buttons)
        parent.hooks["config_save"].append(self.update_paths)
        parent.specbuttons.show()

    # Extra buttons
    def update_buttons(self, parent):
    
        # define table width (2 rows default)
        y = conf.specbuttons_rows if "specbuttons_rows" in conf else 2
        y = max(min(int(conf.specbutton_rows), 4), 1) # 1 <= y <= 4
        self.specbuttons.resize(y, int(math.ceil(len(conf.specbuttons) / y)))
        # clean up
        for widget in self.specbuttons.get_children():
            widget.destroy()
        
        # add icon buttons
        for xy, (btn, cmd) in enumerate(conf.specbuttons.items()):
            #log.IN(btn, cmd)
            w_btn = gtk.Button()
            w_btn.set_image(self.icon(btn))
            w_btn.connect("clicked", lambda x0, cmd=cmd, *x: self.action(cmd))
            self.specbuttons.attach(
                child = w_btn,
                left_attach   = int(xy / y),
                right_attach  = int(xy / y) + 1,
                top_attach    = xy % y,
                bottom_attach = (xy % y) + 1,
                xoptions = gtk.EXPAND,
                yoptions = gtk.EXPAND,
                xpadding = 1,
                ypadding = 1
            )
        self.specbuttons.show_all()

    # Instantiate Image from gtk-* string or path
    def icon(self, btn):
        wi = gtk.Image()
        if (btn.find("gtk-") == 0):
            wi.set_from_stock(btn, gtk.ICON_SIZE_SMALL_TOOLBAR)
        else:
            if not os.path.exists(btn):
                btn = self.locate(btn)
                log.DATA(btn)
            if btn:
                wi.set_from_file(btn)
            else:
                wi.set_from_stock("gtk-image-missing", gtk.ICON_SIZE_SMALL_TOOLBAR)
        return wi

    # Look for image basename (e.g. "play") in /usr/share/icons/*.* and /pixmaps/*
    def locate(self, btn):
        f = subprocess.Popen(["locate", "/usr/share/[pi]*s/*%s*.*" % btn], stdout=subprocess.PIPE)
        path, err = f.communicate()
        if not err:
            return path.split("\n")[0]

    # Update paths when saving config dialog
    def update_paths(self):
        r = {}
        for btn, cmd in conf.specbuttons.items():
            # replace "gtk." to "gtk-"
            if re.match("^gtk\.\w+", btn, re.I):
                btn = re.sub("[._]+", "-", btn).lower()
            # not /path or gtk-
            elif not re.match("^/|\./|gtk-", btn):
                path = self.locate(btn)
                if path:
                    btn = path
                else:
                    log.WARN("Extra button icon '%s' could not be found" % btn)
            r[btn] = cmd
        conf.specbuttons = r
        self.update_buttons(self.parent)

    # Button callback, allow for %url/%title placeholders
    def action(self, cmd):
        if re.search("[%$]", cmd):
            row = self.parent.channel().row()
            cmd = action.run_fmt_url(cmd, row=row, add_default=False, cmd=cmd)
        action.run(cmd)

