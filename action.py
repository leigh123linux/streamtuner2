# encoding: UTF-8
# api: streamtuner2
# type: functions
# cagtegory: io
# title: play/record actions
# description: Starts audio applications, guesses MIME types for URLs
# version: 0.9
# priority: core
#
# Multimedia interface for starting audio players, recording app,
# or web browser (listed as "url/http" association in players).
# It maps audio MIME types, and extracts/converts playlist types
# (PLS, M3U, XSPF, SMIL, JSPF, ASX, raw urls).
#
# Each channel plugin has a .listtype which defines the linked
# audio playlist format. It's "pls", seldomly "m3u", or "xspf".
# Some channels list raw "srv" addresses, while Youtube "href"
# entries point to Flash videos.
#
# As fallback the playlist URL is retrieved and its MIME type
# checked, then its content regexped to guess the list format.
# Lastly a playlist format suitable for audio players recreated.
# Which is somewhat of a security feature; playlists get cleaned
# up this way. The conversion is not strictly necessary for all
# players, as basic PLS/M3U is supported by most.
#
# And finally this module is also used by exporting and (perhaps
# in the future) playlist importing features (e.g. in DND hooks).
#
# Still needs some rewrites to transition off the [url] lists,
# and work with full [rows] primarily. (And perhaps it should be
# renamed to "playlist" module now).


import re
import os
from ahttp import fix_url as http_fix_url, session
from config import *
import platform
import copy
import json
from datetime import datetime
from xml.sax.saxutils import escape as xmlentities, unescape as xmlunescape


# Coupling to main window
#
main = None


# Streamlink/listformat mapping
listfmt_t = {
    "audio/x-scpls":        "pls",
    "audio/x-mpegurl":      "m3u",
    "audio/mpegurl":        "m3u",
    "application/vnd.apple.mpegurl": "m3u",
    "video/x-ms-asf":       "asx",
    "application/xspf+xml": "xspf",
    "*/*":                  "href",  # "href" for unknown responses
    "url/direct":           "srv",
    "url/youtube":          "href",
    "url/http":             "href",
    "audio/x-pn-realaudio": "ram",
    "application/json":     "json",
    "application/smil":     "smil",
    "application/vnd.ms-wpl":"smil",
    "audio/x-ms-wax":       "asx",
    "video/x-ms-asf":       "asx",
    "x-urn/st2-script":     "script", # unused
    "application/x-shockwave-flash": "href",  # fallback
}

# Audio type MIME map
mediafmt_t = {
    "audio/mpeg":   "mp3",
    "audio/ogg":    "ogg",
    "audio/aac" :   "aac",
    "audio/aacp" :  "aac",
    "audio/midi":   "midi",
    "audio/mod":    "mod",
    "audio/it+zip": "mod",
    "audio/s3+zip": "mod",
    "audio/xm+zip": "mod",
}

# Player command placeholders for playlist formats
placeholder_map = dict(
    pls = "(%url | %pls | %u | %l | %r) \\b",
    m3u = "(%m3u | %f | %g | %m) \\b",
    xspf= "(%xspf | %xpsf | %x) \\b",
    jspf= "(%jspf | %j) \\b",
    asx = "(%asx) \\b",
    smil= "(%smil) \\b",
    srv = "(%srv | %d | %s) \\b",
)

