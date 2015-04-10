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
# entries to Flash videos.
#
# As fallback the playlist URL is retrieved and its MIME type
# checked, and its content regexped to guess the link format.
# Lastly a playlist type suitable for audio players recreated.
# Which is somewhat of a security feature, playlists get cleaned
# up this way. The conversion is not strictly necessary for all
# players, as basic PLS is supported by most.
#
# And finally this module is also used by exporting and (perhaps
# in the future) playlist importing features.


import re
import os
from ahttp import fix_url as http_fix_url, session
from config import conf, __print__ as debug, dbg
import platform
import copy
import json


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
   ("pls",  r""" (?i)\[playlist\].*numberofentries """),
   ("xspf", r""" <\?xml .* <playlist .* http://xspf\.org/ns/0/ """),
   ("m3u",  r""" ^ \s* #(EXT)?M3U """),
   ("asx" , r""" <asx\b """),
   ("smil", r""" <smil[^>]*> .* <seq> """),
   ("html", r""" <(audio|video)\b[^>]+\bsrc\s*=\s*["']?https?:// """),
   ("wpl",  r""" <\?wpl \s+ version="1\.0" \s* \?> """),
   ("b4s",  r""" <WinampXML> """),   # http://gonze.com/playlists/playlist-format-survey.html
   ("jspf", r""" ^ \s* \{ \s* "playlist": \s* \{ """),
   ("asf",  r""" ^ \[Reference\] .*? ^Ref\d+= """),
   ("json", r""" "url": \s* "\w+:// """),
   ("gvp",  r""" ^gvp_version:1\.\d+$ """),
   ("href", r""" .* """),
]



# Exec wrapper
#
def run(cmd):
    debug(dbg.PROC, "Exec:", cmd)
    try:    os.system("start \"%s\"" % cmd if conf.windows else cmd + " &")
    except: debug(dbg.ERR, "Command not found:", cmd)


# Start web browser
#
def browser(url):
    bin = conf.play.get("url/http", "sensible-browser")
    run(bin + " " + quote(url))


# Open help browser, streamtuner2 pages
#
def help(*args):
    run("yelp /usr/share/doc/streamtuner2/help/")


# Calls player for stream url and format
#
def play(url, audioformat="audio/mpeg", source="pls", row={}):
    cmd = mime_app(audioformat, conf.play)
    cmd = interpol(cmd, url, source, row)
    run(cmd)


# Call streamripper
#
def record(url, audioformat="audio/mpeg", source="href", row={}):
    cmd = mime_app(audioformat, conf.record)
    cmd = interpol(cmd, url, source, row)
    run(cmd)


# OS shell command escaping
#
def quote(ins):
    if type(ins) is str:
        return "%r" % str(ins)
    else:
        return " ".join(["%r" % str(s) for s in ins])


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
            fn_or_urls = convert_playlist(url, listfmt(source), listfmt(dest), local_file=True, title=row.get("title", ""))
            # insert quoted URL/filepath
            return re.sub(rx, quote(fn_or_urls), cmd, 2, re.X)

    return "false"


# Substitute .pls URL with local .m3u, or direct srv addresses, or leaves URL asis.
#  · Takes a single input `url`.
#  · But returns a list of [urls] after playlist extraction.
#  · If repackaging as .m3u/.pls/.xspf, returns the local [fn].
#
# TODO: This still needs some rewrite to reuse the incoming row={},
# and keep station titles for converted playlists.
#
def convert_playlist(url, source, dest, local_file=True, title=""):
    urls = []
    debug(dbg.PROC, "convert_playlist(", url, source, dest, ")")

    # Leave alone if format matches, or if "srv" URL class, or if not http (local path, mms:/rtsp:)
    if source == dest or source in ("srv", "href") or not re.match("(https?|spdy)://", url):
        return [url]
    
    # Retrieve from URL
    (mime, cnt) = http_probe_get(url)
    
    # Leave streaming server as is
    if mime == "srv":
        cnt = ""
        return [url]

    # Test URL path "extension" for ".pls" / ".m3u" etc.
    ext = re.findall("\.(\w)$", url)
    ext = ext[0] if ext else None

    # Probe MIME type and content per regex
    probe = None
    for probe,rx in playlist_content_map:
        if re.search(rx, cnt, re.X|re.S):
            probe = listfmt(probe)
            break # with `probe` set

    # Check ambiguity (except pseudo extension)
    if len(set([source, mime, probe])) > 1:
        debug(dbg.ERR, "Possible playlist format mismatch:", (source, mime, probe, ext))

    # Extract URLs from content
    for fmt in ["pls", "xspf", "asx", "smil", "jspf", "m3u", "json", "asf", "raw"]:
        if not urls and fmt in (source, mime, probe, ext, "raw"):
            urls = extract_playlist(cnt).format(fmt)
            debug(dbg.DATA, "conversion from:", source, " with extractor:", fmt, "got URLs=", urls)
            
    # Return original, or asis for srv targets
    if not urls:
        return [url]
    elif dest in ("srv", "href"):
        return urls
    debug( urls )

    # Otherwise convert to local file
    if local_file:
        fn, is_unique = tmp_fn(cnt, dest)
        with open(fn, "wb") as f:
            debug(dbg.DATA, "exporting with format:", dest, " into filename:", fn)
            f.write( save_playlist(source="srv", multiply=True).export(urls=urls, dest=dest, title=title) )
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
        debug(dbg.ERR, "Got media MIME type for expected playlist", mime, " on url=", url)
        mime = mediafmt_t.get(mime)
        return (mime, url)
    # Rejoin body
    content = "\n".join(r.iter_lines())
    return (mime, content)



