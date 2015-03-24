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

    # Normal
    """
    """
    # Variation
    """
    <tr><td width="74"> <div id="jquery_jplayer_19" class="jp-jplayer"></div>
	<div id="jp_container_19" class="jp-audio-stream" role="application" aria-label="media player">
		<div class="jp-type-single">
			<div class="jp-gui jp-interface">
				<div class="jp-controls">
					<i onClick="ga('send', 'event', 'tunein', 'playjp', 'http://softrockradio.purestream.net:8032/listen.pls');" style="font-size: 60px;" class="jp-play text-danger mdi-av-play-circle-outline"></i>
					<i style="font-size: 60px;" class="jp-pause text-danger mdi-av-pause-circle-outline"></i>
			</div>	</div>
			<div class="jp-no-solution text-center">
				<small><a href="http://get.adobe.com/flashplayer/" target="_blank">Flash Required</a></small>
	</div></div>
        <div id="volume19" class="text-center" style="visibility: hidden;">
                    <span class="jp-current-time"></span>
                    <div class="jp-volume-bar progress" style="margin:0;">
                            <div class="jp-volume-bar-value progress-bar active progress-bar-striped progress-bar-danger"></div>
        </div>	</div>
	</div>	</td>	<td>
				<h4 class="text-danger" style="display: inline;">SoftRockRadio.net - Classic Soft Rock  (Soft Rock Radio)</h4>
				<br>
				<b>Kenny Loggins - Heart To Heart</b><br>
				<a onClick="ga('send', 'event', 'externallink', 'listing', 'http://www.softrockradio.net');" class="small text-success" href="http://www.softrockradio.net" target="_blank">http://www.softrockradio.net</a>
				<br>Genres: <a onClick="ga('send', 'event', 'genreclick', 'stationlisting', '70s');" href="/stations/70s/">70s</a> 80s <a onClick="ga('send', 'event', 'genreclick', 'stationlisting', 'classic rock');" href="/stations/classic rock/">classic rock</a><!--
				<br><samp>19 http://softrockradio.purestream.net:8032/listen.pls shoutcast1 audio/mpeg</samp>
				<div id="jplayer_inspector_19"></div>-->
			</td>
			<td width="120" class="text-right hidden-xs">
				<p>
              			139 Listeners<br>
				 128 Kbps<br>
				</p>
				<a style="margin:1px" class="btn btn-default btn-xs" onClick="ga('send', 'event', 'tunein', 'playpls', 'http://softrockradio.purestream.net:8032/listen.pls');" href="/servers/tools/playlistgenerator/?u=http://softrockradio.purestream.net:8032/listen.pls&amp;t=.pls">PLS</a>
				<a style="margin:1px" class="btn btn-default btn-xs" onClick="ga('send', 'event', 'tunein', 'playm3u', 'http://softrockradio.purestream.net:8032/listen.pls');" href="/servers/tools/playlistgenerator/?u=http://softrockradio.purestream.net:8032/listen.pls&amp;t=.m3u">M3U</a>
				<a style="margin:1px" class="btn btn-default btn-xs" onClick="ga('send', 'event', 'tunein', 'playram', 'http://softrockradio.purestream.net:8032/listen.pls');" href="/servers/tools/playlistgenerator/?u=http://softrockradio.purestream.net:8032/listen.pls&amp;t=.ram">RAM</a>
				<a style="margin:1px" class="btn btn-default btn-xs" onClick="window.open('/player/?mount=http://softrockradio.purestream.net:8032/listen.pls&amp;title=SoftRockRadio.net - Classic Soft Rock  (Soft Rock Radio)&amp;website=http://www.softrockradio.net','_blank','width=360,height=470'); ga('send', 'event', 'tunein', 'playpopup', 'http://softrockradio.purestream.net:8032/listen.pls');" href="#">FLA</a>
    </td></tr>
    """

    # Regex extraction
    def with_regex(self, html):
        __print__(dbg.PROC, "internet-radio, regex")
        r = []
        html = "\n".join(html)
        
        # Break up into <tr> blocks before extracting bits
        rx_tr = re.compile("""<tr[^>]*>(.+?)</tr>""", re.S)
        rx_data = re.compile(r"""
               playjp',\s*'(https?://[^'">]+)
               .*?   <h4.*?>([^<>]+)</
               .*?   <b>([^<>]+)</b>
         (?:   .*?   href="(.*?)"        )?
         (?:   .*?   Genres:((?:</?a[^>]+>|\w+|\s+)+)    )?
               .*?   (\d+)\s*Listeners
               .*?   (\d+)\s*Kbps
        """, re.S|re.X)

        for div in rx_tr.findall(html):
            if div.find('id="pagination"') < 0:
                #__print__(dbg.DATA, len(div))
                uu = rx_data.search(div)
                if uu:
                    (url, title, playing, homepage, genres, listeners, bitrate) = uu.groups()
                    
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
            


