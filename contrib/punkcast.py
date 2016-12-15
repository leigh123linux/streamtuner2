# api: streamtuner2
# title: PunkCast
# description: Online video site that covered NYC artists. Not updated anymore.
# type: channel
# category: video
# version: 0.3
# url: http://www.punkcast.com/
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAyxJREFUOI0FwUlvG2UAgOH3++abxfsy2dtmcRsnghpBKyKhQA7lgsShPwEk/gVcKn4HN+6AynKIkEgFUkFF
#   okrlpEkap2nqxHFsx/bYHs/m4XmE0s1Yyhjf8/niy6/49utv+PPf57x4sk3083cUzZgwZWElE9hL60yyc1zU39A8PsRxhijLMBFahO/5dFotwvGIeDxkOHJwNYvCwgyRYeElslTPu7ivTnFaTU6dkG4E
#   ytANoskYgMb5W64b51jEuJ6Lq3Rmy2tEUcz1WR1pGGiyiIhMDOlQGHZRQRAQRR4CqJ2eUNvbJcAiEYz45NMtKrdvkc8a1G5M81e1RuiGjDpt1CTASKeQytDxowmmZdLpdDl8+QJLBqTxKSYkc0afbOyz
#   OD/F/fIynhA0wwChazhIpOuNYCJI6hpxPOHiqk1K8+ldthDumFhXnLUHjEZj9DggKyWfbWywPpXHVqBEOKayXubDyl1qx0f0eh1E6GLaRX7aO8NLJjG9PvNLt0kpuJWeMHPTxnan6V81UWmpYacTVN57
#   H9uewu01+OPJDle9AY//O+Dj++9yr3wHUnl8PyCTyzL2PE5aPUgYaFlNPDKigGe7VW6U1iDwcXuXzBbz+K5PThMEvQ6xjJjEAi2Z4Wn1mP03FyR1DaU0jUbnGj81IZXLkckoSpUV7JTB0HF4urvH3IMN
#   jG6XbGGWemeAkc+hNEE0DtCSmngUCkFSixn321iWyVzGImEIVssllAh5e9kkCDV2T05pD4dMTeWpv6ohwghp6opCOOHh1kfcXZzm8S/bPNs/ZOC4mELj4eYGWiT54Z896qMJ9vws4XBE3lRIBeqmDmk/
#   Qmnw+YNNlsur/PrbDqv5NFm7SHMwpNbuMggClmYL5JWkqytErKGPPVQmilhLSpbtBE1nxMFhjedHrymkNUrv3KHTuqLvjWl7MQevL+gNXaqNLlGzSyUvUVuEzMzkWVhZYqd6xPc//o6MBfWrAZcdBxnH
#   zOcy/F1rsf3yFFmtEcWwOZ2h1R8hP5jATGmRQE+wXz0gjiMWihnO2z1qjS6ZQoF76yuU7DSxFFhJC10phmHIhVT8D1yefHn5PzXrAAAAAElFTkSuQmCC
# priority: outdated
# config: { name: punkcast_img, type: boolean, value: 0, description: Load banners. (Channel - Update favicons) }
# extraction-method: regex, play-handler
#
# Punkcast is no longer updated. This plugin is kept for
# historic reasons. It was one of the default streamtuner1
# channels.


import re
import ahttp
from config import conf
import action
from channels import *
from config import *


# Punkcast video archive
class punkcast (ChannelPlugin):

    # keeps category titles->urls    
    catmap = {}
    categories = ["list"]
    titles = dict(playing=False, listeners=False, bitrate=False, homepage=False)
    
    img_resize = 196
    fixed_size = [128,32]


    # don't do anything
    def update_categories(self):
        pass


    # get list
    def update_streams(self, cat):

        rx_link = re.compile("""
            <a\shref="(http://punkcast.com/(\d+)/index.html)">
            .*? ALT="([^<">]+)"
        """, re.S|re.X)

        entries = []
        
        #-- all from frontpage
        html = ahttp.get("http://www.punkcast.com/")
        for uu in rx_link.findall(html):
            (homepage, id, title) = uu
            entries.append({
                    "genre": "%s" % id,
                    "title": title,
                    "playing": "PUNKCAST #%s" % id,
                    "format": "audio/mpeg",
                    "url": "none:",
                    "homepage": homepage,
                    "img": "http://punkcast.com/%s/PUNK%s.jpg" % (id, id) if conf.punkcast_img else None,
            })

        # done    
        return entries


    # special handler for play
    def play(self):
        row = self.row()
        rx_sound = re.compile("""(http://[^"<>]+[.](mp3|ogg|m3u|pls|ram))""")
        html = ahttp.get(row["homepage"])
        
        # look up ANY audio url
        for uu in rx_sound.findall(html):
            log.DATA( uu )
            (url, fmt) = uu
            row["url"] = url
            action.play(row, mime_fmt(fmt), "srv")
            return
        
        # or just open webpage
        action.browser(row["homepage"])

