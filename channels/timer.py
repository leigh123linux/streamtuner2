#
# api: streamtuner2
# title: Recording timer
# description: Schedules play/record events for bookmarked radio stations.
# type: feature
# category: hook
# depends: kronos
# version: 0.6
# config: -
# priority: optional
# support: unsupported
#
# Provides an internal timer, to configure recording and playback times/intervals
# for stations. It accepts a natural language time string when registering a stream.
#
# Context menu > Extension > Add timer
#
# Programmed events are visible in "timer" under the "bookmarks" channel. Times
# are stored in the description field, and can thus be edited. However, after editing
# times manually, streamtuner2 must be restarted for any changes to take effect.
#


from config import *
from channels import *
import bundle.kronos as kronos  # Doesn't work with Python3
from uikit import uikit
import action
import copy
import re



# timed events (play/record) within bookmarks tab
class timer:

    # plugin info
    module = "timer"
    title = "Timer"
    meta = plugin_meta()
    
    # configuration settings
    timefield = "playing"
    
    # kronos scheduler list
    sched = None
    
    
    
    # prepare gui
    def __init__(self, parent):
        if not parent:
            return
          
        # keep reference to main window
        self.parent = parent
        self.bookmarks = parent.bookmarks
        
        # add menu
        uikit.add_menu([parent.streammenu, parent.streamactions], "Add timer for station", self.edit_timer, insert=4)
        
        # target channel
        if not self.bookmarks.streams.get("timer"):
            self.bookmarks.streams["timer"] = [{"title":"--- timer events ---"}]
        self.bookmarks.add_category("timer")
        self.streams = self.bookmarks.streams["timer"]
        
        # widgets
        uikit.add_signals(parent, {
            ("timer_ok", "clicked"): self.add_timer,
            ("timer_cancel", "clicked"): self.hide,
            ("timer_dialog", "close"): self.hide,
            ("timer_dialog", "delete-event"): self.hide,
        })
        
        # prepare spool
        self.sched = kronos.ThreadedScheduler()
        for row in self.streams:
            try: self.queue(row)
            except Exception as e: __print__(dbg.ERR, "queuing error", e)
        self.sched.start()


    # display GUI for setting timespec
    def edit_timer(self, *w):
        self.parent.timer_dialog.show()
        self.parent.timer_value.set_text("Fri,Sat 20:00-21:00 play")

    # done        
    def hide(self, *w):
        return self.parent.timer_dialog.hide()

    # close dialog,get data
    def add_timer(self, *w):
        self.parent.timer_dialog.hide()
        row = self.parent.row()
        row = copy.copy(row)
        
        # add data
        row["listformat"] = "href" #self.parent.channel().listformat
        if row.get(self.timefield):
            row["title"] = row["title"] + " -- " + row[self.timefield]
        row[self.timefield] = self.parent.timer_value.get_text()
        
        # store
        self.save_timer(row)
    
    
    # store row in timer database
    def save_timer(self, row):
        self.streams.append(row)
        self.bookmarks.save()
        self.queue(row)
        pass
        
        
    # add event to list
    def queue(self, row):
    
        # chk
        if not row.get(self.timefield) or not row.get("url"):
            #print("NO TIME DATA", row)
            return
    
        # extract timing parameters
        _ = row[self.timefield]
        days = self.days(_)
        time = self.time(_)
        duration = self.duration(_)
        
        # which action
        if row[self.timefield].find("rec")>=0:
            activity, action_method = "record", self.record
        else:
            activity, action_method = "play", self.play
        
        # add
        task = self.sched.add_daytime_task(action_method, activity, days, None, time, kronos.method.threaded, [row], {})

        #__print__( "queue",  act, self.sched, (action_method, act, days, None, time, kronos.method.threaded, [row], {}), task.get_schedule_time(True) )
    
    
    
    # converts Mon,Tue,... into numberics 1-7
    def days(self, s):
        weekdays = ["su", "mo", "tu", "we", "th", "fr", "sa", "su"]
        r = []
        for day in re.findall("\w\w+", s.lower()):
            day = day[0:2]
            if day in weekdays:
                r.append(weekdays.index(day))
        return list(set(r))
        
    # get start time 18:00
    def time(self, s):
        r = re.search("(\d+):(\d+)", s)
        return int(r.group(1)), int(r.group(2))
        
    # convert "18:00-19:15" to minutes
    def duration(self, s):
        try:
            r = re.search("(\d+:\d+)\s*(\.\.+|-+)\s*(\d+:\d+)", s)
            start = self.time(r.group(1))
            end = self.time(r.group(3))
            duration = (end[0] - start[0]) * 60 + (end[1] - start[1])
            return int(duration) # in minutes
        except:
            return 0   # no limit
        
    # action wrapper
    def play(self, row, *args, **kwargs):
        action.play(
            url = row["url"],
            audioformat = row.get("format","audio/mpeg"), 
            listformat = row.get("listformat","href"),
        )

    # action wrapper
    def record(self, row, *args, **kwargs):
        #print("TIMED RECORD")
        
        # extra params
        duration = self.duration(row.get(self.timefield))
        if duration:
            append = " -a %S.%d.%q -l "+str(duration*60)   # make streamripper record a whole broadcast
        else:
            append = ""

        # start recording
        action.record(
            url = row["url"],
            audioformat = row.get("format","audio/mpeg"), 
            listformat = row.get("listformat","href"),
            append = append,
        )
    
    def test(self, row, *args, **kwargs):
        print("TEST KRONOS", row)


