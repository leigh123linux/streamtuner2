# encoding: UTF-8
# api: streamtuner2
# title: User Agent Switcher
# description: Mask streamtuner2 as browser or different radio player.
# version: 0.2
# type: feature
# category: session
# priority: rare
# config:
#   { type=select, name=useragent, value=Streamtuner2, select="Streamtuner2|VLC|Firefox|Chrome|Android|MSIE|iTunes|WinAmp|NSPlayer", description=Which browser string to use for HTTP requests. }
# hooks: config_save
#
# This is currently unneeded / only for privacy.
# Allows to masquerade streamtuner2 as different
# audio player or just as web browser for station
# or playlist fetching.


from config import *
from channels import *
import ahttp


# override ahttp.session headers, hooks into config dialog
class useragentswitcher():

    module = 'useragentswitcher'
    meta = plugin_meta()
    map = {
       "default": "streamtuner2/2.1 (X11; Linux amd64; rv:33.0) like WinAmp/2.1",
       "vlc": "vlc 1.1.0-git-20100330-0003",
       "firefox": "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
       "chrome": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
       "android": "Mozilla/5.0 (Linux; U; Android 4.2; en-us; Nexus 10 Build/JVP15I) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30",
       "msie": "Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko",
       "itunes": "iTunes/9.0.3 (Macintosh; U; Intel Mac OS X 10_6_2; en-ca)",
       "googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
       "winamp": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648) omBrowser/1.3 (Winamp 5.57 build 2596 Beta, JSAPI2)",
       "nsplayer": "NSPlayer/11.0.5744.6324 WMFSDK/11.0",
    }

    # register
    def __init__(self, parent):
        conf.add_plugin_defaults(self.meta, self.module)
        parent.hooks["config_save"].append(self.apply)
        self.apply()    

    # set new browser string in requests session
    def apply(self):
        ua = self.map.get(conf.useragent.lower(), self.map["default"])
        if ua:
            log.HTTP("UserAgentSwitcher:", ua)
            ahttp.session.headers.update({ "User-Agent": ua })


