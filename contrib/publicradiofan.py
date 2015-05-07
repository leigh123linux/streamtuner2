# encoding: UTF-8
# api: streamtuner2
# title: PublicRadioFan
# description: Scheduled broadcasts, radio stations and genres, sorted by locations
# version: 0.1
# type: channel
# url: http://www.publicradiofan.com/
# category: radio
# priority: extra
# config: -
# png:
#   iVBORw0KGgoAAAANSUhEUgAAAA8AAAAQCAMAAAD+iNU2AAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAACbVBMVEUAAAD//wDR0QDd3QD//wAfHwAhKQALDgAICAYAAADo6ADd3QD8/ADb2wDm5gD//wD//wD//wCxsQClpQDt7QCjowCurgD//wD//wD//wD//wD//wD//wD//wCdnQClowCioACYmAD//wD//wD//wD//wD//wD//wD//wD//w
#   CurgCbmwCEgQCWlgCiogD//wD//wD//wD//wD//wDt7QDHxwDV1QD5+QDq6gCysgBYWQCkpADQ0AD//wD//wD//wD//wDm5gDDwwCOjgCoqADLywD+/gDJyQAgIAB2dgD//wD//wD//wD//wDY2ACnpwA6OgBfXwCzswD29gDOzgAgIAAdHQD//wD9/QDq6gDQ0ABtbQAHBwCEhAD8/ADh4QA/PwCamgD//wD//wD//wD//wDu7gDMzADExACamgAJCQCHhwDl5QDr6wCLiwDh4QD9/QD//wD//wD//wDv7wC6
#   ugCurgBMTAAWFQB9fAB1cADb2gDBwQDe3gDm5gD6+gD//wD//wDk5ADExAB6egKjqBZbZSpSXTp3cSVlJgXCsgG9vgDKygDU1AD39wD//wCXmQBjawBCSwFibzBQWlEuIhw+OxlmZgCOjgCkpADw8AD//wAiKwA9TQE9SkcgICETEwIcHBIfHw6DgwD//wAEBQAVGgAlJycMDAweHh4GBgQAAAABAQEAAAAEBAQAAAAAAAAAAAAAAAAAAAAAAAAAAADHswAPDwA2NgBdXQB0iHd7joxRYRJQYDBabmpdcm4jIy
#   IiJw0rLyA7Pj4+QUEJCQkDAwMfHyAAAAABAQEDAwMDAwMBAQEEBAT////bfgUcAAAAtnRSTlMAAAAAAAAAAAAADDVGMgoAAAM8pb+hNwIAAgUHBgxq5+NiBgAEDRcdHBxg1PXOUQQABBAkO1JOOT51tWcaAAELIkh9p6B4RDiNGQAEFDl3uOngtW9FlhIGKnW57v/lrXitLBMGAAtTx/P7//ntvtCJcDMHDmXk/P78/P/h7e/gdhoGRrXy9vv39fjF7/3zhx8eqO799vjo8dzCUw4S0PL6/PjJHQA23e752SSQ
#   /v/8V5P////+WUJFFrYAAAABYktHRM702fL/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3wQdFiYdwDwd5wAAAQdJREFUCNdjYAADRiYubh5ePmZGEJuRX4BFUEhYRFRMHMhnlJCUkpaRlZPfpqCoxMjAqKyiqqauoamlraOrp8/IYGBoZGxiamZuYWllbWPLyGBn7+Do5Ozi6ubu4enFyMjg7ePr5x8QGBQcEhrGCjQuPCIyKnp7TGxcfEJiUnIKQ2paekbmjqzsnNy8/ILCIobiktKdZeUVlVXVNb
#   V19Q0MjU3NLa1t7R2dXd09vX39DAwTJk6avGv3lKnTps+YOWs2A9ucuXv27ts/b/6BBQsXLV7CwL502cFDh48sX3H02PGVqzgYGFafOHHy1Ok1a0+cObtuPScDw4YTG4Fg0+aNG09s2coAANV6WR2+KyzWAAAAJXRFWHRkYXRlOmNyZWF0ZQAyMDE1LTA0LTMwVDAwOjM4OjA5KzAyOjAwPqZVxAAAACV0RVh0ZGF0ZTptb2RpZnkAMjAxNS0wNC0zMFQwMDozODowOSswMjowME/77XgAAAAASUVORK5CYII=
# x-png-src: https://openclipart.org/detail/101737/vacuum-tubes
#
# PRF is a privately maintained directory of international
# radio stations, scheduled broadcasting programs, and
# internet streams grouped by location/genre/format/topics.
#
# This plugin is just browsing the format categories, uses a
# static genre list. Podcasts, scheduled programs aren't fetched.


import re
from config import *
from channels import *
import ahttp
import action


# Basic HTML scraping
class publicradiofan (ChannelPlugin):

    # control attributes
    has_search = False
    format = "mp3"
    listformat = "href"
    titles = dict(listeners=False, bitrate=False, playing="Description")

    categories = ["adult alternative", "adult contemporary", "blues", "business", "classical",
    "community", "contemporary", "country", "easy", "education", "ethnic", "folk", "free-form",
    "full service", "government", "international", "jazz", "military", "news", "nostalgia",
    "oldies", "reading", "regional", "religious", "rock", "seasonal", "sports", "student",
    "talk", "traffic", "urban", "variety", "world", "youth"]
    

    # static
    def update_categories(self):
        pass
        

    # Extract from listing tables
    def update_streams(self, cat, search=None):

        html = ahttp.get("http://www.publicradiofan.com/cgibin/statsearch.pl?format={}&lang=".format(cat))
        html = re.split("<H2>", html, 2, re.S)[1]
        probe = action.extract_playlist()

        r = []
        for html in re.split("<TR VALIGN=TOP>", html, 0):
            m = re.search(r"""
                <A .*? HREF=" (?P<url> .+?) ">
                <B> (?P<title> .*?) </B>
                .*? stt> (?P<descr> .*?) [<&]
                .*? stt> (?P<genre> .*?) [<&]
                .*? <I> .*? HREF="(?P<homepage> .*?)"
            """, html, re.X|re.S)
            if m:
                r.append(dict(
                    genre = m.group("genre"),
                    url = m.group("url"),
                    title = m.group("title"),
                    playing = m.group("descr"),
                    homepage = m.group("homepage"),
                    listformat = probe.probe_ext(m.group("url")) or "srv",
                ))
        return r

