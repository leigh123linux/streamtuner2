# encoding: UTF-8
# api: streamtuner2
# title: SurfMusik
# description: Streams categorized by region and genre.
# version: 0.1
# type: channel
# category: radio
# author: gorgonz123
# source: http://forum.ubuntuusers.de/topic/streamtuner2-zwei-internet-radios-anhoeren-au/3/
#
#

import re
import ahttp as http
from config import conf
from channels import *



# Surfmusik sharing site
class surfmusik (ChannelPlugin):

    # description
    title = "surfmusik"
    module = "surfmusik"
    homepage = "http://www.surfmusik.de/"

    base = "http://www.surfmusik.de/"
    listformat = "url/http"

    categories = [
        "Genres",
        ["50ger 50s", "Dubstep", "Latin Jazz", "Schlager", "60get 60s", "Electronic", "Latino", "Sega", "70ger 70s", "Eurodance ", "Lounge", "Soft", "80ger 80s", "Filmmusik", "Metal", "Sport", "90ger 90s", "Flamenco", "Merengue", "Swing", "Acid", "Gay", "Mix", "Tamil", "Ambient", "Gospel", "New Age", "Tango", "Arabische Musik", "Gothic", "News", "Techno", "Afrikanische Musik", "Groove", "Nostalgie", "Gabber", "Artist Radio ", "Halloween", "Oktoberfest", "Hardstyle", "Bachata", "Hip Hop", "Oldies", "Jumpstyle", "Bhangra", "Hoerspiel Radio", "Poli", "Minimal", "Balladen", "House", "Pop", "Schranz", "Big Band", "Indian", "Punk", "Top 40", "Blues", "Indisch", "Radioversprecher", "Trance", "Bollywood", "Instrumentalmusik", "Reggae", "Trip Hop", "Campusradio", "Information", "RnB", "Tropical", "Celtic", "Italo Disco ", "Rochester", "Urban", "Chillout", "Jazz", "Rock", "Variety", "Country", "Karnevalsmusik", "Rock n Roll", "Volksmusik", "Dance", "Kinderradio", "Rumba/Salsa", "Zumba", "Discofox", "Kirchlich", "Russische Chansons", "Drum n Bass", "Klassik", "Salsa"],
        "Deutschland", ["Baden Wuerttemberg", "Niedersachsen", "Bayern", "Nordrhein-Westfalen", "Berlin", "Rheinland-Pfalz", "Brandenburg", "Saarland", "Bremen", "Sachsen", "Hamburg", "Sachsen-Anhalt", "Hessen", "Schleswig-Holstein", "Mecklenburg-Vorpommern", "Thueringen"],
        "Europa", ["Albanien", "Griechenland", "Mallorca", "Slowakei", "Andorra", "Irland", "Malta", "Slovenien", "Armenien", "Island", "Niederlande", "Spanien", "Aserbaidschan", "Italien", "Norwegen", "Tschech. Republ", "Belgien", "Kasachstan", "Oesterreich", "Türkei", "Bosnien", "Kanarische Inseln", "Polen", "Ungarn", "Bulgarien", "Kirgistan", "Portugal", "Ukraine", "Daenemark", "Kroatien", "Rumaenien", "Wales", "Deutschland", "Lettland", "Russland", "Weissrussland", "England", "Liechtenstein", "Schottland", "Zypern", "Estland", "Litauen", "Schweden", "Finnland", "Luxemburg", "Schweiz", "Frankreich", "Mazedonien", "Serbien"],
        "Afrika", ["Angola", "Malawi", "Aethiopien", "Mauritius", "Ägypten", "Marokko", "Algerien", "Namibia", "Benin", "Nigeria", "Burundi", "Reunion", "Elfenbeinkueste", "Senegal", "Gabun", "Simbabwe", "Ghana", "Somalia", "Kamerun", "Sudan", "Kap Verde", "Suedafrika", "Kenia", "Tansania", "Kongo", "Togo", "Libyen", "Tunesien", "Madagaskar", "Uganda", "Mali"],
        "USA", ["Alabama", "Illinois", "Montana", "Rhode Island", "Alaska", "Indiana", "Nebraska", "South Carolina", "Arizona", "Iowa", "Nevada", "South Dakota", "Arkansas", "Kansas", "New Hampshire", "Tennessee", "Californien", "Kentucky", "New Jersey", "Texas", "Colorado", "Louisiana", "New Mexico", "Utah", "Connecticut", "Maine", "New York", "Vermont", "Delaware", "Maryland", "North Carolina", "Virginia", "Distr.Columbia", "Massachusetts", "North Dakota", "Washington", "Florida", "Michigan", "Ohio", "West Virginia", "Georgia", "Minnesota", "Oklahoma", "Wisconsin", "Hawaii", "Mississippi", "Oregon", "Wyoming", "Idaho", "Missouri", "Pennsylvania", "NOAA Wetter Radio"],
        "Kanada", ["Alberta", "Ontario", "British Columbia", "Prince Edward Island", "Manitoba", "Québec", "Neufundland", "Saskatchewan", "New Brunswick", "Nordwest-Territorien", "Nova Scotia", "Yukon", "Nunavut",],
        "Amerika", ["Mexiko", "Costa Rica", "Argentinien", "Aruba", "El Salvador", "Bolivien", "Antigua", "Guatemala", "Brasilien", "Barbados", "Honduras", "Chile", "Bahamas", "Nicaragua", "Ecuador", "Bermuda", "Panama", "Franz. Guyana", "Curaçao", "Guyana", "Domenik. Republ", "Kolumbien", "Grenada", "Paraguay", "Guadeloupe", "Uruguay", "Haiti", "Suriname", "Jamaika", "Peru", "Kaimaninseln", "Venezuela", "Kuba", "Martinique", "Puerto Rico", "St.Lucia", "Saint Martin", "Trinidad und Tobago"],
        "Asien",
        "Ozeanien",
        "SurfTV",
        ["MusikTV", "NewsTV"],
    ] 
    titles = dict( genre="Genre", title="Station", playing="Location", bitrate=False, listeners=False )
 
    config = [
    ]    


    # refresh category list
    def update_categories(self):
        pass


    # download links from surfmusik listing
    def update_streams(self, cat, force=0):

        entries = []
        i = 0
        max = int(conf.max_streams)
        
        # placeholder category
        if cat in ["Genres"]:
            src = ""
        # tv
        elif cat in ["SurfTV", "MusikTV", "NewsTV"]:
            src = self.base + "" + cat.lower() + ".html"
        # genre 
        elif cat in self.categories[1]:
            src = self.base + "genre/" + cat.lower() + ".html"
        # country
        else:
            src = self.base + "land/" + cat.lower() + ".html"
        
        if src:    
            html = http.get(src)
        
            rx_current = re.compile(r"""
                <a\s+class="navil"\s+href="([^"]+)"[^>]*>([^<>]+)</a></td>
                <td\s+class="ort">(.*?)</td>.*?
                <td\s+class="ort">(.*?)</td>.*?
                <td\s+class="home1"><a\s+class="navil"\s+href="(.+?)"
            """, re.X|re.I)

            # per-country list
            for uu in rx_current.findall(html):
                (homepage, name, genre, stadt, url) = uu

                entries.append({
                    "title": name,
                    "homepage": homepage,
                    "url": "http://www.surfmusik.de/m3u/" + url[30:-5] + ".m3u",
                    "playing": stadt,
                    "genre": genre,
                })

                if i > max:
                   break
                i += 1
 
        # done    
        return entries


