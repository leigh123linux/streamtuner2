# encoding: utf-8
# api: streamtuner2
# title: Favicons
# description: Display station favicons/logos. Instantly download them when ▸playing.
# config:
#    { name: favicon_google_first, type: bool, value: 1, description: "Prefer faster Google favicon to PNG conversion service." }
#    { name: favicon_delete_stub , type: bool, value: 1, description: "Don't accept any placeholder favicons." }
#    [ main-name: google_homepage ]
#    [ main-name: load_favicon ]
# type: feature
# category: ui
# version: 1.7
# depends: streamtuner2 >= 2.1.9, python:pil
# priority: standard
#
# This module fetches a favicon for each station, or a small banner
# or logo for some channel modules. It converts .ico image files and
# sanitizes .png or .jpeg images even prior display.
# 
# It prepares cache files in ~/.config/streamtuner2/icons/ in silent
# agreement with the station list display logic. Either uses station
# row["homepage"] or row["img"] URLs from any entry.
#
# While it can often discover favicons directly from station homepages,
# it's often speedier to use the Google PNG conversion service. Both
# depend on a recent Pillow2 python module (superseding the PIL module).
# Else may display images with fragments if converted from ICO files.
#
# Has recently been rewritten, is somewhat less entangled with other
# modules now:
#  · GenericChannel presets row["favicon"] with cache image filename
#    in any case, uses row["homepage"] or row["img"] as template
#  · The filename shortening functionality must be shared between
#    favicon and genericchannel.prepare() code
#  · uikit.columns() merely checks row["favicon"] for file existence
#    on redraws
#  · main.play() only calls .update_playing() or .update_all()
#  · urllib is no longer required, uses the main ahttp/requests API
#  · Still might need unhtml() from channels/__init__ later
#  · Reduce config options → move main favicon options here?


import os, os.path
from io import BytesIO
import re
from config import *
import ahttp
from PIL import Image
from uikit import gtk


# Ensure that we don't try to download a single favicon twice per session.
# If it's not available the first time, we won't get it after switching
# stations back and forth either. So URLs are skipped simply.
tried_urls = []



# Hook up as feature plugin
#
class favicon(object):

    # plugin attributes
    module = "favicon"
    meta = plugin_meta()
    
    
    # Register with main
    def __init__(self, parent):
    
        # Reference main, and register hook
        self.parent, self.main = parent, parent
        parent.hooks["play"].append(self.update_playing)

        # Prepare favicon cache directory
        conf.icon_dir = conf.dir + "/icons"
        if not os.path.exists(conf.icon_dir):
            os.mkdir(conf.icon_dir)
            open(icon_dir+"/.nobackup", "a").close()



    # Main callback: update favicon cache for complete list of station rows
    def update_all(self, *args, **kwargs):
        #kwargs[pixstore] = self.parent.channel()._ls, ...
        self.parent.thread(self.update_rows, *args, **kwargs)


    # Main callback for a single play() event
    def update_playing(self, row, pixstore=None):

        # Homepage search
        if conf.google_homepage and not len(row.get("homepage", "")):
            google_find_homepage(row)

        # Favicon only for currently playing station
        if conf.load_favicon:
            if row.get("homepage") or row.get("img"):
                self.update_all([row], pixstore=pixstore)

      
    # Run through rows[] to update "favicon" from "homepage" or "img",
    # optionally display new image right away in ListStore
    def update_rows(self, entries, pixstore=None):
        for i,row in enumerate(entries):
            ok = False

            # Try just once
            if row.get("homepage") in tried_urls:
                continue
            # Ignore existing ["favicon"] filename
            if row.get("favicon") and False:
                pass

            # Cache image filename: have or can't have
            favicon_fn = row_to_fn(row)
            if not favicon_fn:
                continue
            if os.path.exists(favicon_fn):
                continue

            # Custom "img" banner/logo as favicon
            if row.get("img"):
                tried_urls.append(row["img"])
                ok = banner_localcopy(row["img"], favicon_fn)

            # Homepage to favicon
            elif row.get("homepage"):
                tried_urls.append(row["homepage"])
                if conf.favicon_google_first:
                    ok = fav_google_ico2png(row["homepage"], favicon_fn)
                else:
                    ok = fav_from_homepage(row["homepage"], favicon_fn)

            # Update TreeView
            if ok:
                self.update_pixstore(row, pixstore, i)
        pass


    # Update favicon in treeview/liststore
    def update_pixstore(self, row, pixstore=None, row_i=None):
        log.FAVICON_UPDATE_PIXSTORE(pixstore, row_i)
        if not pixstore:
            return

        # Unpack ListStore, pixbuf column no, preset rowno
        ls, pix_entry, i = pixstore
        # Else use row index from update_all-iteration
        if i is None:
            i = row_i

        # Existing "favicon" cache filename
        if row.get("favicon"):
            fn = row["favicon"]
        else:
            fn = row_to_fn(row)

        # Update pixbuf in active station liststore
        if fn and os.path.exists(fn):
            try:
                p = gtk.gdk.pixbuf_new_from_file(fn)
                ls[i][pix_entry] = p
            except Exception as e:
                log.ERR("Update_pixstore image", fn, "error:", e)




