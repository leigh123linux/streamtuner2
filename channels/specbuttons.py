# encoding: utf-8
# title: Extra buttons for apps
# description: Adds configurable mini toolbar buttons
# version: 0.5
# depends: streamtuner2 >= 2.2.0
# type: feature
# category: ui
# config:
#    { name: specbutton_rows, value: 2, type: int, description: "Number of rows to arrange buttons in (default 2, looks ok with up to 3 rows)" }
#
# Shows the mini extra buttons in the toolbar, which allow to control your
# audio player or run other system commands. The configuration list is in
# the Settings → Options tab.
#
# Icons can either be gtk-xyz icon names, or load /usr/share/icon/*.png
# pixmaps.


import os.path
import subprocess
import math
import re
from config import conf, log
import action
from uikit import gtk


# Channel Homepage in Toolbar
class specbuttons(object):
    module = __name__

    # Hook toolbar label
    def __init__(self, parent):
        self.parent = parent
        self.specbuttons = parent.get_widget("specbuttons")
        parent.hooks["init"].append(self.update_buttons)
        parent.hooks["config_save"].append(self.update_paths)
        parent.specbuttons.show()
        parent.tv_config_specbuttons.show()

    # Extra buttons
    def update_buttons(self, parent):
    
        # define table width (2 rows default)
        y = min(int(conf.specbutton_rows), 4)
        self.specbuttons.resize(y, int(math.ceil(len(conf.specbuttons) / y)))
        # clean up
        for widget in self.specbuttons.get_children():
            widget.destroy()
        xy = 0
        
        # add icon buttons
        for btn, cmd in conf.specbuttons.items():
            #log.IN(btn, cmd)
            w_btn = gtk.Button()
            w_btn.set_image(self.icon(btn))
            w_btn.connect("clicked", lambda x0, cmd=cmd, *x: action.run(cmd) )
            self.specbuttons.attach(
                w_btn,
                int(xy / y), int(xy / y) + 1, xy % y, (xy % y) + 1,
                gtk.EXPAND, gtk.EXPAND, 1, 1
            )
            xy = xy + 1
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

    # Look for image basename "play" in /usr/share/icons/*.*
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

