
# encoding: UTF-8
# api: streamtuner2
# type: functions
# title: play/record actions
# description: Starts audio applications, guesses MIME types for URLs
# version: 0.9
#
# Multimedia interface for starting audio players, recording app,
# or web browser (listed as "url/http" association in players).
#
# Each channel plugin has a .listtype which describes the linked
# audio playlist format. It's audio/x-scpls mostly, seldomly m3u,
# but sometimes url/direct if the entry[url] directly leads to the
# streaming server.
#
# As fallback there is a regex which just looks for URLs in the
# given resource (works for m3u/pls/xspf/asx/...).


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
    "video/x-ms-asf":       "asx",
    "application/xspf+xml": "xspf",
    "*/*":                  "href",  # "href" for unknown responses
    "url/direct":           "srv",
    "url/youtube":          "href",
    "url/http":             "href",
    "audio/x-pn-realaudio": "ram",
    "application/smil":     "smil",
    "application/vnd.ms-wpl":"smil",
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
    srv = "(%srv | %d | %s) \\b",
)

# Playlist format content probing (assert type)
playlist_content_map = [
   ("pls",  r""" (?i)\[playlist\].*numberofentries """),
   ("xspf", r""" <\?xml .* <playlist .* http://xspf\.org/ns/0/ """),
   ("m3u",  r""" ^ \s* #(EXT)?M3U """),
   ("asx" , r""" <ASX\b """),
   ("smil", r""" <smil[^>]*> .* <seq> """),
   ("html", r""" <(audio|video)\b[^>]+\bsrc\s*=\s*["']?https?:// """),
   ("wpl",  r""" <\?wpl \s+ version="1\.0" \s* \?> """),
   ("b4s",  r""" <WinampXML> """),   # http://gonze.com/playlists/playlist-format-survey.html
   ("jspf", r""" ^ \s* \{ \s* "playlist": \s* \{ """),
   ("json", r""" "url": \s* "\w+:// """),
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
    cmd = interpol(cmd, url, listformat, row)
    run(cmd)


# Call streamripper
#
def record(url, audioformat="audio/mpeg", source="href", row={}):
    cmd = mime_app(audioformat, conf.record)
    cmd = interpol(cmd, url, listformat, row)
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
def convert_playlist(url, source, dest, local_file=True, title=""):
    urls = []
    debug(dbg.PROC, "convert_playlist(", url, source, dest, ")")

    # Leave alone if format matches, or if "srv" URL class, or if it's a local path already
    if source == dest or source in ("srv", "href") or not re.search("\w+://", url):
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
    for fmt in [ "pls", "asx", "raw" ]:
        if not urls and fmt in (source, mime, probe, ext):
            urls = extract_playlist(source).format(fmt)
            debug(dbg.DATA, "conversion from:", source, " to dest:", fmt, "got URLs=", urls)
            
    # Return original, or asis for srv targets
    if not urls:
        return [url]
    elif dest in ("srv", "href"):
        return urls
    debug( urls )

    # Otherwise convert to local file
    if local_file:
        fn = tmp_fn(cnt)
        save_playlist(source="srv", multiply=True).export(urls=urls, fn=fn, dest=dest, title=title)
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
    # Map MIME to abbr type (pls, m3u, xspf)
    if listfmt_t.get(mime):
        mime = listfmt_t.get(mime)
    # Raw content (mp3, flv)
    elif mimefmt_t.get(mime):
        mime = mimefmt_t.get(mime)
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
    def format(self, fmt):
        cnv = getattr(self, fmt)
        return cnv()

    # PLS
    def pls(self):
        return re.findall("\s*File\d*\s*=\s*(\w+://[^\s]+)", self.src, re.I)

    # ASX
    def asx(self):
        return re.findall("<Ref\s+href=\"(http://.+?)\"", self.src)

    # Regexp out any URL
    def raw(self):
        debug(dbg.WARN, "Raw playlist extraction")
        return re.findall("([\w+]+://[^\s\"\'\>\#]+)", self.src)


# Save rows in one of the export formats.
# Takes a few combinations of parameters (either rows[], or urls[]+title),
# because it's used by playlist_convert() as well as the station saving.
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
        return self.store(rows, None, dest)


    # Export a playlist
    def store(self, rows=None, fn=None, dest="pls"):
    
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
        txt = converter(rows)
        
        # save directly?
        if fn:
            with open(fn, "wb") as f:
                f.write(txt)
        else:
            return txt


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


#-- all others need rework --

    # XSPF
    def xspf(self, rows):
        txt = '<?xml version="1.0" encoding="UTF-8"?>' + "\n"
        txt += '<?http header="Content-Type: application/xspf+xml" ?>' + "\n"
        txt += '<playlist version="1" xmlns="http://xspf.org/ns/0/">' + "\n"
        txt += "  <trackList>\n"
        for row in rows:
            for attr,tag in [("title","title"), ("homepage","info"), ("playing","annotation"), ("description","annotation")]:
                if rows.get(attr):
                    txt += "  <"+tag+">" + xmlentities(row[attr]) + "</"+tag+">\n"
            u = row.get("url")
            txt += '	<track><location>' + xmlentities(u) + '</location></track>' + "\n"
        txt += "  </trackList>\n</playlist>\n"

    # JSPF
    def jspf(self, rows):
        pass
    # ASX
    def asx(self, rows):
        for row in rows:
          txt = "<ASX version=\"3.0\">\n"			\
            + " <Title>" + xmlentities(row["title"]) + "</Title>\n"	\
            + " <Entry>\n"				\
            + "  <Title>" + xmlentities(row["title"]) + "</Title>\n"	\
            + "  <MoreInfo href=\"" + row["homepage"] + "\"/>\n"	\
            + "  <Ref href=\"" + stream_urls[0] + "\"/>\n"		\
            + " </Entry>\n</ASX>\n"
        return txt

    # SMIL
    def smil(self, rows):
        return "<smil>\n<head>\n  <meta name=\"title\" content=\"" + xmlentities(row["title"]) + "\"/>\n</head>\n"	\
             + "<body>\n  <seq>\n    <audio src=\"" + stream_urls[0] + "\"/>\n  </seq>\n</body>\n</smil>\n"



# generate filename for temporary .m3u, if possible with unique id
def tmp_fn(pls):
    # use shoutcast unique stream id if available
    stream_id = re.search("http://.+?/.*?(\d+)", pls, re.M)
    stream_id = stream_id and stream_id.group(1) or "XXXXXX"
    try:
        channelname = main.current_channel
    except:
        channelname = "unknown"
    return (str(conf.tmp) + os.sep + "streamtuner2."+channelname+"."+stream_id+".m3u", len(stream_id) > 3 and stream_id != "XXXXXX")

    

