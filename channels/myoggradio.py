
# api: streamtuner2
# title: MyOggRadio
# description: Open source internet radio directory.
# type: channel
# category: radio
# version: 0.7
# url: http://www.myoggradio.org/
# depends: json, ahttp >= 1.5
# config:
#    { name: myoggradio_login,  type: text,  value: "user:password", description: "Account for storing personal favourites." }
#    { name: myoggradio_morph,  type: boolean, value: 0,  description: "Convert pls/m3u into direct shoutcast url." }
# priority: standard
# png:
#   iVBORw0KGgoAAAANSUhEUgAAAAsAAAAQCAYAAADAvYV+AAAABHNCSVQICAgIfAhkiAAAARdJREFUKJGt0U8rhFEUx/HP3AfjT9QQJo80CyzGG1A2UspL8k4s
#   7G2lvAlLC0skEWliMJTHM2Nx72iSjfJb3Xv6/n7ndA5/UIWz/jtDGZ9rqXQGAT30+vAE6njA80DYCObQxe1QTFdPhlFc4D0lzmMGn3gJGEtQhipFg80a53Uq
#   syksoBYiIMRiNeMw5+GA3S0m+50rqIY0T1LZY6kga5N34v9b3ZDmK6Op7JI/Eu6ZvqMsEthDJ+ADTxEeLth/o5jheIjJdgr6QCsk531cWeOWo0W06KwycYcX
#   3KAI6QAlzSvWX/ncwDWaTNVoXiaDyo+LbmMHp2jEDvb6S8gGwBVs4SRBN1jAOC5/hMrF0w5qHMu/TPDP+gI3M01h2io9UwAAAABJRU5ErkJggg==
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
from config import *
import action
from uikit import uikit
import ahttp

import re
import json
import copy
from uikit import gtk


# open source radio sharing stie
class myoggradio(ChannelPlugin):

    # control flags
    listformat = "pls,m3u,srv"
    has_search = False
    api = "http://www.myoggradio.org/"
    
    # hide unused columns
    titles = dict(playing=False, listeners=False, bitrate=False)
    
    # category map
    categories = ['common', 'personal']
    
    
    
    # prepare GUI
    def init2(self, parent):
        if parent:
            #uikit.add_menu([parent.extensions, parent.extensions_context], "Share in MyOggRadio", self.share)
            uikit.add_menu([parent.streammenu, parent.streamactions], "Share in MyOggRadio", self.share, insert=4)



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
            data = ahttp.get(self.api + "common.json", encoding="utf-8")
            entries = json.loads(data)
            
        # bookmarks
        elif (cat == "personal") and self.user_pw():
            data = ahttp.get(self.api + "favoriten.json?user=" + self.user_pw()[0], encoding="utf-8")
            entries = json.loads(data)
        
        # unknown
        else:
            self.parent.status("Unknown category")
            pass

        # augment result list
        for i,e in enumerate(entries):
            entries[i]["homepage"] = self.api + "c_common_details.jsp?url="  + e["url"]
            entries[i]["genre"] = cat
            entries[i]["format"] = "audio/mpeg"
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
                
                urls = action.convert_playlist(row["url"], row.get("listformat", "any"), "srv", local_file=False, row=row)
                if not urls:
                    urls = [row["url"]]
                row["url"] = ahttp.fix_url(urls[0])
                
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
                ahttp.get(self.api + "c_neu.jsp", params=submit, ajax=1, post=1)

            # use JSON interface
            else:
                ahttp.get(self.api + "commonadd.json", params=submit, ajax=1)
    
            
    # authenticate against MyOggRadio
    def login(self):
        login = self.user_pw()    
        if login:
            data = dict(zip(["benutzer", "passwort"], login))
            ahttp.get(self.api + "c_login.jsp", params=data, ajax=1)
            # let's hope the JSESSIONID cookie is kept


    # returns login (user,pw)
    def user_pw(self):
        if len(conf.myoggradio_login) and conf.myoggradio_login != "user:password":
            return conf.myoggradio_login.split(":")
        else:
            lap =  conf.netrc(["myoggradio", "myoggradio.org", "www.myoggradio.org"])
            if lap:
                return [lap[0] or lap[1], lap[2]]
            else:
                self.parent.status("No login data for MyOggRadio configured. See F12 for setup, or F1 for help.");
        pass        



