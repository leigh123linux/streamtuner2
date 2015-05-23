# encoding: UTF-8
# api: streamtuner2
# title: reddit⛱
# description: Music recommendations from reddit /r/music and associated subreddits.
# version: 0.7
# type: channel
# url: http://reddit.com/r/Music
# category: playlist
# config:
#   { name: reddit_pages, type: int, value: 2, description: Number of pages to fetch. }
#   { name: kill_soundcloud, type: boolean, value: 1, description: Filter soundcloud/spotify/bandcamp (only web links). }
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAAJ1BMVEUAAAAcICX/AABHSk1jZ299hYz/bmajq6//lY/d0M3C1+3T7P38+/iaLhuGAAAAAXRSTlMAQObYZgAAAAFiS0dEAIgF
#   HUgAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAHdElNRQffBRUXIyQbWArCAAAAh0lEQVQI12Pg3g0BDLtXrVq1eveq3Qy7gIxCU9dqEGO11/ZKbzBDenUIUM3u7cGi1UDFW0TE55wsdpZikAw/
#   eebMnMmHGVxqDuUc0zzpynD4zIk5J3vOSDNsOQMG1gy7bI5HTq85Ws2wu/jM9PIzrkArdhmXlzuuXg00eVd5+epVqxmgrtgNAOWeS1KYtcY4AAAAAElFTkSuQmCC
# priority: extra
#
# Just imports Youtube links from music-related subreddits.
# Those are usually new bands or fresh releases, or favorite
# user selections. The category/subreddit list is filtered
# for a minimum quote of usable links (namely Youtube URLs,
# Soundcloud/Spotify/Bandcamp and weblinks aren't playable.)
#
# This plugin currently uses the old reddit API, which might
# be obsolete by August. It's thus a temporary channel, as
# migrating to OAuth or regressing to plain HTML extraction
# is not very enticing.


import json
import re
from config import *
from channels import *
import ahttp


