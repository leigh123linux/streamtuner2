#
# api: streamtuner2
# title: Internet-Radio.com
# description: Broad list of webradios from all genres.
# type: channel
# category: radio
# version: 1.1
# priority: standard
#
# Internet-Radio.co.uk/.com is one of the largest directories of streams.
# Available music genre classifications are mirrored verbatim and flatly.
#
# The new version of this plugin alternates between PyQuery and Regex
# station extraction. Both overlook some paid or incomplete entries.
# HTTP retrieval happens in one batch, determined by the number of pages
# setting, rather than the global max_streams option.
#
#
#
#
#



from channels import *
import re
from config import conf, __print__, dbg
import ahttp as http
from pq import pq




# streams and gui
class internet_radio (ChannelPlugin):


    # description
    title = "InternetRadio"
    module = "internet_radio"
    homepage = "http://www.internet-radio.org.uk/"
    listformat = "audio/x-scpls"
    
    # settings
    config = [
        {
            "name": "internetradio_max_pages",
            "type": "int",
            "value": 5,
            "category": "limit",
            "description": "How many pages to fetch and read.",
        },
    ]
    

    # category map
    categories = []
    current = ""
    default = ""


    # load genres
    def update_categories(self):
    
        html = http.get(self.homepage)
        rx = re.compile("""<option[^>]+value="/stations/[-+&.\w\s%]+/">([^<]+)</option>""")
        
        self.categories = rx.findall(html)


    # fetch station lists
    def update_streams(self, cat):
    
        entries = []
        if cat not in self.categories:
            return []

        rx_pages = re.compile('href="/stations/[-+\w%\d\s]+/page(\d+)">\d+</a>')

        # Fetch multiple pages at once
        html = []
        max_pages = max(int(conf.internetradio_max_pages), 1)
        for page in range(1, max_pages):
        
            # Append HTML source
            html.append(
                http.get(
                    self.homepage + "stations/" +
                    cat.lower().replace(" ", "%20") +
                    "/" + ("page"+str(page) if page>1 else "")
                )
            )
            
            # Is there a next page?
            if str(page+1) not in rx_pages.findall(html[-1]):
                break
            self.parent.status(float(page)/float(max_pages+1))

        # Alternatively try regex or pyquery parsing
        #__print__(dbg.HTTP, html)
        for use_rx in [not conf.pyquery, conf.pyquery]:
            try:
                entries = (self.with_regex(html) if use_rx else self.with_dom(html))
                if len(entries):
                    break
            except Exception as e:
                __print__(dbg.ERR, e)
                continue
            
        # fin
        return entries

    # Advertised 
    """
    <tr valign="top" class="stream">
    <td class="listing1" width="120" align="center">
    <a onClick="return popitup('/player/?mount=http://uk2.internet-radio.com:31076/listen.pls&amp;title=Box Uk Radio Danceradiouk&amp;website=http://danceradiouk.com ')"
       href="/player/?mount=http://uk2.internet-radio.com:31076/listen.pls&amp;title=Box Uk Radio Danceradiouk&amp;website=http://danceradiouk.com ">
       <img style="margin-right: 6px;" src="/images/blank.gif" class="sprite sprite-flash" alt="Flash Player"></a>
       <a onClick="_gaq.push(['_trackEvent', 'TuneIn', 'Play - M3U', 'http://uk2.internet-radio.com:31076/listen.pls']);"
       href="http://servers.internet-radio.com/tools/playlistgenerator/?u=http://uk2.internet-radio.com:31076/listen.pls&amp;t=.m3u">
       <img style="margin-right: 6px;" src="/images/blank.gif" class="sprite sprite-wmp" alt="Windows Media Player"></a>
       <a onClick="_gaq.push(['_trackEvent', 'TuneIn', 'Play - PLS', 'http://uk2.internet-radio.com:31076/listen.pls']);"
       href="http://servers.internet-radio.com/tools/playlistgenerator/?u=http://uk2.internet-radio.com:31076/listen.pls&amp;t=.pls">
       <img style="margin-right: 6px;" src="/images/blank.gif" class="sprite sprite-winamp" alt="Winamp">
       <img style="margin-right: 6px;" src="/images/blank.gif" class="sprite sprite-itunes" alt="iTunes"></a>
       <a onClick="_gaq.push(['_trackEvent', 'TuneIn', 'Play - RAM', 'http://uk2.internet-radio.com:31076/listen.pls']);"
       href="http://servers.internet-radio.com/tools/playlistgenerator/?u=http://uk2.internet-radio.com:31076/listen.pls&amp;t=.ram">
       <img src="/images/blank.gif" class="sprite sprite-realplayer" alt="Realplayer"></a><br>
       <div style="margin-top: 10px;"><a href="/stations/80s/">80s</a> <a href="/stations/90s/">90s</a> 00s <a href="/stations/rock/">Rock</a> <a href="/stations/disco/">Disco</a> <a href="/stations/pop/">Pop</a> </div></td>
    <td class="listing2" ><img src="/images/icons/award_star_silver_1.png" alt="Featured" width="16" height="16">
       <a href="/station/danceradioukchatbox/" style="font-weight:bold;">Box Uk Radio Danceradiouk</a>
    <br>Bow Wow Wow - I Want Candy
    <br><a onClick="_gaq.push(['_trackEvent','Link', 'Station Link', 'http://danceradiouk.com ']);"
       class="url" href="http://danceradiouk.com " title="Box Uk Radio Danceradiouk" target="_blank">http://danceradiouk.com </a>
    </td><td class="listing1" align="right" width="100">
    128 Kbps<br>22 Listeners<br>
    <img src="/images/blank.gif" class="sprite sprite-de" alt="Germany"><img src="/images/blank.gif" class="sprite sprite-cy" alt="Cyprus">
    <img src="/images/blank.gif" class="sprite sprite-se" alt="Sweden"><img src="/images/blank.gif" class="sprite sprite-gb" alt="United Kingdom">
    <img src="/images/blank.gif" class="sprite sprite-rw" alt="Rwanda"><img src="/images/blank.gif" class="sprite sprite-mx" alt="Mexico">
    <img src="/images/blank.gif" class="sprite sprite-ru" alt="Russian Federation"><img src="/images/blank.gif" class="sprite sprite-si" alt="Slovenia">
    <img src="/images/blank.gif" class="sprite sprite-ca" alt="Canada"><img src="/images/blank.gif" class="sprite sprite-tt" alt="Trinidad and Tobago">
    <img src="/images/blank.gif" class="sprite sprite-ch" alt="Switzerland"><img src="/images/blank.gif" class="sprite sprite-hu" alt="Hungary">
    <img src="/images/blank.gif" class="sprite sprite-lt" alt="Lithuania">
    </td></tr>
    """
    # Normal
    """
    <tr valign="top" class="stream">
    <td class="listing1" width="120" align="center">
    <img style="margin-right: 6px;" src="/images/icons/blank.png" alt="Blank">
    <a onClick="_gaq.push(['_trackEvent', 'TuneIn', 'Play - M3U', 'http://80.86.106.136:80/listen.pls']);"
       href="http://servers.internet-radio.com/tools/playlistgenerator/?u=http://80.86.106.136:80/listen.pls&amp;t=.m3u">
       <img style="margin-right: 6px;" src="/images/blank.gif" class="sprite sprite-wmp" alt="Windows Media Player"></a>
       <a onClick="_gaq.push(['_trackEvent', 'TuneIn', 'Play - PLS', 'http://80.86.106.136:80/listen.pls']);"
       href="http://servers.internet-radio.com/tools/playlistgenerator/?u=http://80.86.106.136:80/listen.pls&amp;t=.pls">
       <img style="margin-right: 6px;" src="/images/blank.gif" class="sprite sprite-winamp" alt="Winamp">
       <img style="margin-right: 6px;" src="/images/blank.gif" class="sprite sprite-itunes" alt="iTunes"></a>
       <a onClick="_gaq.push(['_trackEvent', 'TuneIn', 'Play - RAM', 'http://80.86.106.136:80/listen.pls']);"
       href="http://servers.internet-radio.com/tools/playlistgenerator/?u=http://80.86.106.136:80/listen.pls&amp;t=.ram">
       <img src="/images/blank.gif" class="sprite sprite-realplayer" alt="Realplayer"></a>
       <br><div style="margin-top: 10px;">Top 40 </div></td>
    <td class="listing2" ><img src="/images/icons/award_star_bronze_1.png" alt="Recommended" width="16" height="16">
       <a href="/station/kissfmromania/" style="font-weight:bold;">KissFM Romania - www.kissfm.ro</a>
    ---ALTERNATIVELY--- <span style="color: #c00;"><b> TDI Radio MP3 48kbps</b></span>
    <br><a onClick="_gaq.push(['_trackEvent','Link', 'Station Link', 'http://www.kissfm.ro']);"
       class="url" href="http://www.kissfm.ro" title="KissFM Romania - www.kissfm.ro" target="_blank">http://www.kissfm.ro</a>
    </td><td class="listing1" align="right" width="100">
    32 Kbps<br>5716 Listeners<br>
    </td></tr>
    """
    # Variation
    """
    <td class="listing1" width="120" align="center">
    <img style="margin-right: 6px;" src="/images/icons/blank.png" alt="Blank">
      <a onClick="_gaq.push(['_trackEvent', 'TuneIn', 'Play - M3U', 'http://colostreaming.com:8092/listen.pls']);"
       href="http://servers.internet-radio.com/tools/playlistgenerator/?u=http://colostreaming.com:8092/listen.pls&amp;t=.m3u">
      <img style="margin-right: 6px;" src="/images/blank.gif" class="sprite sprite-wmp" alt="Windows Media Player"></a>
      <a onClick="_gaq.push(['_trackEvent', 'TuneIn', 'Play - PLS', 'http://colostreaming.com:8092/listen.pls']);" 
      href="http://servers.internet-radio.com/tools/playlistgenerator/?u=http://colostreaming.com:8092/listen.pls&amp;t=.pls">
      <img style="margin-right: 6px;" src="/images/blank.gif" class="sprite sprite-winamp" alt="Winamp"><img style="margin-right: 6px;" src="/images/blank.gif" class="sprite sprite-itunes" alt="iTunes"></a>
      <a onClick="_gaq.push(['_trackEvent', 'TuneIn', 'Play - RAM', 'http://colostreaming.com:8092/listen.pls']);" href="http://servers.internet-radio.com/tools/playlistgenerator/?u=http://colostreaming.com:8092/listen.pls&amp;t=.ram"><img src="/images/blank.gif" class="sprite sprite-realplayer" alt="Realplayer"></a>
    <br><div style="margin-top: 10px;">Poprock <a href="/stations/dance/">Dance</a> 50s Various </div></td>
    <td class="listing2" ><img src="/images/icons/award_star_bronze_1.png" alt="Recommended" width="16" height="16">
      <span style="color: #c00;"><b> Jack and Jill Radio Pop Rock Dance 50s Big Band Classical Country Folk Jazz Blue</b></span>
    <br>Vince Gill - When Love Finds You - (Album)When Love Finds You - 1994 Countr
    <br><a onClick="_gaq.push(['_trackEvent','Link', 'Station Link', 'http://www.jackandjillradio.com']);"
     class="url" href="http://www.jackandjillradio.com" title="Jack and Jill Radio Pop Rock Dance 50s Big Band Classical Country Folk Jazz Blues Its All Here!" target="_blank">http://www.jackandjillradio.com</a>
    </td><td class="listing1" align="right" width="100">
    24 Kbps<br></td>
    """

    # Regex extraction
    def with_regex(self, html):
        __print__(dbg.PROC, "internet-radio, regex")
        r = []
        html = "\n".join(html)
        
        # Break up into <tr> blocks before extracting bits
        rx_tr = re.compile("""<tr[^>]*>(.+?)</tr>""", re.S)
        rx_data = re.compile(r"""
               \?u=(https?://[^'">]+/listen\.pls)       
               .*?
               <div[^>]+10px[^>]+>(.+?)</div>           
               .*?
               listing2
               .*?
               (?:href="/station/[^>]+> | <b>) ([^<>]+) </[ab]>
               (?:\s*</span>\s*)*
               (?:<br>\s*([^<>]+)\s*<br>)?                
               .*?
               (?:<a[^>]+class="url"[^>]+href="([^<">]+)")?  
               .+
               listing1
               .*?
               (?:(\d+)\s+Kbps \s*<br>\s*)?                  
               (?:(\d+)\s+Listeners)?
               (?:\s*<br>\s*)?
               \s*</td>             
        """, re.S|re.X)

        for div in rx_tr.findall(html):
            if div.find('id="pagination"') < 0:
                #__print__(dbg.DATA, len(div))
                uu = rx_data.search(div)
                if uu:
                    (url, genres, title, playing, homepage, bitrate, listeners) = uu.groups()
                    
                    # transform data
                    r.append({
                        "url": url,
                        "genre": self.strip_tags(genres or ""),
                        "homepage": http.fix_url(homepage or ""),
                        "title": (title or "").strip().replace("\n", " "),
                        "playing": (playing or "").strip().replace("\n", " "),
                        "bitrate": int(bitrate or 0),
                        "listeners": int(listeners or 0),
                        "format": "audio/mpeg", # there is no stream info on that, but internet-radio.org.uk doesn't seem very ogg-friendly anyway, so we assume the default here
                    })
                else:
                    __print__(dbg.ERR, "rx missed", div)
        return r


    # DOM traversing
    def with_dom(self, html_list):
        __print__(dbg.PROC, "internet-radio, dom")
        rx_numbers = re.compile("(\d+)")
        r = []
        for html in html_list:
            # the streams are arranged in table rows
            doc = pq(html)
            for dir in (pq(e) for e in doc("tr.stream")):
                
                bl = dir.find("td[align=right]").text()
                bl = rx_numbers.findall(str(bl) + " 0 0")
                
                r.append({
                    "title": dir.find("b").text(),
                    "homepage": http.fix_url(dir.find("a.url").attr("href")),
                    "url": dir.find("a").eq(2).attr("href"),
                    "genre": dir.find("td").eq(0).text(),
                    "bitrate": int(bl[0]),
                    "listeners": int(bl[1]),
                    "format": "audio/mpeg",
                    "playing": dir.find("td").eq(1).children().remove().end().text()[13:].strip(),
                })
        return r
            


