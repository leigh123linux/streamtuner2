# encoding: UTF-8
# api: streamtuner2
# title: Youtube
# description: Channel, playlist and video browsing for youtube.
# type: channel
# version: 0.2
# url: http://www.youtube.com/
# category: video
# config:
#    { name: youtube_channels,  type: text,  value: "Key Of Awesome, Pentatonix",  description: "Preferred channels to list videos from.",  category: select }
#    { name: youtube_region,  type: select,  select: "=No Region|AR=Argentina|AU=Australia|AT=Austria|BE=Belgium|BR=Brazil|CA=Canada|CL=Chile|CO=Colombia|CZ=Czech Republic|EG=Egypt|FR=France|DE=Germany|GB=Great Britain|HK=Hong Kong|HU=Hungary|IN=India|IE=Ireland|IL=Israel|IT=Italy|JP=Japan|JO=Jordan|MY=Malaysia|MX=Mexico|MA=Morocco|NL=Netherlands|NZ=New Zealand|PE=Peru|PH=Philippines|PL=Poland|RU=Russia|SA=Saudi Arabia|SG=Singapore|ZA=South Africa|KR=South Korea|ES=Spain|SE=Sweden|CH=Switzerland|TW=Taiwan|AE=United Arab Emirates|US=United States",  value: UK,  description: "Filter by region id.",  category: auth }
#    { name: youtube_wadsworth,  type: boolean,  value: 0,  description: "Apply Wadsworth constant.",  category: filter }
# priority: optional
# depends: bin:youtube-dl
#
# 
# Lists recently popular youtube videos by category or channels.
#
# Introduces the faux MIME type "video/youtube" for player and recording
# configuration; both utilizing `youtube-dl`. But VLC can consume Youtube
# URLs directly anyhow.
#
# For now custom channel names must be configured in the settings dialog
# text entry, and applied using Channel > Update categories..


from config import *
from channels import *

import ahttp
import json



