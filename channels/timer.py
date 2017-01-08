# encoding: utf-8
# api: streamtuner2
# title: Recording timer
# description: Schedules play/record events for bookmarked radio stations.
# type: feature
# category: hook
# depends: kronos, action >= 1.1.1
# version: 0.7.8
# config: 
#   { name: timer_duration, type: select, select: "auto|streamripper|fpls", value: none, description: "Support for time ranges" }
#   { name: timer_crontab, type: bool, value: 0, description: "Utilize cron instead of runtime scheduler. (not implemented yet)" }
# priority: optional
# support: basic
#
# Provides an internal timer, to configure recording and playback times/intervals
# for stations. It accepts a natural language time string when registering a stream.
#
# Context menu > Add timer for station
#
# Programmed events are visible in "timer" under the "bookmarks" channel. Times
# are stored in the description field, and can thus be edited. However, after editing
# times manually, streamtuner2 must be restarted for any changes to take effect.
#
# Allowable time specifications are "Mon,Wed,Fri 18:00-20:00 record"
# or even "Any 7:00-12:00 play". The duration is only honored for
# recording via streamripper or fIcy/fPls currently.
#


from config import *
from channels import *
import bundle.kronos as kronos  # unmaintend pkg, but py3-compatibilized version distributed within bundle/
from uikit import uikit
import action
import copy
import re



# timed events (play/record) within bookmarks tab
class timer (FeaturePlugin):

    # configuration settings
    timefield = "playing"
    
    # kronos scheduler list
    sched = None
    
    
    # prepare gui
    def init2(self, parent):
          
        # bookmarks channel shortcut
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

        #-- crontab mode?
        # if "timer_crontab" in conf and conf.timer_crontab:
        #     pass
        # elif "timer_crontab_dequeue" in conf:
        #     pass
        
        #-- prepare scheduler
        self.sched = kronos.ThreadedScheduler()
        for row in self.streams:
            try: self.queue(row)
            except Exception as e: log.ERR("queuing error", e)
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
        timespec = self.parent.timer_value.get_text()

        # basic check for consistency
        if not re.match("^(\w{2,3}|[*,;+])+\s+(\d+:\d+)\s*((\.\.+|-+)\s*(\d+:\d+))?\s+(record|play)", timespec):
            self.warn('Danger, Will Robinson! → The given timer date/action is likely invalid.', timeout=22)

        # hide dialog
        self.parent.timer_dialog.hide()
        row = self.parent.row()
        row = copy.copy(row)

        # add data
        row["listformat"] = "href" #self.parent.channel().listformat
        if row.get(self.timefield):
            row["title"] = row["title"] + " -- " + row[self.timefield]
        row[self.timefield] = timespec

        # store
        if self.save_timer(row):
            self.status("Timer saved.")
    
    
    # store row in timer database
    def save_timer(self, row):
        self.streams.append(row)
        self.bookmarks.save()
        return self.queue(row)
        
        
    # Add timer/recording events to scheduler (or later crontab)
    def queue(self, row):
    
        # chk
        if not row.get(self.timefield) or not row.get("url"):
            return log.DATA("NO TIME DATA", row)
    
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
        if days and time and activity:
            task = self.sched.add_daytime_task(action_method, activity, days, None, time, kronos.method.threaded, [row], {})
            log.QUEUE( activity, self.sched, (action_method, activity, days, None, time, kronos.method.threaded, [row], {}), task.get_schedule_time(True) )
            return True
        else:
            log.ERR_QUEUE( activity, self.sched, (action_method, activity, days, None, time, kronos.method.threaded, [row], {}) )
    
    
    
    # converts Mon,Tue,... into numeric 1-7
    def days(self, s):
        weekdays = ["su", "mo", "tu", "we", "th", "fr", "sa", "su"]
        r = []
        if re.search("any|all|\*", s, re.I):
            return range(0,7)
        for day in re.findall("\w\w+", s.lower()):
            day = day[0:2]
            if day in weekdays:
                r.append(weekdays.index(day))
        return list(set(r))
        
    # get start time 18:00
    def time(self, s):
        r = re.search("(\d+):(\d+)", s)
        if r:
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
            row = row,
            audioformat = row.get("format","audio/mpeg"), 
            source = row.get("listformat","href")
        )

    # kronos/sched callback: action wrapper
    def record(self, row, *args, **kwargs):
        log.TIMER("TIMED RECORD", *args)
        
        # extra params
        # make streamripper record a timed broadcast
        duration = self.duration(row.get(self.timefield))
        append = None
        if duration:
            _rec = conf.record.get("audio/*", "")
            if re.search("streamripper", _rec):
                append = "-a %S.%d.%q -l " + str(duration*60) # seconds
            if re.search("fPls|fIcy", _rec, re.I):
                append = "-M " + str(duration) # minutes

        # start recording
        action.record(
            row = row,
            audioformat = row.get("format","audio/mpeg"), 
            source = row.get("listformat","href"),
            append = append,
        )
    
    # kronos/sched callback for testing
    def test(self, row, *args, **kwargs):
        log.TEST("KRONOS", row)


    # crontab handlers
    def cron_queue(self, row):
        pass

    # crontab cleanup
    """
        All streamtuner2 events will be preceded with a `# streamtuner2: …` comment
    """
    def cron_dequeue_all(self):
        pass
    