# Playlist format content probing (assert type)
playlist_content_map = [
   ("pls",  r""" (?i)\[playlist\].*NumberOfEntries """),
   ("xspf", r""" <\?xml .* <playlist .* ((?i)http://xspf\.org)/ns/0/ """),
   ("m3u",  r""" ^ \s* \#(EXT)?M3U """),
   ("asx" , r""" <asx\b """),
   ("smil", r""" <smil[^>]*> .* <seq> """),
   ("html", r""" (?i)<(audio|video)\b[^>]+\bsrc\s*=\s*["']?https?:// """),
   ("wpl",  r""" <\?wpl \s+ version="1\.0" \s* \?> """),
   ("b4s",  r""" <WinampXML> """),   # http://gonze.com/playlists/playlist-format-survey.html
   ("jspf", r""" ^ \s* \{ \s* "playlist": \s* \{ """),
   ("asf",  r""" ^ \[Reference\] .*? ^Ref\d+= """),
   ("url",  r""" ^ \[InternetShortcut\] .*? ^URL= """),
("desktop", r""" ^ \[Desktop Entry\] .*? ^Link= """),
   ("json", r""" "url": \s* "\w+:\\?/\\?/ """),
   ("jamj", r""" "audio": \s* "\w+:\\?/\\?/ """),
   ("gvp",  r""" ^gvp_version:1\.\d+$ """),
   ("href", r""" .* """),
]

# Preferred probing order of known formats
playlist_fmt_prio = [
   "pls", "xspf", "asx", "smil", "jamj", "json", "m3u", "asf", "raw"
]



# Exec wrapper
#
def run(cmd):
    log.PROC("Exec:", cmd)
    try:    os.system("start \"%s\"" % cmd if conf.windows else cmd + " &")
    except: log.ERR("Command not found:", cmd)


# Start web browser
#
def browser(url):
    bin = conf.play.get("url/http", "sensible-browser")
    log.BROWSER(bin)
    run(bin + " " + quote(url))


# Open help browser, streamtuner2 pages
#
def help(*args):
    run("yelp /usr/share/doc/streamtuner2/help/")


# Calls player for stream url and format
#
def play(row={}, audioformat="audio/mpeg", source="pls", url=None):
    cmd = mime_app(audioformat, conf.play)
    cmd = interpol(cmd, url or row["url"], source, row)
    run(cmd)


# Call streamripper
#
def record(row={}, audioformat="audio/mpeg", source="href", url=None):
    cmd = mime_app(audioformat, conf.record)
    cmd = interpol(cmd, url or row["url"], source, row)
    run(cmd)


# OS shell command escaping
#
def quote(ins):
    if type(ins) is list:
        return " ".join(["%r" % str(s) for s in ins])
    else:
        return "%r" % str(ins)


# Convert e.g. "text/x-scpls" MIME types to just "pls" monikers
#
def listfmt(t = "pls"):
    return listfmt_t.get(t, t) # e.g. "pls" or still "text/x-unknown"


# Convert MIME type into list of ["audio/xyz", "audio/*", "*/*"]
# for comparison against configured record/play association.
def mime_app(fmt, cmd_list):
    major = fmt[:fmt.find("/")]
    for match in [ fmt, major + "/*", "*/*" ]:
        if cmd_list.get(match):
            return cmd_list[match]



# Replaces instances of %m3u, %pls, %srv in a command string.
#  · Also understands short aliases %l, %f, %d.
#  · And can embed %title or %genre placeholders.
#  · Replace .pls URL with local .m3u file depending on map.
#
def interpol(cmd, url, source="pls", row={}):

    # inject other meta fields
    row = copy.copy(row)
    if row:
        for field in row:
            cmd = cmd.replace("%"+field, "%r" % row.get(field))

    # add default if cmd has no %url placeholder
    if cmd.find("%") < 0:
        cmd = cmd + " %pls"
        # "pls" as default requires no conversion for most channels, and seems broadly supported by players

    # standard placeholders
    for dest, rx in placeholder_map.items():
        if re.search(rx, cmd, re.X):
            # from .pls to .m3u
            fn_or_urls = convert_playlist(url, listfmt(source), listfmt(dest), local_file=True, row=row)
            # insert quoted URL/filepath
            return re.sub(rx, quote(fn_or_urls), cmd, 2, re.X)

    return "false"


