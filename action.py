# encoding: UTF-8
# api: streamtuner2
# type: functions
# category: io
# title: play/record actions
# description: Starts audio applications, guesses MIME types for URLs
# version: 1.3
# priority: core
#
# Multimedia interface for starting audio players, recording app,
# or web browser (listed as "url/http" association in players).
# It maps audio MIME types, and extracts/converts playlist types
# (PLS, M3U, XSPF, SMIL, JSPF, ASX, raw urls).
#
# Each channel plugin has a .listformat which defines the linked
# audio playlist format. It's "pls", seldomly "m3u", or "xspf".
# Some channels list raw "srv" addresses, while Youtube "href"
# entries point to Flash videos.
#
# As fallback the playlist URL is retrieved and its MIME type
# checked, then its content regexped to guess the list format.
# Lastly a playlist format suitable for audio players recreated.
# Which is somewhat of a security feature; playlists get cleaned
# up this way. The conversion is not strictly necessary, because
# baseline PLS/M3U is understood by most players.
#
# And finally this module is also used by exporting and playlist
# importing features (e.g. by the drag'n'drop module).
#
# Still needs some rewrites to transition off the [url] lists,
# and work with full [rows] primarily. (And perhaps it should be
# renamed to "playlist" module now).


import re
import os
import platform
import copy
import json
import subprocess, pipes
from datetime import datetime
from xml.sax.saxutils import escape as xmlentities, unescape as xmlunescape

import ahttp
from config import *
import sys


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
    "application/vnd.ms-wpl": "smil",
    "audio/x-ms-wax":       "asx",
    "video/x-ms-asf":       "asx",
    "x-urn/st2-script":     "script",  # unused
    "application/x-shockwave-flash": "href",  # fallback
}

# Audio type MIME map
mediafmt_t = {
    "audio/mpeg":   "mp3",
    "audio/ogg":    "ogg",
    "audio/aac":    "aac",
    "audio/aacp":   "aac",
    "audio/midi":   "midi",
    "audio/mod":    "mod",
    "audio/it+zip": "mod",
    "audio/s3+zip": "mod",
    "audio/xm+zip": "mod",
}

# Player command placeholders for playlist formats
placeholder_map = dict(
    pls = "(%url | %pls | %u | %l | %r)",
    m3u = "(%m3u | %f | %g | %m)",
    xspf= "(%xspf | %xpsf | %x)",
    jspf= "(%jspf | %j)",
    asx = "(%asx)",
    smil= "(%smil)",
    srv = "(%srv | %d | %s)",
)