# Extract URLs from playlist formats:
#
class extract_playlist(object):

    # Content of playlist file
    src = ""
    def __init__(self, text):
        self.src = text
        
    # Extract only URLs from given source type
    def format(self, fmt):
        debug(dbg.DATA, "input regex:", fmt, len(self.src))
        return re.findall(self.extr_urls[fmt], self.src, re.X);

    # Only look out for URLs, not local file paths
    extr_urls = {
       "pls":  r"(?im) ^ \s*File\d* \s*=\s* (\w+://[^\s]+) ",
       "m3u":  r" (?m) ^( \w+:// [^#\n]+ )",
       "xspf": r" (?x) <location> (\w+://[^<>\s]+) </location> ",
       "asx":  r" (?x) <ref \b[^>]+\b href \s*=\s* [\'\"] (\w+://[^\s\"\']+) [\'\"] ",
       "smil": r" (?x) <(?:audio|video|media)\b [^>]+ \b src \s*=\s* [^\"\']? \s* (\w+://[^\"\'\s]+) ",
       "jspf": r" (?x) \"location\" \s*:\s* \"(\w+://[^\"\s]+)\" ",
       "json": r" (?x) \"url\" \s*:\s* \"(\w+://[^\"\s]+)\" ",
       "asf":  r" (?m) ^ \s*Ref\d+ = (\w+://[^\s]+) ",
       "raw":  r" (?i) ( [\w+]+:// [^\s\"\'\>\#]+ ) ",
    }


# Save rows in one of the export formats.
#
# The export() version uses urls[]+title= as input, converts it into a
# list of rows{} beforehand.
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
    # `title` back into each of the URL rows.
    def export(self, urls=None, title=None, dest="pls"):
        rows = [ { "url": url, "title": title } for url in urls ]
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
                    row["url"] = url
                    new_rows.append(row)
                    # Or just allow one stream per station in a playlist entry
                    if not self.multiply:
                        break
            rows = new_rows

        debug(dbg.DATA, "conversion to:", dest, " from:", self.source, "with rows=", rows)

        # call conversion schemes
        converter = getattr(self, dest) or self.pls
        return converter(rows)

    # save directly
    def file(self, rows, dest, fn):
        with open(fn, "wb") as f:
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
        txt = "[playlist]\n" + "numberofentries=%s\n" % len(rows)
        for i,r in enumerate(rows):
            txt += "File%s=%s\nTitle%s=%s\nLength%s=%s\n" % (i, r["url"], i, r["title"], i, -1)
        txt += "Version=2\n"
        return txt

    # JSON (native lists of streamtuner2)
    def json(self, rows):
        return json.dumps(rows, indent=4)


    # XSPF
    def xspf(self, rows):
        return """<?xml version="1.0" encoding="UTF-8"?>\n"""					\
            + """<?http header="Content-Type: application/xspf+xml" ?>\n"""			\
            + """<playlist version="1" xmlns="http://xspf.org/ns/0/">\n\t<trackList>\n"""	\
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
        txt = """<smil>\n<head>\n\t<meta name="title" content="%s""/>\n</head>\n<body>\n\t<seq>\n""" % (rows[0]["title"])
        for row in rows:
            if row.get("url"):
                txt += """\t\t<audio src="%s"/>\n""" % row["url"]
        txt += """\t</seq>\n</body>\n</smil>\n"""
        return txt



# Stub import, only if needed
def xmlentities(s):
    global xmlentities
    from xml.sax.saxutils import escape as xmlentities
    return xmlentities(s)



# generate filename for temporary .m3u, if possible with unique id
def tmp_fn(pls, ext="m3u"):
    # use shoutcast unique stream id if available
    stream_id = re.search("http://.+?/.*?(\d+)", pls, re.M)
    stream_id = stream_id and stream_id.group(1) or "XXXXXX"
    try:
        channelname = main.current_channel
    except:
        channelname = "unknown"
    return (str(conf.tmp) + os.sep + "streamtuner2."+channelname+"."+stream_id+"."+ext, len(stream_id) > 3 and stream_id != "XXXXXX")

    

