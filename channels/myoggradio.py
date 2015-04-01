#
# api: streamtuner2
# title: MyOggRadio
# description: Open source internet radio directory.
# type: channel
# category: radio
# version: 0.6
# url: http://www.myoggradio.org/
# depends: json, StringIO
# config:
#    { name: myoggradio_login,  type: text,  value: "user:password", description: "Account for storing personal favourites." }
#    { name: myoggradio_morph,  type: boolean, value: 0,  description: "Convert pls/m3u into direct shoutcast url." }
# priority: standard
#
# MyOggRadio is an open source radio station directory. Because this matches
# well with streamtuner2, there's now a project partnership. Shared streams can easily
# be downloaded in this channel plugin. And streamtuner2 users can easily share their
# favourite stations into the MyOggRadio directory.
#
# Beforehand an account needs to be configured in the settings. (Registration
# on myoggradio doesn't require an email address or personal information.)
#



from channels import *
from config import conf
from action import action
from uikit import uikit
import ahttp as http

import re
import json
from compat2and3 import StringIO
import copy



# open source radio sharing stie
class myoggradio(ChannelPlugin):

    # settings
    title ="MOR"
    #module = "myoggradio"
    api = "http://www.myoggradio.org/"
    listformat = "url/direct"
    
    # hide unused columns
    titles = dict(playing=False, listeners=False, bitrate=False)
    
    # category map
    categories = ['common', 'personal']
    default = 'common'
    current = 'common'
    
    # netrc instance
    netrc = None
    
    
    
    # prepare GUI
    def __init__(self, parent):
        ChannelPlugin.__init__(self, parent)
        if parent:
            uikit.add_menu([parent.extensions, parent.extensions_context], "Share in MyOggRadio", self.share)



    # this is simple, there are no categories
    def update_categories(self):
        pass



    # download links from dmoz listing
    def update_streams(self, cat):

        # result list
        entries = []
        
        # common
        if (cat == "common"):
            # fetch
            data = http.get(self.api + "common.json")
            entries = json.load(StringIO(data))
            
        # bookmarks
        elif (cat == "personal") and self.user_pw():
            data = http.get(self.api + "favoriten.json?user=" + self.user_pw()[0])
            entries = json.load(StringIO(data))
        
        # unknown
        else:
            self.parent.status("Unknown category")
            pass

        # augment result list
        for i,e in enumerate(entries):
            entries[i]["homepage"] = self.api + "c_common_details.jsp?url="  + e["url"]
            entries[i]["genre"] = cat
        # send back
        return entries
        
        
    
    # upload a single station entry to MyOggRadio
    def share(self, *w):
    
        # get data
        row = self.parent.row()
        if row:
            row = copy.copy(row)
            
            # convert PLS/M3U link to direct ICY stream url
            if conf.myoggradio_morph and self.parent.channel().listformat != "url/direct":
                row["url"] = http.fix_url(action.srv(row["url"]))
                
            # prevent double check-ins
            if row["title"] in (r.get("title") for r in self.streams["common"]):
                pass
            elif row["url"] in (r.get("url") for r in self.streams["common"]):
                pass

            # send
            else:
                self.parent.status("Sharing station URL...")
                self.upload(row)
                sleep(0.5) # artificial slowdown, else user will assume it didn't work
            
        # tell Gtk we've handled the situation
        self.parent.status("Shared '" + row["title"][:30] + "' on MyOggRadio.org")
        return True


    # upload bookmarks
    def send_bookmarks(self, entries=[]):
    
        for e in (entries if entries else parent.bookmarks.streams["favourite"]):
            self.upload(e)
        

    # send row to MyOggRadio
    def upload(self, e, form=0):
        if e:
            login = self.user_pw()
            submit = {
                "user": login[0],    	  # api
                "passwort": login[1], 	  # api
                "url": e["url"],
                "bemerkung": e["title"],
                "genre": e["genre"],
                "typ": e["format"][6:],
                "eintragen": "eintragen", # form
            }

            # just push data in, like the form does
            if form:
                self.login()
                http.get(self.api + "c_neu.jsp", params=submit, ajax=1, post=1)

            # use JSON interface
            else:
                http.get(self.api + "commonadd.json", params=submit, ajax=1)
    
            
    # authenticate against MyOggRadio
    def login(self):
        login = self.user_pw()    
        if login:
            data = dict(zip(["benutzer", "passwort"], login))
            http.get(self.api + "c_login.jsp", params=data, ajax=1)
            # let's hope the JSESSIONID cookie is kept


    # returns login (user,pw)
    def user_pw(self):
        if len(conf.myoggradio_login) and conf.myoggradio_login != "user:password":
            return conf.myoggradio_login.split(":")
        else:
            lap =  conf.netrc(["myoggradio", "myoggradio.org", "www.myoggradio.org"])
            if lap:
                return [lap[0] or lap[1], lap[2]]
        pass        