# Substitute .pls URL with local .m3u, or direct srv addresses, or leaves URL asis.
#  · Takes a single input `url` (and original row{} as template).
#  · But returns a list of [urls] after playlist extraction.
#  · If repackaging as .m3u/.pls/.xspf, returns the local [fn].
#
def convert_playlist(url, source, dest, local_file=True, row={}):
    urls = []
    log.PROC("convert_playlist(", url, source, dest, ")")

    # Leave alone if format matches, or if already "srv" URL, or if not http (local path, mms:/rtsp:)
    if source == dest or source in ("srv", "href") or not re.match("(https?|spdy)://", url):
        return [url]
    
    # Retrieve from URL
    (mime, cnt) = http_probe_get(url)
    
    # Leave streaming server as is
    if mime == "srv":
        cnt = ""
        return [url]

    # Deduce likely content format
    cnv = extract_playlist(cnt)
    ext = cnv.probe_ext(url)
    probe = cnv.probe_fmt()

    # Check ambiguity (except pseudo extension)
    if len(set([source, mime, probe])) > 1:
        log.ERR("Possible playlist format mismatch:", "listformat={}, http_mime={}, rx_probe={}, ext={}".format(source, mime, probe, ext))

    # Extract URLs from content
    for fmt in playlist_fmt_prio:
        if not urls and fmt in (source, mime, probe, ext, "raw"):
            urls = cnv.urls(fmt)
            log.DATA("conversion from:", source, " with extractor:", fmt, "got URLs=", urls)
            
    # Return original, or asis for srv targets
    if not urls:
        return [url]
    elif dest in ("srv", "href"):
        return urls

    # Otherwise convert to local file
    if local_file:
        fn, is_unique = tmp_fn(cnt, dest)
        with open(fn, "w") as f:
            log.DATA("exporting with format:", dest, " into filename:", fn)
            f.write( save_playlist(source="srv", multiply=True).export(urls, row, dest) )
        return [fn]
    else:
        return urls



# Tries to fetch a resource, aborts on ICY responses.
#
def http_probe_get(url):

    # HTTP request, abort if streaming server hit (no HTTP/ header, but ICY/ response)
    try:
        r = session.get(url, stream=True, timeout=5.0)
        if not len(r.headers):
            return ("srv", r)
    except:
        return ("srv", None)

    # Extract payload
    mime = r.headers.get("content-type", "href")
    mime = mime.split(";")[0].strip()

    # Map MIME to abbr type (pls, m3u, xspf)
    if listfmt_t.get(mime):
        mime = listfmt_t.get(mime)
    # Raw content (mp3, flv)
    elif mediafmt_t.get(mime):
        log.ERR("Got media MIME type for expected playlist", mime, " on url=", url)
        mime = mediafmt_t.get(mime)
        return (mime, url)

    # Rejoin into string
    content = "\n".join(str.decode(errors='replace') for str in r.iter_lines())
    return (mime, content)