# reddit.com
#
# Uses old API requests such as:
#  → http://www.reddit.com/r/music/new.json?sort=new
#
class reddit (ChannelPlugin):

    # control attributes
    has_search = False
    listformat = "srv"
    audioformat = "video/youtube"
    titles = dict(playing="submitter", listeners="votes", bitrate=False)
    
    # just subreddit names to extract from
    categories = [
        # static radio list
        "radioreddit 📟",

        # major subreddits
        "Music",
        ["trueMusic", "futurebeats", "FutureFunkAirlines",
        "Turntablists", "Catchysongs", "MusicForConcentration", "MusicToSleepTo"],

        # cover bands/songs
        "CoverSongs",
        ["ICoveredASong", "MyMusic", "UserProduced", "RepublicOfMusic", "RoyaltyFreeMusic"],

        # discover subreddits
        "music_discovery",
        ["ListenToThis", "ListenToUs", "WhatIListenTo", "ListenToConcerts",
        "HeadBangToThis", "unheardof", "under10k", "lt10k"],
        
        # Classical
        "ClassicalMusic",
        ["composer", "baroque", "classicalmusic", "contemporary",
        "choralmusic", "ChamberMusic", "EarlyMusic",
        "ElitistClassical", "icm", "Opera", "pianocovers"],

        # Electronic Music
        "ElectronicMusic",
        ["acidhouse", "ambientmusic",  "AtmosphericDnB", "BigBeat",
        "boogiemusic", "breakbeat", "breakcore", #"brostep", "chicagohouse",
        "chillout", "Chipbreak", "darkstep", "deephouse",
        "DnB", "DubStep", "EDM", "electronicdancemusic", "ElectronicJazz",
        "ElectronicBlues", "electrohouse", #"electronicmagic",
        "ElectronicMusic", "electropop", "electroswing", #"ExperimentalMusic",
        "fidget", "frenchelectro", "frenchhouse", "funkhouse",
        "futurebeats", "FutureFunkAirlines", "FutureGarage",
        "futuresynth", "gabber", "glitch", "Grime", "happyhardcore",
        "hardhouse", "hardstyle", "house", "idm", "industrialmusic", "ItaloDisco",
        "latinhouse", "LiquidDubstep", "mashups", "minimal", "moombahcore",
        "nightstep", "OldskoolRave", "partymusic", "plunderphonics", "psybient",
        "PsyBreaks", "psytrance", "purplemusic", "raggajungle", "RealDubstep",
        "swinghouse", "tech_house", "Techno", "Trance", "tranceandbass",
        "tribalbeats", "ukfunky", "witchhouse", "wuuB"],

        # Rock / Metal
        "Rock",
        ["80sHardcorePunk", "90sAlternative", "90sPunk", "90sRock",
        "AlternativeRock", "AltCountry", "AORMelodic", "ausmetal",
        "BlackMetal", "bluegrass", "Blues", "bluesrock", "Boneyard",
        "CanadianClassicRock", "CanadianMusic", "ClassicRock", "country",
        "Christcore", "crunkcore", "deathcore", "deathmetal", "Djent", "DoomMetal",
        "Emo", "EmoScreamo", "epicmetal", "flocked", "folk", "folkmetal",
        "folkpunk", "folkrock", "folkunknown", "GaragePunk", "GothicMetal",
        "Grunge", "hardcore", "HardRock", "horrorpunk", "indie_rock", "jrock",
        "krautrock", "LadiesofMetal", "MathRock", "melodicdeathmetal",
        "MelodicMetal", "Metalmusic", "metal", "metalcore",
        "monsterfuzz", "neopsychedelia", "NewWave", "noiserock", "numetal",
        "pianorock", "poppunkers", "PostHardcore", "PostRock", "powermetal",
        "powerpop", "ProgMetal", "progrockmusic", "PsychedelicRock", "punk",
        "Punkskahardcore", "Punk_Rock", "raprock","shoegaze", "stonerrock",
        "symphonicblackmetal", "symphonicmetal", "synthrock", "truethrash",
        "Truemetal", "OutlawCountry", "WomenRock"],

        # hippety-hop
        "HipHopHeads",
        ["80sHipHop", "90sHipHop", "altrap", "asianrap", "backspin", "BayRap",
        "ChapHop", "ChiefKeef", "DrillandBop", "Gfunk", "NYrap",
        "Rap", "raprock", "rhymesandbeats", "trapmuzik"],

        # decades
        "Decades →", ["2010smusic", "2000smusic", "90sMusic", "80sMusic",
        "70s", "70sMusic", "60sMusic", "50sMusic"],

        # By country/region/culture
        "WorldMusic",
        ["AfricanMusic", "afrobeat", "balkanbrass", "balkanmusic", "britpop",
        "Irishmusic", "ItalianMusic", "jpop", "kpop", "spop", "cpop"],

        # Other
        "Genres →",
        ["Acappella", "AcousticCovers", "animemusic", "boomswing",
        "bossanova", "carmusic", "chillmusic",
        "dembow", "disco", "DreamPop", "Elephant6", "ETIMusic", "Exotica",
        "FilmMusic", "FunkSouMusic", "gamemusic", "GamesMusicMixMash",
        "GunslingerMusic", "GypsyJazz", "HomeworkMusic", "IndieFolk",
        "Jazz", "JazzFusion", "JazzInfluence", "listentoconcerts", "klezmer",
        "lt10k", "MedievalMusic", "MelancholyMusic", "minimalism_music", "motown",
        "MovieMusic", "muzyka", "NuDisco", "oldiemusic", "OldiesMusic",
        "pianocovers", "PopMusic", "PoptoRock", "rainymood", #"recordstorefinds",
        "reggae", "remixxd", "RetroMusic", "rnb", "rootsmusic", "SalsaMusic", "Ska",
        "Soca", "Soulies", "SoulDivas", "SoundsVintage", "SpaceMusic",
        "swing", "Tango", "TheRealBookVideos", "TouhouMusic", "TraditionalMusic",
        "treemusic", "triphop", "vaporwave", "VintageObscura", "vocaloid"],

        # Redditor Made Music (removed some spotify/soundcloud-only subreddits)
        "Redditor-Made →",
        ["AcousticOriginals", "Composer", "ICoveredASong",
        "independentmusic", "MusicCritique", "MyMusic",
        "ratemyband", "Songwriters",
        "ThisIsOurMusic", "UserProduced",],

        # Multi-Genre & Community Subreddits (a third cleaned out for too few usable links)
        "Community →",
        ["audioinsurrection", "albumaday", "albumoftheday", #"Albums",
        "albumlisteners", "BinauralMusic", "Catchysongs",
        "CircleMusic", "CoverSongs", "cyberpunk_music", "DANCEPARTY", "danktunes",
        "deepcuts", "EarlyMusic", "FemaleVocalists",
        "FitTunes", "freemusic", "Frisson",
        "GayMusic", "germusic", "gethightothis",
        "GuiltyPleasureMusic", "HeadNodders", "heady", "HeyThatWasIn",
        "indie", "IndieWok", "Instrumentals",
        "ipm", "IsolatedVocals", "LetsTalkMusic", "listentoconcerts",
        "listentomusic", "ListenToThis", "ListenToUs", "livemusic",
        "llawenyddhebddiwedd", "Lyrics", "mainstreammusic",
        "MiddleEasternMusic", "MLPtunes", "Music", "MusicAlbums",
        "musicsuggestions", "MusicToSleepTo", "musicvideos", "NameThatSong",
        "newmusic", "onealbumaweek", "partymusic", "RedditOriginals",
        "RepublicOfMusic", "RoyaltyFreeMusic", "runningmusic",
        "ScottishMusic", "ThemVoices",
        "unheardof", "WhatIListenTo", "WTFMusicVideos"],
        # Community
        #["AlbumArtPorn", "albumreviews", "Audio", "Audiophile", "AustinMusicians",
        #"bandmembers", "CarAV", "CassetteCulture", "Cd_collectors",
        #"ConcertTickets", "germusic", "glastonbury_festival", "ICoveredASong",
        #"ifyoulikeblank", "independentmusic", "ineedasong/", "japanesemusic",
        #"Jazzguitar", "koreanmusic", "LubbockMusicians", "mixcd", "musiccritics",
        #"MusicalComedy", "musicessentials", "MusicEventMeetUp", "musicfestivals",
        #"musicnews", "MusiciansBlogs", "Musicians", "NeedVocals", "OSOM",
        #"performer", "RecordClub", "recordstore", "redditmusicclub", "Rockband",
        #"RockbandChallenges", "TheSongRemainsTheSame", "TipOfMyTongue",
        #"TouringMusicians", "vinyl", "VinylReleases", "WeAreTheMusicMakers"],

        # Single Artist/Band subreddits (unchecked list)
        "Bands/Artists →",
        ["311", "ADTR", "AliciaKeys", "ArcadeFire", "ArethaFranklin",
        "APerfectCircle", "TheAvettBrothers", "BaysideIsACult", "TheBeachBoys",
        "Beatles", "billytalent", "Blink182", "BMSR", "boniver", "brandnew",
        "BruceSpringsteen", "Burial", "ChristinaAguilera", "cityandcolour",
        "Coldplay", "CutCopy", "TheCure", "DaftPunk", "DavidBowie", "Deadmau5",
        "DeathCabforCutie", "DeepPurple", "Deftones", "DieAntwoord", "DMB",
        "elliegoulding", "empireofthesun", "EnterShikari", "Evanescence", "feedme",
        "FirstAidKit", "flaminglips", "franzferdinand", "Gorillaz", "gratefuldead",
        "Greenday", "GunsNRoses", "Incubus", "JackWhite", "JanetJackson",
        "John_frusciante", "kings_of_leon", "Korn", "ladygaga", "lanadelrey",
        "lennykravitz", "Led_Zeppelin", "lorde", "Macklemore", "Madonna", "Manowar",
        "MariahCarey", "MattAndKim", "Megadeth", "Metallica", "MGMT",
        "MichaelJackson", "MinusTheBear", "ModestMouse", "Morrissey",
        "MyChemicalRomance", "Muse", "NeilYoung", "NIN", "Nirvana", "oasis",
        "Opeth", "OFWGKTA(OddFuture)", "OutKast", "panicatthedisco", "PearlJam",
        "phish", "Pinback", "PinkFloyd", "porcupinetree", "prettylights",
        "Puscifer", "Queen", "Radiohead", "RATM", "RedHotChiliPeppers",
        "The_Residents", "RiseAgainst", "Rush", "SigurRos", "Slayer", "slipknot",
        "SmashingPumpkins", "SparksFTW", "TeganAndSara", "TheKillers",
        "TheOffspring", "TheStrokes", "TheMagneticZeros", "tragicallyhip",
        "ToolBand", "U2Band", "Umphreys", "UnicornsMusic", "velvetunderground",
        "Ween", "weezer", "WeirdAl", "yesband", "Zappa"],
    ]


    # static
    def update_categories(self):
        pass


    # Extract video/music news links
    def update_streams(self, cat, search=None):
        
        # radioreddit
        if cat == "radioreddit 📟":
            return self.radioreddit()
        elif cat.find("→") > 0:
            return self.placeholder

        # collect links
        data = []
        after = None
        for i in range(1, int(conf.reddit_pages) + 1):
            try:
                j = ahttp.get(
                    "http://www.reddit.com/r/{}/new.json".format(cat.lower()),
                    { "sort": "new", "after": after }
                )
                j = json.loads(j)
            except Exception as e:
                log.ERR("Reddit down? -", e)
                break
            if j.get("data",{}).get("children"):
                data += j["data"]["children"]
            else:
                break
            if j.get("data",{}).get("after"):
                after = j["data"]["after"]
            else:
                break

        # convert
        r = []
        for row in (ls["data"] for ls in data):

            # find links in text posts
            text_urls = re.findall("\]\((https?://(?:www\.)?youtu[^\"\'\]\)]+)", row.get("selftext", ""))
            url_ext = (re.findall("\.(\w+)$", row["url"]) or [None])[0]
            listformat = "href"
            state = "gtk-media-play"

            # Youtube
            if re.search("youtu", row["url"]):
                format = "video/youtube"
                listformat = "srv"
            # direct MP3/Ogg
            elif url_ext in ("mp3", "ogg", "flac", "aac", "aacp"):
                format = "audio/" + url_ext
                listformat = "srv"
            # playlists?
            elif url_ext in ("m3u", "pls", "xspf"):
                listformat = url_ext
                format = "audio/x-unknown"
            # links from selftext
            elif text_urls:
                row["url"] = text_urls[0]
                format = "video/youtube"
            # filter out Soundcloud etc.
            elif re.search("soundcloud|spotify|bandcamp", row["url"]):
                if conf.kill_soundcloud:
                    continue
                format = "url/http"
                listformat = "srv"
                state = "gtk-media-pause"
            # pure web links etc.
            else:
                continue

            # repack into streams list
            r.append(dict(
                title = row["title"],
                url = row["url"],
                genre = re.findall("\[(.+?)\]", row["title"] + "[-]")[0],
                playing = row["author"],
                listeners = row["score"],
                homepage = "http://reddit.com{}".format(row["permalink"]),
                img = row.get("thumbnail", ""),
                format = format,
                listformat = listformat,
                state = state,
            ))
        return r        


    # static station list
    def radioreddit(self):
        return [
            dict(
                genre=id, title=id.title(),
                url="http://cdn.audiopump.co/radioreddit/"+id+"_mp3_128k",
                format="audio/mpeg", homepage="http://radioreddit.com/",
                listformat="srv"
            )
            for id in [
                "main", "random", "rock", "metal", "indie",
                "electronic", "hiphop", "talk", "festival"
            ]
        ]
    