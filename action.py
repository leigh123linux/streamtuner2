
# encoding: UTF-8
# api: streamtuner2
# type: functions
# title: play/record actions
# description: Starts audio applications, guesses MIME types for URLs
# version: 0.8
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


# Coupling to main window
#
main = None



# Streamlink/listformat mapping
listfmt_t = {
    "audio/x-scpls":        "pls",
    "audio/x-mpegurl":      "m3u",
    "video/x-ms-asf":       "asx",
    "application/xspf+xml": "xspf",
    "*/*":                  "href",
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
def play(url, audioformat="audio/mpeg", listformat="href"):
    cmd = mime_app(audioformat, conf.play)
    cmd = interpol(cmd, url, listformat)
    run(cmd)


# Call streamripper
#
def record(url, audioformat="audio/mpeg", listformat="href", append="", row={}):
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
        cmd = cmd + " %m3u"

    # standard placeholders
    for dest, rx in placeholder_map.items():
        if re.search(rx, cmd, re.X):
            # from .pls to .m3u
            urls = convert_playlist(url, listfmt(source), listfmt(dest))
            # insert quoted URL/filepath
            return re.sub(rx, quote(urls), cmd, 2, re.X)

    return "false"


# Substitute .pls URL with local .m3u,
# or direct srv address, or leave as-is.
#
def convert_playlist(url, source, dest):
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
    ext = ext[0] if ext else ""

    # Probe MIME type and content per regex
    probe = None
    print cnt
    for probe,rx in playlist_content_map:
        if re.search(rx, cnt, re.X|re.S):
            probe = listfmt(probe)
            break # with `probe` set

    # Check ambiguity (except pseudo extension)
    if len(set([source, mime, probe])) > 1:
        debug(dbg.ERR, "Possible playlist format mismatch:", (source, mime, probe, ext))

    # Extract URLs from content
    for fmt,extractor in [ ("pls",extract_playlist.pls), ("asx",extract_playlist.asx), ("raw",extract_playlist.raw) ]:
        if not urls and fmt in (source, mime, probe, ext):
            urls = extractor(cnt)
            debug(fmt, extractor, urls)
            
    # Return original, or asis for srv targets
    if not urls:
        return [url]
    elif dest in ("srv", "href", "any"):
        return urls
    debug( urls )

    # Otherwise convert to local file
    fn = tmp_fn(cnt)
    save(urls[0], fn, dest)
    return [fn]



# Tries to fetch a resource, aborts on ICY responses.
#
def http_probe_get(url):

    # possible streaming request
    r = session.get(url, stream=True)
    if not len(r.headers):
        return ("srv", r)

    # extract payload
    mime = r.headers.get("content-type", "any")
    if listfmt_t.get(mime):
        mime = listfmt_t.get(mime)
    elif mimefmt_t.get(mime):
        mime = mimefmt_t.get(mime)
        return (mime, url)
    content = "\n".join(r.iter_lines())
    return (mime, content)



# Extract URLs from playlist formats:
#
class extract_playlist(object):

    @staticmethod
    def pls(text):
        return re.findall("\s*File\d*\s*=\s*(\w+://[^\s]+)", text, re.I)

    @staticmethod
    def asx(text):
        return re.findall("<Ref\s+href=\"(http://.+?)\"", text)

    @staticmethod
    def raw(text):
        debug(dbg.WARN, "Raw playlist extraction")
        return re.findall("([\w+]+://[^\s\"\'\>\#]+)", content)


# Save row(s) in one of the export formats,
# depending on file extension:
#
#  · m3u
#  · pls
#  · xspf
#  · asx
#  · json
#  · smil
#
def save(row, fn, listformat="audio/x-scpls"):

    # output format
    format = re.findall("\.(m3u|pls|xspf|jspf|json|asx|smil)", fn)

    # modify stream url
    stream_urls = extract_urls(row["url"], listformat)

    # M3U
    if "m3u" in format:
        txt = "#M3U\n"
        for url in stream_urls:
            txt += http_fix_url(url) + "\n"

    # PLS
    elif "pls" in format:
        txt = "[playlist]\n" + "numberofentries=1\n"
        for i,u in enumerate(stream_urls):
            i = str(i + 1)
            txt += "File"+i + "=" + u + "\n"
            txt += "Title"+i + "=" + row["title"] + "\n"
            txt += "Length"+i + "=-1\n"
        txt += "Version=2\n"

    # XSPF
    elif "xspf" in format:
        txt = '<?xml version="1.0" encoding="UTF-8"?>' + "\n"
        txt += '<?http header="Content-Type: application/xspf+xml" ?>' + "\n"
        txt += '<playlist version="1" xmlns="http://xspf.org/ns/0/">' + "\n"
        for attr,tag in [("title","title"), ("homepage","info"), ("playing","annotation"), ("description","annotation")]:
            if row.get(attr):
                txt += "  <"+tag+">" + xmlentities(row[attr]) + "</"+tag+">\n"
        txt += "  <trackList>\n"
        for u in stream_urls:
            txt += '	<track><location>' + xmlentities(u) + '</location></track>' + "\n"
        txt += "  </trackList>\n</playlist>\n"

    # JSPF
    elif "jspf" in format:
        pass

    # JSON
    elif "json" in format:
        row["stream_urls"] = stream_urls
        txt = str(row)   # pseudo-json (python format)
    
    # ASX
    elif "asx" in format:
        txt = "<ASX version=\"3.0\">\n"			\
            + " <Title>" + xmlentities(row["title"]) + "</Title>\n"	\
            + " <Entry>\n"				\
            + "  <Title>" + xmlentities(row["title"]) + "</Title>\n"	\
            + "  <MoreInfo href=\"" + row["homepage"] + "\"/>\n"	\
            + "  <Ref href=\"" + stream_urls[0] + "\"/>\n"		\
            + " </Entry>\n</ASX>\n"

    # SMIL
    elif "smil" in format:
            txt = "<smil>\n<head>\n  <meta name=\"title\" content=\"" + xmlentities(row["title"]) + "\"/>\n</head>\n"	\
                + "<body>\n  <seq>\n    <audio src=\"" + stream_urls[0] + "\"/>\n  </seq>\n</body>\n</smil>\n"

    # unknown
    else:
        return

    # write
    if txt:
        with open(fn, "wb") as f:
            f.write(txt)
    pass



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

    

