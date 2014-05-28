# encoding: UTF-8
# api: streamtuner2
# title: SurfMusik
# description: User collection of streams categorized by region and genre.
# version: 0.1
# type: channel
# category: radio
# author: gorgonz123
# source: http://forum.ubuntuusers.de/topic/streamtuner2-zwei-internet-radios-anhoeren-au/3/
# recognizes: max_streams
#
# While the categories and genre names are in German, there's a vast
# collection of international stations on Surfmusik.de
# While it's not an open source project, most entries are user contributed.
#
# They do have a Windows client, hencewhy it's even more important for
# streamtuner2 to support it on other plattforms.
#
# TV stations don't seem to work mostly. And loading the webtv/ pages would
# be somewhat slow (for querying the actual mms:// streams).
#
# * There's also an English version //surfmusic.com/
#   So it might make sense to duplicate it with alternative category titles.
#

import re
import ahttp as http
from config import conf
from channels import *



# Surfmusik sharing site
class surfmusik (ChannelPlugin):

    # description
    title = "SurfMusik"
    module = "surfmusik"
    homepage = "http://www.surfmusik.de/"

    base = "http://www.surfmusik.de/"
    base2 = "http://www.surfmusic.de/"
    listformat = "audio/x-scpls"

    categories = [
        "Genres", ["50ger 50s", "Dubstep", "Latin Jazz", "Schlager", "60ger 60s", "Electronic", "Latino", "Sega", "70ger 70s", "Eurodance ", "Lounge", "Soft", "80ger 80s", "Filmmusik", "Metal", "Sport", "90ger 90s", "Flamenco", "Merengue", "Swing", "Acid", "Gay", "Mix", "Tamil", "Ambient", "Gospel", "New Age", "Tango", "Arabische Musik", "Gothic", "News", "Techno", "Afrikanische Musik", "Groove", "Nostalgie", "Gabber", "Artist Radio ", "Halloween", "Hardstyle", "Bachata", "Hip Hop", "Oldies", "Jumpstyle", "Bhangra", "Hoerspiel Radio", "Minimal", "Balladen", "House", "Pop", "Schranz", "Big Band", "Indian", "Punk", "Top 40", "Blues", "Indisch", "Radioversprecher", "Trance", "Bollywood", "Instrumentalmusik", "Reggae", "Trip Hop", "Campusradio", "Information", "RnB", "Tropical", "Celtic", "Italo Disco ", "Rochester", "Urban", "Chillout", "Jazz", "Rock", "Variety", "Country", "Karnevalsmusik", "Rock n Roll", "Volksmusik", "Dance", "Kinderradio", "Rumba/Salsa", "Zumba", "Discofox", "Kirchlich", "Russische Chansons", "Drum n Bass", "Klassik", "Salsa"],
        "Deutschland", ["Baden Wuerttemberg", "Niedersachsen", "Bayern", "Nordrhein-Westfalen", "Berlin", "Rheinland-Pfalz", "Brandenburg", "Saarland", "Bremen", "Sachsen", "Hamburg", "Sachsen-Anhalt", "Hessen", "Schleswig-Holstein", "Mecklenburg-Vorpommern", "Thueringen"],
        "Europa", ["Albanien", "Griechenland", "Mallorca", "Slowakei", "Andorra", "Irland", "Malta", "Slovenien", "Armenien", "Island", "Niederlande", "Spanien", "Aserbaidschan", "Italien", "Norwegen", "Tschech. Republ", "Belgien", "Kasachstan", "Oesterreich", "Tuerkei", "Bosnien", "Kanarische Inseln", "Polen", "Ungarn", "Bulgarien", "Kirgistan", "Portugal", "Ukraine", "Daenemark", "Kroatien", "Rumaenien", "Wales", "Deutschland", "Lettland", "Russland", "Weissrussland", "England", "Liechtenstein", "Schottland", "Zypern", "Estland", "Litauen", "Schweden", "Finnland", "Luxemburg", "Schweiz", "Frankreich", "Mazedonien", "Serbien"],
        "Afrika", ["Angola", "Malawi", "Aethiopien", "Mauritius", "Aegypten", "Marokko", "Algerien", "Namibia", "Benin", "Nigeria", "Burundi", "Reunion", "Elfenbeinkueste", "Senegal", "Gabun", "Simbabwe", "Ghana", "Somalia", "Kamerun", "Sudan", "Kap Verde", "Suedafrika", "Kenia", "Tansania", "Kongo", "Togo", "Libyen", "Tunesien", "Madagaskar", "Uganda", "Mali"],
        "USA", ["Alabama", "Illinois", "Montana", "Rhode Island", "Alaska", "Indiana", "Nebraska", "South Carolina", "Arizona", "Iowa", "Nevada", "South Dakota", "Arkansas", "Kansas", "New Hampshire", "Tennessee", "Californien", "Kentucky", "New Jersey", "Texas", "Colorado", "Louisiana", "New Mexico", "Utah", "Connecticut", "Maine", "New York", "Vermont", "Delaware", "Maryland", "North Carolina", "Virginia", "Distr.Columbia", "Massachusetts", "North Dakota", "Washington", "Florida", "Michigan", "Ohio", "West Virginia", "Georgia", "Minnesota", "Oklahoma", "Wisconsin", "Hawaii", "Mississippi", "Oregon", "Wyoming", "Idaho", "Missouri", "Pennsylvania", "NOAA Wetter Radio"],
        "Kanada", ["Alberta", "Ontario", "British Columbia", "Prince Edward Island", "Manitoba", "Québec", "Neufundland", "Saskatchewan", "New Brunswick", "Nordwest-Territorien", "Nova Scotia", "Yukon", "Nunavut",],
        "Amerika", ["Mexiko", "Costa Rica", "Argentinien", "Aruba", "El Salvador", "Bolivien", "Antigua", "Guatemala", "Brasilien", "Barbados", "Honduras", "Chile", "Bahamas", "Nicaragua", "Ecuador", "Bermuda", "Panama", "Guyana", "Curaçao", "Guyana", "Domenik. Republ", "Kolumbien", "Grenada", "Paraguay", "Guadeloupe", "Uruguay", "Haiti", "Suriname", "Jamaika", "Peru", "Kaimaninseln", "Venezuela", "Kuba", "Martinique", "Puerto Rico", "St.Lucia", "Saint Martin", "Trinidad und Tobago"],
        "Asien", ["Afghanistan", "Kirgistan", "Vereinigte Arabische Emirate", "Sued-Korea", "Bahrain", "Kuwait", "Bangladesch", "Libanon", "Brunei", "Malaysia", "China", "Nepal", "Guam", "Oman", "Hong Kong", "Pakistan", "Iran", "Palaestina", "Indien", "Philippinen", "Indonesien", "Saudi Arabien", "Israel", "Singapur", "Jordanien", "Sri Lanka", "Japan", "Syrien", "Kambodscha", "Taiwan", "Kasachstan", "Thailand",],
        "Ozeanien", ["Australien", "Neuseeland", "Suedpol", "Fidschi", "Papanew", "Tahiti",],
        #"SurfTV",
        "MusikTV", "NewsTV",
        "Poli", "Flug",
    ] 
    titles = dict( genre="Genre", title="Station", playing="Location", bitrate=False, listeners=False )
 
    config = [
        #{"name": "surfmusik_lang", "type": "select", "select":"DE=SurfMusik.de|EN=SurfMusic.de", "description": "You can alternatively use the German or English category titles.", "category": "language"}
    ]    


    # just a static list for now
    def update_categories(self):
        pass


    # summarize links from surfmusik
    def update_streams(self, cat, force=0):

        entries = []
        i = 0
        max = int(conf.max_streams)
        is_tv = 0
        
        # placeholder category
        if cat in ["Genres"]:
            path = None
        # tv
        elif cat in ["SurfTV", "MusikTV", "NewsTV"]:
            path = ""
            is_tv = 1
        # genre 
        elif cat in self.categories[1]:
            path = "genre/"
        # country
        else:
            path = "land/"
        
        if path is not None:
            html = http.get(self.base + path + cat.lower() + ".html")
            html = re.sub("&#x?\d+;", "", html)
        
            rx_radio = re.compile(r"""
                <td\s+class="home1"><a[^>]*\s+href="(.+?)"[^>]*> .*?
                <a\s+class="navil"\s+href="([^"]+)"[^>]*>([^<>]+)</a></td>
                <td\s+class="ort">(.*?)</td>.*?
                <td\s+class="ort">(.*?)</td>.*?
            """, re.X|re.I)
            rx_video = re.compile(r"""
                <a[^>]+href="([^"]+)"[^>]*>(?:<[^>]+>)*Externer
            """, re.X|re.I)

            # per-country list
            for uu in rx_radio.findall(html):
                (url, homepage, name, genre, stadt) = uu
                
                # find mms:// for webtv stations
                if is_tv:
                    m = rx_video.search(http.get(url))
                    if m:
                        url = m.group(1)
                # just convert /radio/ into /m3u/ link
                else:
                    url = "http://www.surfmusik.de/m3u/" + url[30:-5] + ".m3u"

                entries.append({
                    "title": name,
                    "homepage": homepage,
                    "url": url, 
                    "playing": stadt,
                    "genre": genre,
                    "format": ("video/html" if is_tv else "audio/mpeg"),
                })

                # limit result list
                if i > max:
                   break
                if i % 10 == 0:
                   self.parent.status(float(i)/float(max+5))
                i += 1
 
        # done    
        return entries


