# api: streamtuner2
# title: Streema
# description: Directory and app for over 70.000 stations
# type: channel
# category: radio
# version: 0.2
# url: http://www.streema.com/
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABF0lEQVR42oWTMWsCURCE/Y/Bxh+QLrUIloKdELCxTOOBRSSgpZVYhCAWCtcEETGQJmCTkG7k47HcereeA4vnu32zszt7jceRFMXDQGoN
#   pd40RXci9d+kpxep+VzkNaLLXBzMpe1R+vu/jq8fabxKOSEBL6YfqgVEnSwgsMoen9+JcJlL5990xv9QAYf5qbhMC/RrQf/trLgctoA8A/0yPCO38PkVApPpAdFsndyoJeDlaKFarPZ3FJj3i12qHIEh
#   sichgSfi18j8bHDmpgvlQfFMNe/O5hAoMOnMoJMVRNjHCnsFbGKFgCl7IJPloZoHLrEPlRYi+8ogh724uUiv72ny0QeEQl+5QmDDIomeLVhdzuzzLrt1AQVnVKF/yji7AAAAAElFTkSuQmCC
# config: -
# priority: optional
# extraction-method: regex, action-handler
#
# Streema lists over 70000 radio stations. Requires a double lookup
# however, as stream addresses are embedded in the web player only.
# It does only poll one page of results.
#
# Currently playing field is quite spotty. No homepages are listed.
# The category map is prepared here, because it's quite slow to
# update. Region/city categories are left unused.
#
# The server search function is implemented however.
#


import re
import ahttp
from config import *
from channels import *