# Youtube
#
#
# INTERNA
#
# The Youtube v3.0 API is quite longwinded. Here the .api() call shadows
# a few of the details.
# While .wrap3() unpacks the various variations of where the video IDs
# get hidden in the result sets.
# Google uses some quote/billing algorithm for all queries. It seems
# sufficient for Streamtuner2 for now, as the fields= JSON filter strips
# a lot of uneeded data. (Clever idea, but probably incurs more processing
# effort on Googles servers than it actually saves bandwidth, but hey..)
#
# EXAMPLES
#
#  api("videos", chart="mostPopular")
#  api("search", chart="mostPopular", videoCategoryId=10, order="date", type="video")
#  api("channels", categoryId=10)
#  api("search", topicId="/m/064t9", type="video")
#
# Discovery
#
#   videoCat  Music  id= 10
#   guideCat  Music  id= GCTXVzaWM   channelid= UCBR8-60-B28hp2BmDPdntcQ
#   topicId   Music  mid= /m/0kpv0g
#
class youtube (ChannelPlugin):

    # description
    title = "Youtube"
    module = "youtube"
    homepage = "http://www.youtube.com/"
    listformat = "url/youtube"
    has_search = True
    fmt = "video/youtube"
    titles = dict( genre="Channel", title="Title", playing="Playlist", bitrate=False, listeners=False )

    # API config
    service = {
        2: [ "http://gdata.youtube.com/",
            {
                "v": 2,
                "alt": "json",
                "max-results": 50,
            }
        ],
        3: [ "https://www.googleapis.com/youtube/v3/",
            {
                "key": "AIzaSyAkbLSLn1VgsdFXCJjjdZtLd6W8RqtL4Ag",
                "maxResults": 50,
                "part": "id,snippet",
                "fields": "pageInfo,nextPageToken,items(id,snippet(title,thumbnails/default/url,channelTitle))",
            }
        ]
    }

    categories = [
        "mostPopular",
        ["Music", "Comedy", "Movies", "Shows", "Trailers", "Film & Animation", "Entertainment", "News & Politics"],
        "topics",
        ["Pop", "Billboard charts", "Rock", "Hip Hop", "Classical", "Soundtrack", "Ambient",
         "Jazz", "Blues", "Soul", "Country", "Disco", "Dance", "House", "Trance", "Techno", "Electronica"],
        "my channels",
        ["Key of Awesome", "Pentatonix"]
    ] 
    # from GET https://www.googleapis.com/youtube/v3/videoCategories?part=id%2Csnippet&
    videocat_id = {
        "Film & Animation": 1,
        "Autos & Vehicles": 2,
        "Music": 10,
        "Pets & Animals": 15,
        "Sports": 17,
        "Short Movies": 18,
        "Travel & Events": 19,
        "Gaming": 20,
        "Videoblogging": 21,
        "People & Blogs": 22,
        "Comedy": 34,
        "Entertainment": 24,
        "News & Politics": 25,
        "Howto & Style": 26,
        "Education": 27,
        "Science & Technology": 28,
        "Nonprofits & Activism": 29,
        "Movies": 30,
        "Anime/Animation": 31,
        "Action/Adventure": 32,
        "Classics": 33,
        "Documentary": 35,
        "Drama": 36,
        "Family": 37,
        "Foreign": 38,
        "Horror": 39,
        "Sci-Fi/Fantasy": 40,
        "Thriller": 41,
        "Shorts": 42,
        "Shows": 43,
        "Trailers": 44,
    }
    # Freebase topics
    topic_id = {
        "pop": "/m/064t9",
        "billboard charts": "/m/04qf57",
        "rock": "/m/06by7",
        "dance": "/m/0ggx5q",
        "classical": "/m/0ggq0m",
        "hip hop": "/m/0glt670",
        "soundtrack": "/m/0l14gg",
        "ambient": "/m/0fd3y",
        "electronica": "/m/0m0jc",
        "jazz": "/m/03_d0",
        "techno": "/m/07gxw",
        "disco": "/m/026z9",
        "country": "/m/01lyv",
        "blues": "/m/0155w",
        "soul": "/m/0gywn",
        "trance": "/m/07lnk",
        "house": "/m/03mb9",
    }


    # just a static list for now
    def update_categories(self):
        i = self.categories.index("my channels") + 1
        self.categories[i] = [ title.strip() for title in conf.youtube_channels.split(",") ]


    # retrieve and parse
    def update_streams(self, cat, search=None):

        entries = []
        channels = self.categories[self.categories.index("my channels") + 1]
        
        # plain search request for videos        
        if search is not None:
            for row in self.api("search", type="video", regionCode=conf.youtube_region, q=search):
                entries.append( self.wrap3(row, {"genre": ""}) )

        # Most Popular
        elif cat == "mostPopular":
            #for row in self.api("feeds/api/standardfeeds/%s/most_popular"%conf.youtube_region, ver=2):
            #    entries.append(self.wrap2(row))
            for row in self.api("videos", chart="mostPopular", regionCode=conf.youtube_region):
                entries.append( self.wrap3(row, {"genre": "mostPopular"}) )

        # Categories
        elif cat in self.videocat_id:
            for row in self.api("search", chart="mostPopular", videoCategoryId=self.videocat_id[cat], order="date", type="video"):
                entries.append( self.wrap3(row, {"genre": cat}) )

        # Topics
        elif cat.lower() in self.topic_id:
            for row in self.api("search", order="date", regionCode=conf.youtube_region, topicId=self.topic_id[cat.lower()], type="video"):
                entries.append( self.wrap3(row, {"genre": cat}) )

        # My Channels
        # - searches channel id for given title
        # - iterates over playlist
        # - then over playlistitems to get videos
        elif cat in channels:
            # channel id, e.g. UCEmCXnbNYz-MOtXi3lZ7W1Q
            UC = self.channel_id(cat)
            
            # playlist
            for i,playlist in enumerate(self.api("playlists", fields="items(id,snippet/title)", channelId=UC, maxResults=15)):

                # items (videos)
                for row in self.api("playlistItems", playlistId=playlist["id"], fields="items(snippet(title,resourceId/videoId,description))"):
                    entries.append(self.wrap3(row, {"genre": cat, "playing": playlist["snippet"]["title"]}))

                self.update_streams_partially_done(entries)
                self.parent.status(i / 15.0)
            
        
        # empty entries
        else:
            entries = [dict(title="Placeholder for subcategories", genre="./.", playing="./.", url="http://youtube.com/")]
 
        # done    
        return entries
        

    
    # Search for channel name:
    def channel_id(self, title):
        id = self.channel2id.get(title)
        if not id:
            data = self.api("search", part="id", type="channel", q=title)
            if data:
                id = data[0]["id"]["channelId"]
        self.channel2id[title] = id
        return id
    channel2id = {}



    #-- Retrieve Youtube API query results
    #
    def api(self, method, ver=3, pages=5, **params):
        items = []

        # URL and default parameters
        (base_url, defaults) = self.service[ver]
        params = dict( list(defaults.items()) + list(params.items())  )

        # Retrieve data set
        while pages > 0:
            j = ahttp.get(base_url + method, params=params)
            #__print__(dbg.DATA, j)
            if j:
                # json decode
                data = json.loads(j)
                
                # extract items
                if "items" in data:
                    items += data["items"]
                elif "feed" in data:
                    items += data["feed"]["entry"]
                else:
                    pages = 0

            # Continue to load results?
            if len(items) >= int(conf.max_streams):
                pages = 0
            elif "pageInfo" in data and data["pageInfo"]["totalResults"] < 50:
                pages = 0
            elif "nextPageToken" in data:
                params["pageToken"] = data["nextPageToken"]
                pages -= 1
            else:
                pages = 0
            self.parent.status( (10 - 1.852 * pages) / 10.5 )

        return items



    # Wrap API 3.0 result into streams row
    def wrap3(self, row, data):

        # Video id
        if "id" in row:
            # plain /video queries
            id = row["id"]
            # for /search queries
            if type(row["id"]) is dict:
                id = id["videoId"]
        # for /playlistItems
        elif "resourceId" in row["snippet"]:
            id = row["snippet"]["resourceId"]["videoId"]

        data.update(dict(
            url = "http://youtube.com/v/" + id,
            homepage = "http://youtu.be/" + id + ("?wadsworth=1" if conf.youtube_wadsworth else ""),
            format = self.fmt,
            title = row["snippet"]["title"],
        ))
        
        # optional values
        if "playing" not in data:
            data["playing"] = row["snippet"]["channelTitle"]
        if "description" in row["snippet"]:
            data["description"] = row["snippet"]["description"],

        return data


    # API version 2.0s jsonified XML needs different unpacking:
    def wrap2(self, row):
        #__print__(dbg.DATA, row)
        return dict(
            genre = row["category"][1]["term"],
            title = row["title"]["$t"],
            playing = row["author"][0]["name"]["$t"],
            format = self.fmt,
            url = row["content"]["src"].split("?")[0],
            homepage = row["media$group"]["media$player"]["url"],
            image = row["media$group"]["media$thumbnail"][0]["url"],
        )



