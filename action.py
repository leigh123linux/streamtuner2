#
# encoding: UTF-8
# api: streamtuner2
# type: functions
# title: play/record actions
# description: Starts audio applications, guesses MIME types for URLs
#
#
#  Multimedia interface for starting audio players or browser.
#
#
#  Each channel plugin has a .listtype which describes the linked
#  audio playlist format. It's audio/x-scpls mostly, seldomly m3u,
#  but sometimes url/direct if the entry[url] directly leads to the
#  streaming server.
#  As fallback there is a regex which just looks for URLs in the
#  given resource (works for m3u/pls/xspf/asx/...). There is no
#  actual url "filename" extension guessing.
#
#
#


import re
import os
import http
from config import conf
import platform


#from channels import __print__
def __print__(*args):
    if conf.debug:
        print(" ".join([str(a) for a in args]))


main = None


#-- media actions                           ---------------------------------------------
#
# implements "play" and "record" methods,
# but also "browser" for web URLs
#        
class action:

        # streamlink formats
        lt = {"asx":"video/x-ms-asf", "pls":"audio/x-scpls", "m3u":"audio/x-mpegurl", "xspf":"application/xspf+xml", "href":"url/http", "ram":"audio/x-pn-realaudio", "smil":"application/smil"}
        # media formats
        mf = {"mp3":"audio/mp3", "ogg":"audio/ogg", "aac":"audio/aac"}


        # web
        @staticmethod
        def browser(url):
            __print__( conf.browser )
            os.system(conf.browser + " '" + action.quote(url) + "' &")
            
        # os shell cmd escaping
        @staticmethod
        def quote(s):
            return "%r" % s


        # calls player for stream url and format
        @staticmethod
        def play(url, audioformat="audio/mp3", listformat="text/x-href"):
            if (url):
                url = action.url(url, listformat)
            if (audioformat):
                if audioformat == "audio/mpeg":
                    audioformat = "audio/mp3"  # internally we use the more user-friendly moniker
                cmd = conf.play.get(audioformat, conf.play.get("*/*", "vlc %u"))
                __print__( "play", url, cmd )
            try:
                action.run( action.interpol(cmd, url) )
            except:
                pass
        
        @staticmethod
        def run(cmd):
            __print__( cmd )
            os.system(cmd + (" &" if platform.system()!="Windows" else "")) 


        # streamripper
        @staticmethod
        def record(url, audioformat="audio/mp3", listformat="text/x-href", append="", row={}):
            __print__( "record", url )
            cmd = conf.record.get(audioformat, conf.record.get("*/*", None))
            try: action.run( action.interpol(cmd, url, row) + append )
            except: pass


        # save as .m3u
        @staticmethod
        def save(row, fn, listformat="audio/x-scpls"):
            # modify stream url
            row["url"] = action.url(row["url"], listformat)
            stream_urls = action.extract_urls(row["url"], listformat)
            # output format
            if (re.search("\.m3u", fn)):
                txt = "#M3U\n"
                for url in stream_urls:
                    txt += http.fix_url(url) + "\n"
            # output format
            elif (re.search("\.pls", fn)):
                txt = "[playlist]\n" + "numberofentries=1\n"
                for i,u in enumerate(stream_urls):
                    i = str(i + 1)
                    txt += "File"+i + "=" + u + "\n"
                    txt += "Title"+i + "=" + row["title"] + "\n"
                    txt += "Length"+i + "=-1\n"
                txt += "Version=2\n"
            # output format
            elif (re.search("\.xspf", fn)):
                txt = '<?xml version="1.0" encoding="UTF-8"?>' + "\n"
                txt += '<?http header="Content-Type: application/xspf+xml" ?>' + "\n"
                txt += '<playlist version="1" xmlns="http://xspf.org/ns/0/">' + "\n"
                for attr,tag in [("title","title"), ("homepage","info"), ("playing","annotation"), ("description","annotation")]:
                    if row.get(attr):
                        txt += "  <"+tag+">" + xmlentities(row[attr]) + "</"+tag+">\n"
                txt += "  <trackList>\n"
                for u in stream_urls:
                    txt += '	<track><location>' + xmlentities(u) + '</location></track>' + "\n"
                txt += "  </trackList>\n</playlist>\n"
            # output format
            elif (re.search("\.json", fn)):
                row["stream_urls"] = stream_urls
                txt = str(row)   # pseudo-json (python format)
            # output format
            elif (re.search("\.asx", fn)):
                txt = "<ASX version=\"3.0\">\n"			\
                    + " <Title>" + xmlentities(row["title"]) + "</Title>\n"	\
                    + " <Entry>\n"				\
                    + "  <Title>" + xmlentities(row["title"]) + "</Title>\n"	\
                    + "  <MoreInfo href=\"" + row["homepage"] + "\"/>\n"	\
                    + "  <Ref href=\"" + stream_urls[0] + "\"/>\n"		\
                    + " </Entry>\n</ASX>\n"
            # output format
            elif (re.search("\.smil", fn)):
                txt = "<smil>\n<head>\n  <meta name=\"title\" content=\"" + xmlentities(row["title"]) + "\"/>\n</head>\n"	\
                    + "<body>\n  <seq>\n    <audio src=\"" + stream_urls[0] + "\"/>\n  </seq>\n</body>\n</smil>\n"
            # unknown
            else:
                txt = ""
            # write
            if txt:
                f = open(fn, "wb")
                f.write(txt)
                f.close()
            pass


        # replaces instances of %u, %l, %pls with urls / %g, %f, %s, %m, %m3u or local filenames
        @staticmethod
        def interpol(cmd, url, row={}):
            # inject other meta fields
            if row:
                for field in row:
                    cmd = cmd.replace("%"+field, "%r" % row.get(field))
            # add default if cmd has no %url placeholder
            if cmd.find("%") < 0:
                cmd = cmd + " %m3u"
            # standard placeholders
            if (re.search("%(url|pls|[ulr])", cmd)):
                cmd = re.sub("%(url|pls|[ulr])", action.quote(url), cmd)
            if (re.search("%(m3u|[fgm])", cmd)):
                cmd = re.sub("%(m3u|[fgm])", action.quote(action.m3u(url)), cmd)
            if (re.search("%(srv|[ds])", cmd)):
                cmd = re.sub("%(srv|[ds])", action.quote(action.srv(url)), cmd)
            return cmd


        # eventually transforms internal URN/IRI to URL
        @staticmethod
        def url(url, listformat):
            if (listformat == "audio/x-scpls"):
                url = url
            elif (listformat == "text/x-urn-streamtuner2-script"):
                url = main.special.stream_url(url)
            else:
                url = url
            return url

            
        # download a .pls resource and extract urls
        @staticmethod
        def pls(url):
            text = http.get(url)
            __print__( "pls_text=", text )
            return re.findall("\s*File\d*\s*=\s*(\w+://[^\s]+)", text, re.I)
            # currently misses out on the titles            
            
        # get a single direct ICY stream url (extract either from PLS or M3U)
        @staticmethod
        def srv(url):
            return action.extract_urls(url)[0]


        # retrieve real stream urls from .pls or .m3u links
        @staticmethod
        def extract_urls(pls, listformat="__not_used_yet__"):
            # extract stream address from .pls URL
            if (re.search("\.pls", pls)):       #audio/x-scpls
                return action.pls(pls)
            elif (re.search("\.asx", pls)):	#video/x-ms-asf
                return re.findall("<Ref\s+href=\"(http://.+?)\"", http.get(pls))
            elif (re.search("\.m3u|\.ram|\.smil", pls)):	#audio/x-mpegurl
                return re.findall("(http://[^\s]+)", http.get(pls), re.I)
            else:  # just assume it was a direct mp3/ogg streamserver link
                return [ (pls if pls.startswith("/") else http.fix_url(pls)) ]
            pass


        # generate filename for temporary .m3u, if possible with unique id
        @staticmethod
        def tmp_fn(pls):
            # use shoutcast unique stream id if available
            stream_id = re.search("http://.+?/.*?(\d+)", pls, re.M)
            stream_id = stream_id and stream_id.group(1) or "XXXXXX"
            try:
                channelname = main.current_channel
            except:
                channelname = "unknown"
            return (conf.tmp+"/streamtuner2."+channelname+"."+stream_id+".m3u", len(stream_id) > 3 and stream_id != "XXXXXX")
            
        # check if there are any urls in a given file
        @staticmethod
        def has_urls(tmp_fn):
            if os.path.exists(tmp_fn):
                return open(tmp_fn, "r").read().find("http://") > 0
            
        
        # create a local .m3u file from it
        @staticmethod
        def m3u(pls):
        
            # temp filename
            (tmp_fn, unique) = action.tmp_fn(pls)
            # does it already exist?
            if tmp_fn and unique and conf.reuse_m3u and action.has_urls(tmp_fn):
                return tmp_fn

            # download PLS
            __print__( "pls=",pls )
            url_list = action.extract_urls(pls)
            __print__( "urls=", url_list )

            # output URL list to temporary .m3u file
            if (len(url_list)):
                #tmp_fn = 
                f = open(tmp_fn, "w")
                f.write("#M3U\n")
                f.write("\n".join(url_list) + "\n")
                f.close()
                # return path/name of temporary file
                return tmp_fn
            else:
                __print__( "error, there were no URLs in ", pls )
                raise "Empty PLS"

        # open help browser                
        @staticmethod
        def help(*args):
        
            os.system("yelp /usr/share/doc/streamtuner2/help/ &")
            #or action.browser("/usr/share/doc/streamtuner2/")

#class action