# streema.com
class streema (ChannelPlugin):

    # settings/data
    catmap = {}
    categories = ["African", ["African", "African_Gospel", "Bongo_Flava", "Cabo_Love", "Chaabi", "Ghetto", "Kizomba", "Kuduro", "Kwaito_music", "Soukous", "Zouk"], "Alternative", ["AAA", "Alternative", "Cinematics", "Dreampop", "Experimental", "Garbage", "Gothic", "IDM", "New_Wave", "Postpunk", "Progressive", "Psych", "Shoegaze", "Underground"], "Blues", ["Blues"], "Caribbean", ["Bolero", "Calypso", "Caribbean", "Chutney", "Dancehall", "Gumbe", "Hawaiian", "Kompa", "Steel_Pan"], "Classical", ["Baroque", "Chamber_Music", "Classical", "Contemporary_Classical", "Medieval", "Opera"], "Community", ["Kids", "Community", "Culture", "Ehthnic", "Folk", "Gaming", "Ham_Radio", "LGBT", "Military", "Traditional", "Woman"], "Country", ["Bluegrass", "Country", "Rural"], "Dance", ["Dance", "Disco"], "Decades", ["40s", "50s", "60s", "70s", "80s", "90s"], "Easy_Listening", ["Ambient", "Bossa_Nova", "Easy_Listening", "Lounge", "Meditation", "New_Age", "Slow", "Smooth_Jazz", "Soft", "Spiritual", "Zen"], "Electronic", ["Breaks", "Chillout", "Dance_Hits", "Deep_House", "DJ", "Downtempo", "Drum_and_Bass", "Dubstep", "EBM", "Electro", "Electronica", "Gabber", "House", "Jungle", "Laptop_Music", "Minimal", "Progressive_House", "Techno", "Trance"], "Hip_Hop", ["Hip_Hop", "Rap", "Trip_Hop"], "Indian", ["Bhangra", "Bollywood", "India", "Tamil"], "Jazz", ["Acid_Jazz", "Big_Band", "Jazz", "Latin_Jazz"], "Language", ["Arabic", "Austrian", "Brazilian", "Bulgarian", "Catalan", "Chinese", "Croatian", "Dutch", "English", "French", "Greek", "Hebrew", "Indian", "Irish", "Islamic", "Italian", "Japanese", "Lithuanian", "Mexican", "Polish", "Portuguese", "Romanian", "Russian", "Spanish", "Swedish", "Turkish"], "Latin", ["Bachata", "Cumbia", "Grupera", "Latin", "Merengue", "Ranchera", "Rapso", "Reggaeton", "Rumba", "Salsa", "Samba", "Sertanejo", "Soca", "Tejano", "Tropical", "Vallenato"], "Other", ["Acoustic", "Arabesk", "Balada", "Ballad", "Cooking", "Current_Affairs", "Eclectic", "Fado", "FIlipino", "Flamenco", "Gay", "Guitar", "Information", "Instrumental", "Language_Learning", "Live_Shows", "Manele", "Nature", "Other", "Polka", "Radio_Reading_Service", "Schlager", "Student_Radio", "Tango", "Travel_Tourism", "Variety", "Vocal"], "Pop", ["Adult_Contemporary", "Britpop", "Classics", "Hits", "J_pop", "Lite_Pop", "Old_School", "Old_Time_Radio", "Oldies", "Pop", "Standards", "Synthpop", "Teen_Pop", "Top"], "Reggae", ["Reggae"], "Region", ["Americana", "Asian", "Balkan", "Celtic", "Chansons_Francaises", "Europe", "Gospel_Pop", "Mediterranean", "Middle_Eastern", "World"], "Religion", ["Catholic", "Christian", "Gospel", "Gospel_Rock", "Jewish", "Praise_and_Worship", "Religious", "Sikh"], "RnB", ["Funk", "Groove", "Liquid_Funk", "RnB", "Soul", "Urban"], "Rock", ["Active_Rock", "Christian_Rock", "Classic_Rock", "Emo", "Garage", "Grunge", "Hard_Rock", "Hardcore", "Indie", "Metal", "Postrock", "Punk", "Rock", "Ska"], "Talk", ["Business", "College", "Education", "Emergency_and_Public_Safety", "Football", "Government", "Health", "Holistic_health", "News", "Nutrition", "Paranormal_Talk", "Politics", "Public", "Scanner", "Science", "Sex_Education", "Sports", "Talk", "Technology", "Weather"], "Theme", ["Adult", "Anime", "Art", "Astrology", "Christmas", "Comedy", "Drama", "Entertainment", "Halloween", "Hanukkah", "Holidays", "Love", "Poetry_and_Prose", "Positive", "Romantic", "Seasons", "Soundtracks", "Tribute"], "Transport", ["Air_Traffic_Control", "Airport", "Railroad", "Traffic"]]
    titles = dict(bitrate=False)
    has_search = True
    base = "http://streema.com/radios"
    

    # takes a while to load
    def update_categories(self):
        self.categories = []
        html = ahttp.get(self.base)
        main_cats = re.findall('<a href="/radios/main-genre/(\w+)">', html)
        for cat in main_cats:
            self.progress(main_cats)
            html = ahttp.get(self.base + "/main-genre/" + cat)
            sub = re.findall('<a href="/radios/genre/(\w+)">', html)
            self.categories.append(cat)
            self.categories.append(sub)
        self.progress(0)
        return self.categories


    # get streems
    def update_streams(self, cat, search=None):
        r = []
        if cat:
            html = ahttp.get(self.base + "/genre/" + cat)
        elif search:
            html = ahttp.get(self.base + "/search/?q=" + search)
        else:
            return
        
        # split into blocks
        for html in re.split('<div[^>]+class="item"', html):

            # not very efficient
            url = re.findall('data-url="/radios/play/(\d+)"', html)
            homepage = re.findall('data-profile-url="/radios/(.+?)"', html)
            title = re.findall('title="Play (.+?)"', html)
            img = re.findall('<img\s*src="(.+?)"', html)
            playing = re.findall('<span class="now-playing-text">(.*?)</span>', html, re.S)
            genre = re.findall('<p class="genre">(.*?)</p>', html, re.S)
            listeners = re.findall('<p>(\d+) Listen\w*s</p>', html)

            # catch absent fields
            try:
                r.append(dict(
                   url = "urn:streema:" + url[0],
                   homepage = self.base + "/" + homepage[0],
                   title = title[0],
                   img = img[0],
                   img_resize = 24,
                   playing = playing[0],
                   genre = unhtml(genre[0]),
                   listeners = to_int(listeners[0])
                ))
            except:
                pass #some field missing
        
        # done
        return r


    # load page and get first download url (there's four, but usually identical)
    def resolve_urn(self, row):
        if row.get("url", "-").find("urn:streema:") != 0:
            return
        id = row["url"][12:]
        html = ahttp.get("http://streema.com/radios/play/%s" % id)
        url = re.findall('<ul class="stream-downloads">.+?<a href="(.+?)"', html, re.S)
        if not url:
            return
        row["url"] = url[0]

