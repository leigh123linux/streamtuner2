# encoding: utf-8
# api: streamtuner2
# title: win32/subprocess
# description: Utilizes subprocess spawning or win32 API instead of os.system
# version: 0.2
# depends: streamtuner2 > 2.2.0, python >= 2.7
# priority: optional
# config:
#    { name: cmd_spawn, type: select, select: "popen|call|execv|spawnv|pywin32|win32api|system", value: popen, description: Spawn method }
#    { name: cmd_flags, type: select, select: "none|nowait|detached|nowait0|all|sw_show", value: none, description: Process creation flags (win32) }
# type: handler
# category: io
#
# Overrides the action.run method with subprocess.Popen() and some
# cmdline parsing. Which mostly makes sense on Windows to avoid some
# `start` bugs, such as "http://.." arguments getting interpreted
# independently.
#
#  +------------------+-----+---------+-------+----------------------+
#  | VARIANT          | SYS | FLAGS   | PATHS | NOTES                |
#  +------------------+-----+---------+-------+----------------------+
#  | subprocess.popen |  *  | all     | base  | Most versatile       |
#  | subprocess.call  |  *  | all     | base& | May block Gtk thread |
#  | os.execv         | w32 | none    | full& | fork+exec            |
#  | os.spawnv        | lnx | nowait  | full& | ?                    |
#  | w32proc.CreatePr | w32 | detachd | full  | Few parameters used  |
#  | win32api.WinExec | w32 | sw_show | base  | Mostly like `start`? |
#  | system/default   |  *  | none    | base  | normal action.run()  |
#  +------------------+-----+---------+-------+----------------------+
#
# Notes:
#  · Note that for Linux, you should decorate player commands with "&" and
#    use absolute paths for call/exec/spawn to work as expected.
#  · The flags are only supported on Windows, should be `none` for Linux.
#  · streamripper calls will always use the default action.run/os.system
#  · cmdline parsing may not reproduce the original arguments on Windows,
#    in particular if list2cmdline was used.
#  · Does not yet check for modules being load
#  · Testing mostly. Though might replace action.run someday. Command and
#    argument parsing is the holdup for not having this earlier.
#


import re
import os
import shlex
from config import *
from channels import FeaturePlugin
import action

try:
    import subprocess
except:
    None

try:
    import win32process
except:
    None

try:
    import win32api
except:
    None


# hook action.run
class st2subprocess (FeaturePlugin):

    # alternative run methods
    flagmap = {
        "nowait": os.P_NOWAIT,
        "detached": 0x00000008,  # https://stackoverflow.com/a/13593257/345031
        "nowait0": os.P_NOWAITO,
        "all": 8 | os.P_NOWAIT | os.P_NOWAITO,
        "wait": os.P_WAIT, 
        "none": 0, # https://docs.python.org/2.7/library/subprocess.html#subprocess.STARTUPINFO
        "sw_show": 5,  # https://msdn.microsoft.com/en-us/library/windows/desktop/ms633548(v=vs.85).aspx
    }


    # swap out action.run()
    def init2(self, parent, *k, **kw):
        self.osrun = action.run
        action.run = self.action_run
        

    # override for exec method
    def action_run(self, cmd):

        # blacklist
        if re.search("streamripper|cmd\.exe", cmd):
            return self.osrun(cmd)
        
        # split args
        args = shlex.split(cmd)
        # undo win32 quoting damage
        if conf.windows and re.search('\^', cmd):
            args = [re.sub(r'\^(?=[()<>"&^])', '', s) for s in args]
        # flags
        flags = self.flagmap[conf.cmd_flags] if conf.windows and conf.cmd_flags in self.flagmap else 0
        # debug
        log.EXEC("st2subprocess:", args, "creationflags=%s"%flags)
                 
        #-- Popen → https://docs.python.org/2/library/subprocess.html#popen-constructor
        if conf.cmd_spawn == "popen":
            log.POPEN(
                subprocess.Popen(args, creationflags=flags)
            )
        #-- call → https://docs.python.org/2/library/subprocess.html#replacing-os-system
        elif conf.cmd_spawn == "call":
            log.CALL(
                subprocess.call(args, creationflags=flags)
            )
        #-- execv → https://docs.python.org/2/library/os.html#os.execv
        elif conf.cmd_spawn == "execv":
            log.OS_EXECV(
                os.execv(args[0], args) if os.fork() == 0 else "..."
            )
        #-- spawnv → https://docs.python.org/2/library/os.html#os.spawnv
        elif conf.cmd_spawn == "spawnv":
            log.OS_SPAWNL(
                os.spawnv(flags, args[0], args)
            )
        #-- pywin32 → https://www.programcreek.com/python/example/8489/win32process.CreateProcess
        elif conf.cmd_spawn == "pywin32":
            log.WIN32PROCESS_CreateProcess(
                win32process.CreateProcess(
                    None, cmd, None, None, 0, flags,
                    None, None, win32process.STARTUPINFO()
                )
            )
        #-- win32api
        elif conf.cmd_spawn == "win32api":
            log.WIN32API_WinExec(
                win32api.WinExec(cmd, win32con.SW_SHOW)
            )
            
        # fallback
        else:
           return self.osrun(cmd)



