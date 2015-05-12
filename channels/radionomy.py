# encoding: UTF-8
# api: streamtuner2
# title: Radionomy
# description: Modern radio directory and streaming provider
# url: http://radionomy.com/
# version: 0.5
# type: channel
# category: radio
# config: -
#    { name: radionomy_pages,  type: int,  value: 3,  category: limit,  description: Number of pages per category to scan. }
#    { name: radionomy_update,  type: boolean,  value: 1,  description: Also fetch OnAir updates about currently playing songs. }
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAACXBIWXMAAAsTAAALEwEAmpwYAAABIElEQVQ4y62Uv0rEQBCHv/yRQziJ1bYWV/gCaxrhGrtrg1f5GMc+xOKLeIetVjZXHRrwAewstxMWFDViM5EQcrk9yTRJZn+/j51h
#   JhESypZnwAKYAWP6wwN3wLUz+gkgEsglsOR/MXdGryK5yaMk34ECWAPVFmMCTIFb4FByeSrl1JDMGf0VcIt7ZcsMeBPYIpaeABSBEABEW8jnLG00dt0WK1ueSikvwDnw4YzeNCS1Z5w2klULkgAb4Bh4AC7kKOrypDsq+JHnBDgBRtuE
#   aWBLrpzRr32COBD0vEsQCvocCsQ+oKTj/Ehm5rtnyv9AXt6nrYGrgKyxBl1Re3ykbHkDzPdcEZQtDxorshxsaQf7jcTSjxWQC8wHmL1oc/HyC1/TWBfFRR9xAAAAAElFTkSuQmCC
# priority: extra
#
# Over 6500 radio stations of mixed genres and from different
# countries.
#
# Radionomy is a commercial radio hosting service. All listed
# stations are actually hosted by itself. Public and free access.
# And stream hosting is free as well, by adding advertisements,
# and given a daily listener quota.
#
# With "RMO" it furthermore provides access to a reusable song
# collection, and jingles etc.


from config import *
from channels import *
import ahttp
import re
import json
from pq import pq


# radionomy
class radionomy (ChannelPlugin):

    # control attributes
    has_search = False
    listformat = "srv"
    audioformat = "audio/mpeg"
    titles = dict(listeners=False, bitrate=False)
    categories = []
    
    base = "http://www.radionomy.com"

    playing = {}  # OnAir/Update dict


    # categories
    def update_categories(self):

        # get main categories
        main = []
        html = ahttp.get(self.base + "/en/style/")
        for a in pq(html)("#browseMainGenre li a"):
            main += [a.text]
            self.catmap[a.text] = a.attrib["href"]
        cats = [main[0], [main[1]]]

        # append sub categories
        for cat in main[2:]:
            cats.append(cat)
            subs = []
            html = ahttp.get("http://www.radionomy.com" + self.catmap[cat])
            for a in pq(html)("#browseSubGenre li a"):
                subs += [a.text]
                self.catmap[a.text] = a.attrib["href"]
            cats.append(subs)

        self.categories = cats


    # stations
    def update_streams(self, cat, search=None):
        r = []
        # category or search
        if cat:
            req = self.base + self.catmap[cat]

        # assemble page input
        html = ahttp.get(req)
        self.onair_update(req)
        for i in range(0, int(conf.radionomy_pages) - 1):
            add = ahttp.get(req, { "scrollOffset": i }, post=1, ajax=1)
            if add.find("browseRadio") < 0:
                break
            html += add
            self.onair_update(req)
        
        # extractzz
        for data in self.data_play_stream(html):
            data = json.loads(data)
            # combine
            r.append(dict(
                genre = cat,
                title = data["title"],
                url = data["mp3"],
                playing = self.playing.get(data["radioUID"], data["song"]),
                favourite = int(data.get("isFavorite", 0)),
                homepage = "http://www.radionomy.com/en/radio/{}/index".format(data["url"]),
                img = re.sub("\.s\d+\.", ".s32.", data["logo"]),
                uid = data["radioUID"],
            ))
        return r


    # Extracts the data- attribute JSON blob
    @use_rx
    def data_play_stream(self, html, use_rx):
        if use_rx:
            return [entity_decode(j) for j in re.findall('data-play-stream="({.*?})"', html)]
        else:
            # fix up for PyQuery, else ignores appended content
            html = re.sub("</html>|</body>", "", html) + "</body></html>"
            return [div.attrib["data-play-stream"] for div in pq(html)(".browseRadioWrap .radioPlayBtn")]


    # Retrieve en/OnAir/Update for per-UID song titles
    def onair_update(self, req):
        if conf.radionomy_update:
            try:
                d = json.loads(
                    ahttp.get("https://www.radionomy.com/en/OnAir/Update", post=1, referer=req)
                )
                if not d:
                    return
                print d
                self.playing.update(
                    {row["RadioUID"]: "{Title} - {Artist}".format(**row) for row in d}
                )
            except Exception as e:
                log.ERR("Radionomy title update:", e)

                