#--- somewhat unrelated ---
#
# Should become a distinct feature plugin. - It just depends on correct
# invocation order for both plugins to interact.
# Googling is often blocked anyway, because this is clearly a bot request.
# And requests are tagged with ?client=streamtuner2 still purposefully.
# 
def google_find_homepage(self, row):
    """ Searches for missing homepage URL via Google. """
    if row.get("url") not in tried_urls:
        tried_urls.append(row.get("url"))

    if row.get("title"):
        rx_t = re.compile('^(([^-:]+.?){1,2})')
        rx_u = re.compile(r'/url\?q=(https?://[^"&/]+)')

        # Use literal station title now
        title = row["title"]
        #title = title.group(0).replace(" ", "%20")
        
        # Do 'le google search
        html = ahttp.get("http://www.google.com/search", params=dict(hl="en", q=title, client="streamtuner2"), ajax=1)
                  
        # Find first URL hit
        url = rx_u.findall(html)
        if url:
            row["homepage"] = ahttp.fix_url(url[0])
    pass
#-----------------




# Convert row["img"] or row["homepage"] into local favicon cache filename
def row_to_fn(row):
    url = row.get("img") or row.get("homepage") or None
    if url:
         url = url.lower()
         url = re.sub("^\w+://|/$", "", url)   # strip proto:// and trailing /
         url = re.sub("[^\w._-]", "_", url)    # remove any non-word characters
         url = "{}/{}.png".format(conf.icon_dir, url)
    return url


    
# Copy banner row["img"] into icons/ directory
def banner_localcopy(url, fn):

    # Check URL and target filename
    if not re.match("^https?://[\w.-]{10}", url):
        return False

    # Fetch and save
    imgdata = ahttp.get(url, binary=1, verify=False)
    if imgdata:
        return store_image(imgdata, fn)
    

    
# Check valid image, possibly convert, and save to cache filename
def store_image(imgdata, fn, resize=None):

    # Convert accepted formats -- even PNG for filtering now
    if re.match(br'^(.PNG|GIF\d+|.{0,15}JFIF|\x00\x00\x01\x00|.{0,255}<svg[^>]+svg)', imgdata):
        try:
            # Read from byte/str
            image = Image.open(BytesIO(imgdata))
            log.FAVICON_IMAGE_TO_PNG(image, resize)

            # Resize
            if resize and image.size[0] > resize:
                image.resize((resize, resize), Image.ANTIALIAS)

            # Convert to PNG via string buffer
            out = BytesIO()
            image.save(out, "PNG", quality=98)
            imgdata = out.getvalue()

        except Exception as e:
            return log.ERR("favicon/logo conversion error:", e) and False
    else:
        log.WARN("Couldn't detect valig image type from its raw content")

    # PNG already?
    if re.match(b"^.(PNG)", imgdata):
        try:
            with open(fn, "wb") as f:
                f.write(imgdata)
                return True
        except Exception as e:
            log.ERR("favicon.store_image() failure:", e)



# PNG via Google ico2png
def fav_google_ico2png(url, fn):
    log.FAVICON("fav_google_ico2png()")

    # Download from service
    domain = re.sub("^\w+://|/.*$", "", url).lower()
    geturl = "http://www.google.com/s2/favicons?domain={}".format(domain)
    imgdata = ahttp.get(geturl, binary=1, timeout=2.5)
    
    # Check for stub sizes
    if conf.favicon_delete_stub and len(imgdata) in (726,896): # google_placeholder_filesizes
        log.FAVICON("placeholder size, skipping")
        return False
    # Save
    else:
        return store_image(imgdata, fn)
    

  
# Peek at homepage URL, download favicon.ico <link rel>, convert to PNG file, resize to 16x16
def fav_from_homepage(url, fn):

    # Check for <link rel=icon>
    img = html_link_icon(url)
    if not img:
        return False
        
    # Fetch image, verify MIME type
    r = ahttp.get(img, binary=1, content=0, timeout=2.75)
    if not re.match('image/(png|jpe?g|png|ico|x-ico|vnd.microsoft.ico)', r.headers["content-type"], re.I):
        log.WARN("content-type wrong", r.headers)
        return False
        
    # Convert, resize and save
    return store_image(r.content, fn, resize=16)



# Download HTML, look for favicon name in <link rel=shortcut icon>.
#
# Very rough, doesn't respect any <base href=> and manually patches
# icon path to homepage url; nor does any entity decoding.
#
def html_link_icon(url, href="/favicon.png"):
    html = ahttp.get(url, encoding="iso-8859-1", timeout=3.5)
    # Extract
    for link in re.findall(r"""  <link ([^<>]+) >  """, html, re.X):
        pair = re.findall(r"""  \b(rel|href) \s*=\s* ["']? ([^<>"']+) ["']? """, link, re.X)
        pair = { name: val for name, val in pair }
        for name in ("shortcut icon", "favicon", "icon", "icon shortcut"):
            if name == pair.get("rel", "ignore") and pair.get("href"):
                href = pair["href"] # unhtml()
                break
    # Patch URL together (strip double proto/domain, or double slash)
    return re.sub("^(https?://\w[^/]+\w)?/?(https?://\w[^/]+\w)/?(/.+)$", "\g<2>\g<3>", url+href)
    # (should rather split this up again, a few more special cases w/ non-root homepages)
    




#-- test
if __name__ == "__main__":
    import sys
    favicon(None).download(sys.argv[1])

