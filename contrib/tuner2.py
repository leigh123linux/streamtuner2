# encoding: UTF-8
# api: streamtuner2
# title: Tuner2.com
# description: Your ears will know
# url: http://tuner2.com/
# doc-provider: Media Tuners LLC
# version: 0.1
# type: channel
# category: radio
# png:
#    iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAADVElEQVR42mWTfUzUdRzH738f8IDBQWVPLu84rrsLCRRZmGXnMCtCgnt+APSOFOWoWzJFRBPhIK4LTsY1m6mtU4FVo7BsrXO52ajmJl62xXTpam5t/pfwu736HPQX/fHe9/v9fPb9PL7fqnyzj6XIe6aRPLMXjclHgSDX
#    7JK7vI3N4m8k3+hGY87YfahWFTlYiiydk+zMXWun9KW97D84ykBsjGPDYziCJ1hb1SZ+G+oiO6qszIclWCmObAlyoO8MV6/NEo6M49gXZ9vOGBZvlOItHTxR5idHa80EcPI/6Lxk6+vwtUXZFehiNBrh0sdDjI2EqXUeYn3tUdaU76bQ4JYAOilVoNbZJXOmAhf5JT563vuIuzNfo0wf
#    Zv5KG3M3BklfP84v8Xpq9sQxbO7g8eIGCaB1ota6WV7kliA2tto7uZX6CWXMxmzbY4x4nuV0Vy3pVD9z31hIRcvwdk1Qsq2bPEmsUktGtfS7UmfFHxphfvZL/t77CDsrK8jNzEPfsDDQ+9fHSZ8pZvxIAM+hBCZLSCqWFlZoHRSsC9C4L4JySz77V1Gxbju5soFleis5az10dAwyN1HD
#    r91mBk8lqW4/y6NGqyR1odq4/R1mbqT456+fUXp19L5uIkvvEthRFzs4emyY+fEd3HtLzflPJwjGkhi3tMsKbQsrV30xdZm5+3dQbsZRIoV817eZZlsznQeO89ulKMpACXfa85lKnKP//DUs9iPScr1w5L8Af9y+TfreNMqPHh5MVjD//csoyQDKh8/xoHUZNw+WcuHCRaKTM9Q0HWaF
#    tkk4YpUKFkmnupxMovx5hfR0kHTCgPLBaub7NdztfopEeD89p3+gNfotla+8TY6seqE1Gbpal2GsMNG0wUMiNsDvn4e4+smbfDYYYOjdHlrCk9SEzrKpOU5llRPjRg9PV/oof2EXz7+6m03VftaYhYnLDVY0Ukpv9xAnv0qxtWmUDe4TlL4Rocz6PmW2YdZ7T1LVcgpL6Byu8EV8vVNU
#    VLeyWv+a8EBW8aRhB8HOYepbeqnfE6ZBTmtLHzY56wJiC/RQ5+/BGYzSFIpR/mKAHOHHQgsFpkaRqntRphkpCzQi5TyxF4p8C0wiYZH0QyLnh00uCsweFv4YF+X8L6KBLpzwswJYAAAAAElFTkSuQmCC
# priority: optional
# extraction-method: regex
#
# A station list website featuring a map. (Uncovered via streamripper
# homepage, which however mentions those streams not being recordable).
# Most entries are AAC+. Else MP3. No Vorbis streams.
#
# Furthermore no homepages, and playing= field is only sometimes set.
# Gotostationpage URLs don't work either. The website seems a bit
# unmaintained. Yet still provides iPhone/Android apps.
#
# This plugin just fetches a single result list page per category. But
# supports the live server search, as the result format is identical
# and easy to extract.


import re
from config import *
from channels import *
import ahttp


# vtuner2.com directory
class tuner2 (ChannelPlugin):

    # control flags
    has_search = True
    audioformat = "audio/mpeg"
    titles = dict(listeners=False)
    base = "http://www.tuner2.com/"

    # Categories come straight from a <select> box
    def update_categories(self):
        html = ahttp.get("http://www.tuner2.com/")
        self.categories = re.findall('<option value="/index.html\?s=([\w\s]+)">[\w\s]+</option>', html)

    # Page fetching and row extraction
    def update_streams(self, cat, search=None):
        html = ahttp.get(self.base + "index.html?s=" + (cat or search))

        # each entry in two <tr> blocks, but can be extracted without further ado
        ls = re.findall("""
            <p\s+class="stations"><a\s+href="([^"]+)"    .+?
            <font\s+class="stationname">([^<]+)</font>
            \s*\[(.+?)\]   .+?
            (?:Now\s+playing:\s+<.+?>([^<]+)< .+?)?
            <p\sclass="stations">(AAC\+|MP3|OGG)<br.*?>(\d+)
            """, html, re.X|re.S)
        r = []
        for e in ls:
            print e
            r.append(dict(
                url = unhtml(e[0]),
                title = unhtml(e[1]),
                genre = e[2],
                playing = unhtml(e[3]),
                format = mime_fmt(e[4]),
                listeners = to_int(e[5])
            ))
        return r
