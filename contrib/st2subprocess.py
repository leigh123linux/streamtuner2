# encoding: utf-8
# api: streamtuner2
# title: win32/subprocess
# description: Utilizes subprocess spawning or win32 API instead of os.system
# version: 0.5
# depends: streamtuner2 > 2.2.0, python >= 2.7
# priority: optional
# config:
#    { name: cmd_spawn, type: select, select: "popen|shell|call|execv|spawnv|pywin32|win32api|system", value: popen, description: Spawn method }
#    { name: cmd_flags, type: select, select: "none|nowait|detached|nowaito|all|sw_hide|sw_maximize|sw_minimize|sw_show", value: detached, description: Process creation flags (win32) }
#    { name: cmd_quote, type: bool, value: 0, description: Simple quoting override (for Windows) }
#    { name: cmd_split, type: select, select: kxr|shlex|nonposix, value: kxr, description: Command string splitting variant }
# type: handler
# category: io
# license: MITL, CC-BY-SA-3.0
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
#  | win32api.WinExec | w32 | str  | sw_*    | base  | Mostly like `start`? |
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
import pipes
import re
from config import *
from channels import FeaturePlugin
import action

try:
    import win32process
    import win32api
except Exception as e:
    log.ERR("st2subprocess:", e)


# references to original action.* methods
orig_run = action.run
orig_quote = action.quote    


# hook action.run
class st2subprocess (FeaturePlugin):


    # option strings to creationflags
    flagmap = {
        "nowait": os.P_NOWAIT,
        "detached": 0x00000008,  # https://stackoverflow.com/a/13593257/345031
        "nowaito": os.P_NOWAITO,
        "all": 8 | os.P_NOWAIT | os.P_NOWAITO,
        "wait": os.P_WAIT, 
        "none": 0,
        "sw_hide": 0, # https://docs.python.org/2.7/library/subprocess.html#subprocess.STARTUPINFO
        "sw_minimize": 2,  # or 6
        "sw_maximize": 3,
        "sw_show": 5,  # https://msdn.microsoft.com/en-us/library/windows/desktop/ms633548(v=vs.85).aspx
    }


    # swap out action.run()
    def init2(self, parent, *k, **kw):
        action.run = self.run
        if conf.windows or conf.cmd_split:
            action.quote = self.quote

    
    # override for action.quote
    def quote(self, ins):
        # use default for string-style exec methods / or array arg
        if conf.cmd_spawn in ("system", "default", "win32api") or type(ins) is list:
            return orig_quote(ins)
        # only Posix-style shell quoting
        return pipes.quote(ins)
    

    # override for action.run (os.system exec method)
    def run(self, cmd):

        # blacklist
        if re.search("streamripper|cmd\.exe", cmd):
            return orig_run(cmd)

        
        # split args
        if conf.cmd_split in ("kxr", "cmdline_split", "multi"):
            args = self.cmdline_split(cmd, platform=(not conf.windows))
        else:
            args = shlex.split(cmd, posix=(cmd_split=="shlex"))
        # undo win32 quoting damage
        if conf.windows and re.search('\^', cmd): #and action.quote != self.quote:
            args = [re.sub(r'\^(?=[()<>"&^])', '', s) for s in args]
        # flags
        if conf.windows and conf.cmd_flags in self.flagmap:
            flags = self.flagmap[conf.cmd_flags]
        else:
            flags = 0
        # variant
        v = conf.cmd_spawn
        # debug
        log.EXEC("st2subprocess/%s:" % v, args, "creationflags=%s"%flags)

                 
        #-- Popen → https://docs.python.org/2/library/subprocess.html#popen-constructor
        if v in ("popen", "shell"):
            #-- Popen w/ shell=True and string cmd
            if (v=="shell"):
                args = [cmd]
            log.POPEN(
                subprocess.Popen(args, shell=(v=="shell"), creationflags=flags).__dict__
            )
        #-- call → https://docs.python.org/2/library/subprocess.html#replacing-os-system
        elif v == "call":
            log.CALL(
                subprocess.call(args, creationflags=flags)
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
                win32api.WinExec(cmd, flags)  # should only use SW_* flags
            )
        # fallback
        else:
           return orig_run(cmd)


    # shlex.split for Windows
    def cmdline_split(self, s, platform='this'):
        """Multi-platform variant of shlex.split() for command-line splitting.
        For use with subprocess, for argv injection etc. Using fast REGEX.

        platform: 'this' = auto from current platform;
                  1 = POSIX; 
                  0 = Windows/CMD
                  (other values reserved)

        author: kxr / Philip Jenvey
        license: CC-BB-SA-3.0
        src: https://stackoverflow.com/questions/33560364/python-windows-parsing-command-lines-with-shlex
        """
        if platform == 'this':
            platform = (sys.platform != 'win32')
        if platform == 1:
            RE_CMD_LEX = r'''"((?:\\["\\]|[^"])*)"|'([^']*)'|(\\.)|(&&?|\|\|?|\d?\>|[<])|([^\s'"\\&|<>]+)|(\s+)|(.)'''
        elif platform == 0:
            RE_CMD_LEX = r'''"((?:""|\\["\\]|[^"])*)"?()|(\\\\(?=\\*")|\\")|(&&?|\|\|?|\d?>|[<])|([^\s"&|<>]+)|(\s+)|(.)'''
        else:
            raise AssertionError('unkown platform %r' % platform)

        args = []
        accu = None   # collects pieces of one arg
        for qs, qss, esc, pipe, word, white, fail in re.findall(RE_CMD_LEX, s):
            if word:
                pass   # most frequent
            elif esc:
                word = esc[1]
            elif white or pipe:
                if accu is not None:
                    args.append(accu)
                if pipe:
                    args.append(pipe)
                accu = None
                continue
            elif fail:
                raise ValueError("invalid or incomplete shell string")
            elif qs:
                word = qs.replace('\\"', '"').replace('\\\\', '\\')
                if platform == 0:
                    word = word.replace('""', '"')
            else:
                word = qss   # may be even empty; must be last

            accu = (accu or '') + word

        if accu is not None:
            args.append(accu)

        return args