# Extract URLs from playlist formats:
#
# It's entirely regex-based at the moment, because that's more
# resilient against mailformed XSPF or JSON.
# Needs proper extractors later for real playlist *imports*.
#
class extract_playlist(object):

    # Content of playlist file
    src = ""
    fn = ""
    def __init__(self, text=None, fn=None):
        # Literal playlist source content
        if text:
            self.src = text
        # Only read filename if it matches allowed extension
        if fn and self.probe_ext(fn):
            self.fn = fn
            self.src = open(fn, "rt").read()


    # Test URL/path "extension" for ".pls" / ".m3u" etc.
    def probe_ext(self, url):
        e = re.findall("\.(pls|m3u|xspf|jspf|asx|wpl|wsf|smil|html|url|json|desktop)$", url)
        if e: return e[0]
        else: pass


    # Probe MIME type and content per regex
    def probe_fmt(self):
        for probe,rx in playlist_content_map:
            if re.search(rx, self.src, re.X|re.S):
                return listfmt(probe)
        return None

    # Return just URL list from extracted playlist
    def urls(self, fmt):
        return [row["url"] for row in self.rows(fmt)]
        
    # Extract only URLs from given source type
    def rows(self, fmt=None):
        if not fmt:
            fmt = self.probe_fmt()
        log.DATA("input extractor/regex:", fmt, len(self.src))

        # specific extractor implementations
        if fmt in self.__dict__:
            return getattr(self, fmt)()

        # regex scheme
        rules = self.extr_urls[fmt]
        rows = []
        fields = [name for name in ("url", "title", "homepage", "genre", "playing") if rules.get(name)]

        # Block-wise processing
        if rules.get("split"):
            for part_src in re.split(rules["split"], self.src, re.X):
                row = {}
                for name in fields:
                    val = self.field(name, rules, part_src)
                    if val and val[0]:
                        row[name] = val[0]
                if row.get("url"):
                    rows.append(row)
            log.DATA("split-rx", rows)
        
        # Just associate each found url+title in pairs
        else:
            for name in fields:
                for i,val in enumerate(self.field(name, rules, self.src)):
                    if len(rows) <= i:
                        rows.append({"url":None})
                    rows[i][name] = val;
            log.DATA("pair-rx", rows)

        return self.uniq(rows)

    # Single field
    def field(self, name, rules, src_part):
        if name in rules:
            vals = re.findall(rules[name], src_part, re.X)
            #log.PLS_EXTR_FIELD(name, vals, src_part, rules[name])
            return [self.decode(val, rules.get("unesc")) for val in vals]
        return [None]

    # Decoding
    def decode(self, val, unesc):
        if unesc in ("xml", "*"):
            val = xmlunescape(val)
        if unesc in ("json", "*"):
            val = val.replace("\\/", "/")
        return val

    # filter out duplicate urls
    def uniq(self, rows):
        seen = []
        filtered = []
        for row in rows:
            if not row or not row.get("url") or row.get("url") in seen:
                continue;
            seen.append(row.get("url"))
            filtered.append(row)
        return rows


    # These regexps only look out for URLs, not local file paths.
    extr_urls = {
        "pls": dict(
            url   = r"(?im) ^ \s*File\d* \s*=\s* (\w+://[^\s]+) ",
            title = r"(?m) ^Title\d*=(.+)",
            # Notably this extraction method assumes the entries are grouped in associative order
        ),
        "m3u": dict(
            split = r"(?m) (?=^\#)",
            url   = r"(?m) ^( \w+:// [^#\n]+ )",
            title = r"(?m) ^ \#EXTINF [-:\d,]* (.+)",
        ),
        "xspf": dict(
            split = r"(?x) <track[^>]*>",
            url   = r"(?x) <location> (\w+://[^<>\s]+) </location> ",
            title = r"(?x) <title> ([^<>]+) ",
            homepage = r"(?x) <info> ([^<>]+) ",
            playing  = r"(?x) <annotation> ([^<>]+) ",
            unesc = "xml",
        ),
        "asx": dict(
            split = r" (?x) <entry[^>]*> ",
            url   = r" (?x) <ref \b[^>]+\b href \s*=\s* [\'\"] (\w+://[^\s\"\']+) [\'\"] ",
            title = r"(?x) <title> ([^<>]+) ",
            unesc = "xml",
        ),
        "smil": dict(
            url   = r" (?x) <(?:audio|video|media)\b [^>]+ \b src \s*=\s* [^\"\']? \s* (\w+://[^\"\'\s\>]+) ",
            unesc = "xml",
        ),
        "jspf": dict(
            split = r"(?s) \"track\":\s*\{ >",
            url   = r"(?s) \"location\" \s*:\s* \"(\w+://[^\"\s]+)\" ",
            unesc = "json",
        ),
        "jamj": dict(
            url   = r" (?x) \"audio\" \s*:\s* \"(\w+:\\?/\\?/[^\"\s]+)\" ",
            title = r" (?x) \"name\" \s*:\s* \"([^\"]+)\" ",
            unesc = "json",
        ),
        "json": dict(
            url   = r" (?x) \"url\" \s*:\s* \"(\w+:\\?/\\?/[^\"\s]+)\" ",
            title = r" (?x) \"title\" \s*:\s* \"([^\"]+)\" ",
            unesc = "json",
        ),
        "asf": dict(
            url   = r" (?m) ^ \s*Ref\d+ = (\w+://[^\s]+) ",
            unesc = "xml",
        ),
        "url": dict(
            url   = r"(?m) ^URL=(\w+://.+)",
        ),
        "desktop": dict(
            url   = r"(?m) ^URL=(\w+://.+)",
            title = r"(?m) ^Name=(.+)",
            genre = r"(?m) ^Categories=(.+)",
          playing = r"(?m) ^Comment=(.+)",
        ),
        "raw": dict(
            url   = r" (?i) ( [\w+]+:// [^\s\"\'\>\#]+ ) ",
            title = r"(?i)Title[\W]+(.+)",
            unesc = "*",
        ),
    }


    # Add placeholder fields to extracted row
    def mkrow(self, row, title=None):
        url = row.get("url", "")
        comb = {
            "title": row.get("title") or re.sub("\.\w+$", "", os.path.basename(self.fn)),
            "playing": "",
            "url": None,
            "homepage": "",
            "listformat": self.probe_ext(url) or "href", # or srv?
            "format": self.mime_guess(url),
            "genre": "copy",
        }
        comb.update(row)
        return comb

    # Probe url "extensions" for common media types
    # (only care about the common audio formats, don't need an exact match or pre-probing in practice)
    def mime_guess(self, url):
        audio = re.findall("(ogg|opus|spx|aacp|aac|mpeg|mp3|m4a|mp2|flac|midi|mod|kar|aiff|wma|ram|wav)", url)
        if audio:
            return "audio/{}".format(*audio)
        video = re.findall("(mp4|flv|avi|mp2|theora|3gp|nsv|fli|ogv|webm|mng|mxu|wmv|mpv|mkv)", url)
        if audio:
            return "video/{}".format(*audio)
        return "x-audio-video/unknown"



