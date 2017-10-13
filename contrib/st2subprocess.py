# encoding: utf-8
# api: streamtuner2
# title: win32/subprocess
# description: Utilizes subprocess spawning or win32 API instead of os.system
# version: 0.3
# depends: streamtuner2 > 2.2.0, python >= 2.7
# priority: optional
# config:
#    { name: cmd_spawn, type: select, select: "popen|shell|call|execv|spawnv|pywin32|win32api|system", value: popen, description: Spawn method }
#    { name: cmd_flags, type: select, select: "none|nowait|detached|nowaito|all|sw_hide||sw_minimize|sw_show", value: nowait, description: Process creation flags (win32) }
# type: handler
# category: io
#
# Overrides the action.run method with subprocess.Popen() and a bit
# cmdline parsing. Which mostly makes sense on Windows to avoid some
# `start` bugs, such as "http://.." arguments getting misinterpreted.
# Also works on Linux, though with few advantages and some gotchas.
#
#  +------------------+-----+------+---------+-------+----------------------+
#  | VARIANT          | SYS | ARGS | FLAGS   | PATHS | NOTES                |
#  +------------------+-----+------+---------+-------+----------------------+
#  | subprocess.popen |  *  | []   | all     | base  | Most compatible      |
#  | subprocess.shell | lnx | str  | all     | base  | Linux only?          |
#  | subprocess.call  |  *  | []   | all     | base& | May block Gtk thread |
#  | os.execv         | w32 | s/[] | -       | full& | fork+exec            |
#  | os.spawnv        | lnx | s/[] | nowait  | full& | ?                    |
#  | pywin32.CreatePr | w32 | str  | detached| full  | Few parameters used  |
#  | win32api.WinExec | w32 | str  | sw_show | base  | Mostly like `start`? |
#  | system/default   |  *  | str  | -       | base  | normal action.run()  |
#  +------------------+-----+------+---------+-------+----------------------+
#
# · The flags are only supported on Windows. The FLAGS column just lists
#   recommended defaults. Will implicitly be `none` for Linux.
# · Note that for Linux, you should decorate player commands with "&" and
#   use absolute paths for call/exec/spawn to work as expected.
# · streamripper calls will always use the default action.run/os.system
# · cmdline parsing may not reproduce the original arguments on Windows,
#   in particular if list2cmdline was used.
# · Does not yet check for modules being load
# · Testing mostly. Though might replace action.run someday. Command and
#   argument parsing is the holdup for not having this earlier.
# · Unlike action.run() none of the methods does interpret shell variables
#   or features obviously. Unless you wrap player commands with `sh -c …`
#


import subprocess
import os
import shlex
import re
from config import *
from channels import FeaturePlugin
import action

try:
    import win32process
    import win32api
except Exception as e:
    log.ERR("pywin32/win32api not available", e)


# hook action.run
class st2subprocess (FeaturePlugin):

    # option strings to creationflags
    flagmap = {
        "nowait": os.P_NOWAIT,
        "detached": 0x00000008,  # https://stackoverflow.com/a/13593257/345031
        "nowait0": os.P_NOWAITO,
        "all": 8 | os.P_NOWAIT | os.P_NOWAITO,
        "wait": os.P_WAIT, 
        "none": 0,
        "sw_hide": 0, # https://docs.python.org/2.7/library/subprocess.html#subprocess.STARTUPINFO
        "sw_minimize": 2,  # or 6
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
        v = conf.cmd_spawn
        if v in ("popen"):
            log.POPEN(
                subprocess.Popen(args, shell=(v=="shell"), creationflags=flags).__dict__
            )
        #-- Popen w/ shell=True and string cmd
        v = conf.cmd_spawn
        if v in ("popen", "shell"):
            log.POPEN_SHELL(
                subprocess.Popen(cmd, shell=(v=="shell"), creationflags=flags).__dict__
            )
        #-- call → https://docs.python.org/2/library/subprocess.html#replacing-os-system
        elif v == "call":
            log.CALL(
                subprocess.call(args, creationflags=flags).__dict__
            )
        #-- execv → https://docs.python.org/2/library/os.html#os.execv
        elif v == "execv":
            log.OS_EXECV(
                os.execv(args[0], args) if os.fork() == 0 else "..."
            )
        #-- spawnv → https://docs.python.org/2/library/os.html#os.spawnv
        elif v == "spawnv":
            log.OS_SPAWNV(
                os.spawnv(flags, args[0], args)
            )
        #-- pywin32 → https://www.programcreek.com/python/example/8489/win32process.CreateProcess
        elif v == "pywin32":
            log.WIN32PROCESS_CreateProcess(
                win32process.CreateProcess(
                    None, cmd, None, None, 0, flags,
                    None, None, win32process.STARTUPINFO()
                )
            )
        #-- win32api
        elif conf.cmd_spawn == "win32api":
            log.WIN32API_WinExec(
                win32api.WinExec(cmd, flags)
            )
            
        # fallback
        else:
           return self.osrun(cmd)



