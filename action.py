
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
from ahttp import fix_url as http_fix_url, get as http_get
from config import conf, __print__ as debug, dbg
import platform


# Coupling to main window
#
main = None



# Streamlink/listformat mapping
#
lt = dict(
    pls = "audio/x-scpls",
    m3u = "audio/x-mpegurl",
    asx = "video/x-ms-asf",
    xspf = "application/xspf+xml",
    href = "url/http",
    srv = "url/direct",
    ram = "audio/x-pn-realaudio",
    smil = "application/smil",
    script = "text/x-urn-streamtuner2-script", # unused
)


# Audio type MIME map
#
mf = dict(
    mp3 = "audio/mpeg",
    ogg = "audio/ogg",
    aac = "audio/aac",
    midi = "audio/midi",
    mod = "audio/mod",
)

# Player command placeholders for playlist formats
placeholder_map = dict(
    pls = "%url | %pls | %u | %l | %r",
    m3u = "%m3u | %f | %g | %m",
    pls = "%srv | %d | %s",
)



# Exec wrapper
#
def run(cmd):
    if cmd: debug(dbg.PROC, "Exec:", cmd)
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
def quote(s):
    return "%r" % str(s)


# Convert e.g. "text/x-scpls" MIME types to just "pls" monikers
#
def listfmt(t = "pls"):
    if t in lf.values():
       for short,mime in lf.items():
           if mime == t:
               return short
    return t # "pls"


# Convert MIME type into list of ["audio/xyz", "audio/*", "*/*"]
# for comparison against configured record/play association.
def mime_app(fmt, cmd_list):
    for match in [ fmt, fmt[:fmt.find("/")] + "/*", "*/*" ]:
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
            url = convert_playlist(url, listfmt(source), listfmt(dest))
            # insert quoted URL/filepath
            return re.sub(rx, cmd, quote(url), 2, re.X)

    return "false"


# Substitute .pls URL with local .m3u,
# or direct srv address, or leave as-is.
#
def convert_playlist(url, source, dest):

    # Leave alone
    if source == dest or source in ("srv", "href"):
        return url

    # Else
    return url



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
        f = open(fn, "wb")
        f.write(txt)
        f.close()
    pass




# retrieve real stream urls from .pls or .m3u links
def extract_urls(pls, listformat="__not_used_yet__"):
    # extract stream address from .pls URL
    if (re.search("\.pls", pls)):       #audio/x-scpls
        return pls(pls)
    elif (re.search("\.asx", pls)):	#video/x-ms-asf
        return re.findall("<Ref\s+href=\"(http://.+?)\"", http_get(pls))
    elif (re.search("\.m3u|\.ram|\.smil", pls)):	#audio/x-mpegurl
        return re.findall("(http://[^\s]+)", http_get(pls), re.I)
    else:  # just assume it was a direct mpeg/ogg streamserver link
        return [ (pls if pls.startswith("/") else http_fix_url(pls)) ]
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

# check if there are any urls in a given file
def has_urls(tmp_fn):
    if os.path.exists(tmp_fn):
        return open(tmp_fn, "r").read().find("http://") > 0
    

# create a local .m3u file from it
def m3u(pls):

    # temp filename
    (tmp_fn, unique) = tmp_fn(pls)
    # does it already exist?
    if tmp_fn and unique and conf.reuse_m3u and has_urls(tmp_fn):
        return tmp_fn

    # download PLS
    debug( dbg.DATA, "pls=",pls )
    url_list = extract_urls(pls)
    debug( dbg.DATA, "urls=", url_list )

    # output URL list to temporary .m3u file
    if (len(url_list)):
        #tmp_fn = 
        f = open(tmp_fn, "w")
        f.write("#M3U\n")
        f.write("\n".join(url_list) + "\n")
        f.close()
        # return path/name of temporary file
        return tmp_fn
    else:
        debug( dbg.ERR, "error, there were no URLs in ", pls )
        raise "Empty PLS"

# Download a .pls resource and extract urls
def extract_from_pls(url):
    text = http_get(url)
    debug(dbg.DATA, "pls_text=", text)
    return re.findall("\s*File\d*\s*=\s*(\w+://[^\s]+)", text, re.I)
    # currently misses out on the titles            


# get a single direct ICY stream url (extract either from PLS or M3U)
def srv(url):
    return extract_urls(url)[0]