# Playlist format content probing (assert type)
playlist_content_map = [
   ("pls",  r""" (?i)\[playlist\].*NumberOfEntries """),
   ("xspf", r""" <\?xml .* <playlist .* ((?i)http://xspf\.org)/ns/0/ """),
   ("m3u",  r""" ^ \s* \#(EXT)?M3U """),
   ("asx" , r""" (?i) <asx\b """),
   ("smil", r""" <smil[^>]*> .* <seq> """),
   ("html", r""" (?i)<(audio|video)\b[^>]+\bsrc\s*=\s*["']?https?:// """),
   ("wpl",  r""" <\?wpl \s+ version="1\.0" \s* \?> """),
   ("b4s",  r""" <WinampXML> """),   # http://gonze.com/playlists/playlist-format-survey.html
   ("qtl",  r""" <?quicktime\d+type="application/x-quicktime-media-link"\d*?> """),
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

# custom stream domain (with faux audioformat) handlers
#  - may contain both "audio/x-service" handlers to convert playlist formsts
#  - and "urn:service" resolvers (which fetch an #id/page to extract actual stram url)
handler = {
    # "audio/soundcloud": playlist_callback(),
    # "urn:reciva": stream_resolve(),
}



# Exec wrapper
def run(cmd):
    if "cmd" in conf:
        cmd = conf.cmd % cmd
    elif conf.windows:
        cmd = "start " + cmd.encode(sys.getfilesystemencoding())
    else:
        cmd = cmd + " &"
    try:
        log.EXEC(cmd)
        os.system(cmd)
    except:
        log.ERR("Command not found:", cmd)

# Open help browser, chm, or streamtuner2 pages
def help(*args):
    for path in ("./help", "../share/streamtuner2/help", "/usr/share/doc/streamtuner2/help"):
        if not os.path.exists(path):
            continue
        if conf.windows:
            return run(("%s/help.chm" % path).replace("/", '\\'))
        else:
            return run("yelp %s" % path)
    return browser("http://fossil.include-once.org/streamtuner2/doc/tip/help/html/index.html")

# Invokes player/recorder for stream url and format
def run_fmt_url(row={}, audioformat="audio/mpeg", source="pls", assoc={}, append=None, cmd=None, add_default=True):
    # look for specific "audio/type"
    if audioformat in handler:
        return handler[audioformat](row, audioformat, source, assoc)
    # or "urn:service:…" resolvers (though this is usally done by genericchannel.row() already)
    elif row.get("url", "").startswith("urn:"):
        row = resolve_urn(row) or row
    # use default handler for mime type
    if not cmd:
        cmd = mime_app(audioformat, assoc)
    # replace %u, %url or $title placeholders
    cmd = interpol(cmd, source, row, add_default=add_default)
    if append:
        cmd = re.sub('(["\']?\s*)$', " " + append + "\\1", cmd)
    run(cmd)

# Start web browser
def browser(url):
    run_fmt_url({"url": url, "homepage": url}, "url/http", "srv", conf.play)

# Calls player for stream url and format
def play(row={}, audioformat="audio/mpeg", source="pls"):
    run_fmt_url(row, audioformat, source, conf.play)

# Call streamripper / youtube-dl / wget
def record(row={}, audioformat="audio/mpeg", source="href", append=None):
    run_fmt_url(row, audioformat, source, conf.record, append=append)


# OS shell command escaping
#
def quote(ins):
    if type(ins) is list:
        return " ".join([quote(s) for s in ins])
    # Windows: double quotes / caret escaping
    elif conf.windows:
        if re.search(r"""[()<>&!^'";\s]""", ins):
            ins = '"%s"' % ins
            ins = re.sub(r'([()<>"&^])', r"^\1", ins)
            return ins
        else:
            return subprocess.list2cmdline([ins])
    # Posix-style shell quoting
    else:
        if re.match("^\w[\w.:/\-]+$", ins):
            return ins
        else:
            return pipes.quote(ins)
    #return "%r" % ins


# Convert e.g. "text/x-scpls" MIME types to just "pls" monikers
#
def listfmt(t = "pls"):
    return listfmt_t.get(t, t) # e.g. "pls" or still "text/x-unknown"


# Convert MIME type into list of ["audio/xyz", "audio/*", "*/*"]
# for comparison against configured record/play association.
def mime_app(fmt, cmd_list):
    major = fmt[:fmt.find("/")]
    for match in [ fmt, major + "/*", "*/*", "video/*", "audio/*" ]:
        if cmd_list.get(match):
            return cmd_list[match]
    log.ERR("No audio player for stream type found")


# Is called upon rows containing an url starting with "urn:service:#id",
# calls the handler from the channel plugin to look up the page and find
# the actual streaming url
def resolve_urn(row):
    if row["url"].startswith("urn:"):
        urn_service = ":".join(row["url"].split(":")[:2])
        if urn_service in handler:
            row = handler[urn_service](row)
        else:
            log.WARN("There's currently no action.handler[] for %s:#id streaming addresses (likely disabled channel plugin)." % urn_service)
    return row


# Replaces instances of %m3u, %pls, %srv in a command string
# ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
#  · Also understands short aliases %l, %f, %d.
#  · And can embed %title or $genre placeholders (may use either % or $).
#  · Replace .pls URL with local .m3u file depending on map.
#
def interpol(cmd, source="pls", row={}, add_default=True):
    row = copy.copy(row)

    # Inject other meta fields (%title, %genre, %playing, %format, etc.)
    rx_keys = "[\$\%](" + "|".join(row.keys()) + ")\\b"
    cmd = re.sub(rx_keys, lambda m: quote(str(row.get(m.group(1)))), cmd)

    # Add default %pls if cmd has no %url placeholder
    if add_default and cmd.find("%") < 0:
        cmd = cmd + " %pls"
        # "pls" as default requires no conversion for most channels, and seems broadly supported by players

    # Playlist type placeholders (%pls, %m3u, %xspf, etc.)
    for dest, rx in placeholder_map.items():
        rx = "(?<!%%)%s\\b" % rx
        if re.search(rx, cmd, re.X):
            # no conversion
            if conf.playlist_asis:
                url = row["url"]
            # e.g. from .m3u to .pls
            else:
                url = convert_playlist(row["url"], listfmt(source), listfmt(dest), local_file=True, row=row)
            # insert quoted URL/filepath
            return re.sub(rx, quote(url), cmd.replace("%%", "%"), 2, re.X)

    if not add_default:
        return cmd
    else:
        return "/bin/false"


# Substitute streaming address with desired playlist format
# ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
# Converts input rows/urls, probes for playlist format, fetches them
# and possibly converts remote .pls to local .m3u/.xpsf filename or
# just returns direct "srv" urls.
#
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

    # Reuse tempoary files?
    if local_file and conf.reuse_m3u and os.path.exists(tmp_fn(row, dest)):
        log.STAT("reuse temporary filename")
        return [tmp_fn(row, dest)]
    
    # Retrieve from URL
    main.status("Converting " + url, timeout=0.95)
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
        log.WARN("Possible playlist format mismatch:", "listformat={}, http_mime={}, rx_probe={}, ext={}".format(source, mime, probe, ext))
#        log.DATA(cnt)

    # Extract URLs from content
    for fmt in playlist_fmt_prio:
        if not urls and fmt in (source, mime, probe, ext, "raw"):
            urls = cnv.urls(fmt)
            urls = filter(None, urls)
            log.DATA("conversion from:", source, " with extractor:", fmt, "got URLs=", urls)
            
    # Return original, or asis for srv targets
    if not urls:
        return [url]
    elif dest in ("srv", "href"):
        return urls

    # Otherwise convert to local file
    if local_file:
        fn = tmp_fn(row, dest)
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
        r = ahttp.session.get(url, stream=True, timeout=5.0)
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



# A few guessing functions
#
class heuristic_funcs(object):

    # Probe url "extensions" for common media types
    # (only care about the common audio formats, don't need an exact match or pre-probing in practice)
    def mime_guess(self, url, default="x-audio-video/unknown"):
        audio = re.findall("\\b(ogg|opus|spx|aacp|aac|mpeg|mp3|m4a|mp2|flac|midi|mod|kar|aiff|wma|ram|wav)", url)
        if audio:
            return "audio/{}".format(*audio)
        video = re.findall("\\b(mp4|flv|avi|mp2|theora|3gp|nsv|fli|ogv|webm|mng|mxu|wmv|mpv|mkv)", url)
        if audio:
            return "video/{}".format(*audio)
        return default

    # guess PLS/M3U from url
    def list_guess(self, url):
        ext = re.findall("|".join(playlist_fmt_prio), url)
        if ext:
            return ext[0]
        else:
            return "srv"



# Extract URLs and meta infos (titles) from playlist formats
# ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
# It's mostly regex-based at the moment, because that's more
# resilient against malformed XSPF or JSON. But specialized
# import helpers can be added as needed.
#
class extract_playlist(heuristic_funcs):

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
            self.src = open(fn, conf.open_mode).read()


    # Test URL/path "extension" for ".pls" / ".m3u" etc.
    def probe_ext(self, url):
        e = re.findall("\.(pls|m3u|xspf|jspf|asx|wpl|wsf|smil|html|url|json|desktop)\d?$", url)
        if e: return e[0]
        else: pass


    # Probe MIME type and content per regex
    def probe_fmt(self):
        for probe,rx in playlist_content_map:
            if re.search(rx, self.src, re.X|re.M|re.S):
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
        if hasattr(self, fmt):
            try:
                return getattr(self, fmt)()
            except Exception as e:
                log.WARN("Native '{}' parser failed on input (improper encoding, etc)".format(fmt), e)

        # regex scheme
        if not fmt in self.extr_urls:
            log.ERR("Unknown playlist format type '{}' - falling back to 'raw' mode".format(fmt))
            fmt = "raw"
        rules = self.extr_urls[fmt]
        rows = []
        fields = [name for name in ("url", "title", "homepage", "genre", "playing") if rules.get(name)]

        # Block-wise processing
        if rules.get("split"):
            for part_src in re.split(rules["split"], self.src, 0, re.X):
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


    # String decoding
    def decode(self, val, unesc):
        if unesc in ("xml", "*"):
            val = xmlunescape(val)
        if unesc in ("json", "*"):
            val = val.replace("\\/", "/")
        return val


    # Filter out duplicate urls
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
            url   = r"(?m) ^File\d* \s*=\s* (\w+://[^\s]+) ",
            title = r"(?m) ^Title\d* \s*=\s*(.+)",
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
            split = r" (?ix) <entry[^>]*> ",
            url   = r" (?ix) <ref \b[^>]+\b href \s*=\s* [\'\"] (\w+://[^\s\"\']+) [\'\"] ",
            title = r" (?ix) <title> ([^<>]+) ",
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
           #title = r" (?x) \"name\" \s*:\s* \"([^\"]+)\" ",
            unesc = "json",
        ),
        "json": dict(
            url   = r" (?x) \"(?:url|audio|stream)\" \s*:\s* \"(\w+:\\?/\\?/[^\"\s]+)\" ",
            title = r" (?x) \"(?:title|name|station)\" \s*:\s* \"([^\"]+)\" ",
            playing = r" (?x) \"(?:playing|current|description)\" \s*:\s* \"([^\"]+)\" ",
            homepage= r" (?x) \"(?:homepage|website|info)\" \s*:\s* \"([^\"]+)\" ",
            genre = r" (?x) \"(?:genre|keywords|category)\" \s*:\s* \"([^\"]+)\" ",
            unesc = "json",
        ),
        "asf": dict(
            url   = r" (?m) ^ \s*Ref\d+ = (\w+://[^\s]+) ",
            unesc = "xml",
        ),
        "qtl": dict(
            url   = r" <embed\s+src=[\"\']([^\"\']+)[\"\']\s*/>",
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
    
    
    # More exact PLS extraction (for the unlikely case entries were misordered)
    def pls(self):
        fieldmap = dict(file="url", title="title")
        rows = {}
        for field,num,value in re.findall("^\s* ([a-z_-]+) (\d+) \s*=\s* (.*) $", self.src, re.M|re.I|re.X):
            if not num in rows:
                rows[num] = {}
            field = fieldmap.get(field.lower())
            if field and len(value):
                rows[num][field] = value.strip()
        return [rows[str(i)] for i in sorted(map(int, rows.keys()))]


    # Jamendo JAMJAMJSON playlists
    def jamj(self):
        rows = []
        log.DATA(self.src)
        for result in json.loads(self.src)["results"]:
            for track in result.get("tracks") or [result]:
                rows.append(dict(
                    title = track["name"],
                    url = track["audio"],
                    playing = track.get("artist_name"),
                    img = track.get("image"),
                ))
        return rows


    # Add placeholder fields to extracted row
    def mkrow(self, row, title=None):
        url = row.get("url", "")
        comb = {
            "title": row.get("title") or title or re.sub("\.\w+$", "", os.path.basename(self.fn)),
            "playing": "",
            "url": None,
            "homepage": "",
            "listformat": self.probe_ext(url) or "href", # or srv?
            "format": self.mime_guess(url),
            "genre": "copy",
        }
        comb.update(row)
        return comb



# Save rows[] in one of the export formats
# ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
#  → The export() version uses urls[] and a template row{} as input,
# converts it into a list of complete rows{} beforehand. It's mostly
# utilized to expand a source playlist, merge in alternative streaming
# server addresses.
#
#  → With store() a full set of rows[] is required to begin with, as
# it performs a complete serialization.  Can save directly to a file.
# Which is often used directly by export functions, when no internal
# .pls/.m3u urls should be expanded or converted.
#
# Note that this can chain to convert_playlist() itself. So there's
# some danger for neverending loops in here. Never happened, but some
# careful source= and dest= parameter use is advised. Use source="asis"
# or "srv" to leave addresses alone, or "href" for input probing.
#
class save_playlist(object):

    # if converting
    source = "pls"
 
    # expand multiple server URLs into duplicate entries in target playlist
    multiply = True
 
    # constructor
    def __init__(self, source="asis", multiply=False):
        self.source = source
        self.multiply = multiply
    

    # Used by playlist_convert(), to transform a list of extracted URLs
    # into a local .pls/.m3u collection again. Therefore injects the
    # `title` back into each of the URL rows / or uses row{} template.
    def export(self, urls=[], row={}, dest="pls", title=None):
        row["title"] = row.get("title", title or "unnamed stream")
        rows = []
        for url in urls:
            if url:
                row.update(url=url)
                rows.append(copy.copy(row))
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
            txt += "%s\n" % ahttp.fix_url(r["url"])
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


    # QTL
    def qtl(self, rows):
        return """<?xml version="1.0"?>\n<?quicktime type="application/x-quicktime-media-link"?>\n"""\
            + "<embed src=\"%s\" />\n" % xmlentities(rows[0]["url"])


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
        return "[Desktop Entry]\nVersion=1.0\nIcon=media-playback-start\nType=Link\nName={title}\nComment={playing}\nURL={url}\n".format(**rows[0])

    # .URL shortcuts
    def url(self, rows):
        return "[InternetShortcut]\nURL={url}\n".format(**rows[0])



# Generate filename for temporary .pls/m3u, with unique id
def tmp_fn(row, ext="pls"):
    # use original url for generating a hash sum
    stream_url_hash = abs(hash(str(row)))
    try:
        channelname = main.current_channel
    except:
        channelname = "unknown"
    # return temp filename
    fn = "%s/%s.%s.%s" % (str(conf.tmp), channelname, stream_url_hash, ext)
    tmp_files.append(fn)
    return fn

# Collect generated filenames
tmp_files = []

# Callback from main / after gtk_main_quit
def cleanup_tmp_files():
    if not int(conf.reuse_m3u):
        [os.remove(fn) for fn in set(tmp_files)]

