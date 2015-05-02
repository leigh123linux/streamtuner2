# encoding: UTF-8
# api: streamtuner2
# title: User Agent Switcher
# description: Mask streamtuner2 as browser or different radio player.
# version: 0.1
# type: feature
# category: session
# priority: rare
# config:
#   { type=select, name=useragent, value=Streamtuner2, select="Streamtuner2|VLC|Firefox|Chrome|Android|MSIE|iTunes", description=Which browser string to use for HTTP requests. }
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

    module = "useragentswitcher"
    meta = plugin_meta()
    map = {
       "default": "streamtuner2/2.1 (X11; Linux amd64; rv:33.0) like WinAmp/2.1",
       "vlc": "vlc 1.1.0-git-20100330-0003",
       "firefox": "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
       "chrome": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
       "android": "Mozilla/5.0 (Linux; U; Android 4.0.3; ko-kr; LG-L160L Build/IML74K) AppleWebkit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30",
       "msie": "Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko",
       "itunes": "iTunes/9.0.3 (Macintosh; U; Intel Mac OS X 10_6_2; en-ca)",
       "googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
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


