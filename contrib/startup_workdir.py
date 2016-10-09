# encoding: utf-8
# title: Working directory
# description: Changes to another directory on startup
# version: 0.1
# priority: rare
# depends: streamtuner2 >= 2.1.5
# type: feature
# category: session
# config:
#   { name: start_dir, value: /home/$USER/Music, type: string, decription: Switch to this directory. }
#
# Can be used to predefine an alternative start directory,
# which also influences where streamrippers downloads to.
#
# This is somewhat redundant, as you can specify the working
# directory in your Desktop starter already; or set the path
# for streamripper with a parameter.

from config import conf
import os, os.path

# Stop button
class startup_workdir(object):
    module = __name__

    # button + hook
    def __init__(self, parent):
        os.chdir(
            os.path.expandvars(
                os.path.expanduser(
                    conf.start_dir
                )
            )
        )