# Save rows in one of the export formats.
#
# The export() version uses urls[]+row/title= as input, converts it into
# a list of rows{} beforehand.
#
# While store() requires rows{} to begin with, to perform a full
# conversion. Can save directly to a file name.
#
class save_playlist(object):

    # if converting
    source = "pls"
    # expand multiple server URLs into duplicate entries in target playlist
    multiply = True
    # constructor
    def __init__(self, source, multiply):
        self.source = source
        self.multiply = multiply
    

    # Used by playlist_convert(), to transform a list of extracted URLs
    # into a local .pls/.m3u collection again. Therefore injects the
    # `title` back into each of the URL rows / or uses row{} template.
    def export(self, urls=[], row={}, dest="pls", title=None):
        row["title"] = row.get("title", title or "unnamed stream")
        rows = []
        for url in urls:
            row.update(url=url)
            rows.append(row)
        return self.store(rows, dest)

    # Export a playlist from rows{}
    def store(self, rows=None, dest="pls"):
    
        # can be just a single entry
        rows = copy.deepcopy(rows)
        if type(rows) is dict:
            rows = [row]

        # Expand contained stream urls
        if not self.source in ("srv", "raw", "asis"):
            new_rows = []
            for i,row in enumerate(rows):
                # Preferrably convert to direct server addresses
                for url in convert_playlist(row["url"], self.source, "srv", local_file=False):
                    row = dict(row.items())
                    row["url"] = url
                    new_rows.append(row)
                    # Or just allow one stream per station in a playlist entry
                    if not self.multiply:
                        break
            rows = new_rows

        log.DATA("conversion to:", dest, "  with rows=", rows)

        # call conversion schemes
        converter = getattr(self, dest) or self.pls
        return converter(rows)

    # save directly
    def file(self, rows, dest, fn):
        with open(fn, "w") as f:
            f.write(self.store(rows, dest))
    
    

    # M3U
    def m3u(self, rows):
        txt = "#EXTM3U\n"
        for r in rows:
            txt += "#EXTINF:-1,%s\n" % r["title"]
            txt += "%s\n" % http_fix_url(r["url"])
        return txt

    # PLS
    def pls(self, rows):
        txt = "[playlist]\n" + "NumberOfEntries=%s\n" % len(rows)
        for i,r in enumerate(rows):
            txt += "File%s=%s\nTitle%s=%s\nLength%s=%s\n" % (i+1, r["url"], i+1, r["title"], i+1, -1)
        txt += "Version=2\n"
        return txt

    # JSON (native lists of streamtuner2)
    def json(self, rows):
        return json.dumps(rows, indent=4)


    # XSPF
    def xspf(self, rows):
        return """<?xml version="1.0" encoding="UTF-8"?>\n"""				\
            + """<?http header="Content-Type: application/xspf+xml; x-ns='http://xspf.org/ns/0/'; x-gen=streamtuner2" ?>\n"""	\
            + """<playlist version="1" xmlns="http://xspf.org/ns/0/">\n"""		\
            + """\t<date>%s</date>\n\t<trackList>\n""" % datetime.now().isoformat()	\
            + "".join("""\t\t<track>\n%s\t\t</track>\n""" % self.xspf_row(row, self.xspf_map) for row in rows)	\
            + """\t</trackList>\n</playlist>\n"""
    # individual tracks
    def xspf_row(self, row, map):
        return "".join("""\t\t\t<%s>%s</%s>\n""" % (tag, xmlentities(row[attr]), tag) for attr,tag in map.items() if row.get(attr))
    # dict to xml tags
    xspf_map = dict(title="title", url="location", homepage="info", playing="annotation", description="info")


    # JSPF
    def jspf(self, rows):
        tracks = []
        for row in rows:
            tracks.append( { tag: row[attr] for attr,tag in self.xspf_map.items() if row.get(attr) } )
        return json.dumps({ "playlist": { "track": tracks } }, indent=4)


    # ASX
    def asx(self, rows):
        txt = """<asx version="3.0">\n"""
        for row in rows:
            txt += """\t<entry>\n\t\t<title>%s</title>\n\t\t<ref href="%s"/>\n\t</entry>\n""" % (xmlentities(row["title"]), xmlentities(row["url"]))
        txt += """</asx>\n"""
        return txt


    # SMIL
    def smil(self, rows):
        txt = """<smil>\n<head>\n\t<meta name="title" content="%s"/>\n</head>\n<body>\n\t<seq>\n""" % (rows[0]["title"])
        for row in rows:
            if row.get("url"):
                txt += """\t\t<{} src="{}"/>\n""".format(row.get("format", "audio").split("/")[0], row["url"])
        txt += """\t</seq>\n</body>\n</smil>\n"""
        return txt

    # .DESKTOP links
    def desktop(self, rows):
        row = rows[0]
        return "[Desktop Entry]\nVersion=1.0\nIcon=media-playback-start\nType=Link\nName={title}\nComment={playing}\nURL={url}\n".format(**row)



# Generate filename for temporary .m3u, if possible with unique id
def tmp_fn(pls, ext="m3u"):
    # use shoutcast unique stream id if available
    stream_id = re.search("http://.+?/.*?(\d+)", pls, re.M)
    stream_id = stream_id and stream_id.group(1) or "XXXXXX"
    try:
        channelname = main.current_channel
    except:
        channelname = "unknown"
    # return temp filename
    fn = "%s/streamtuner2.%s.%s.%s" % (str(conf.tmp), channelname, stream_id, ext)
    is_unique = len(stream_id) > 3 and stream_id != "XXXXXX"
    tmp_files.append(fn)
    return fn, is_unique

# Collect generated filenames
tmp_files = []

# Callback from main / after gtk_main_quit
def cleanup_tmp_files():
    if not int(conf.reuse_m3u):
        [os.remove(fn) for fn in set(tmp_files)]

