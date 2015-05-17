# encoding: utf-8
# api: streamtuner2
# title: Favicons
# description: Load and display station favicons/logos.
# config:
#    { name: load_favicon, type: bool, value: 1, description: "Load favicon instantly when ▸playing a station.", color: yellow }
#    { name: favicon_google_first, type: bool, value: 1, description: "Prefer faster Google favicon to PNG conversion service." }
#    { name: favicon_delete_stub , type: bool, value: 1, description: "Don't accept any placeholder favicons." }
#    { name: google_homepage, type: bool, value: 0, description: "Google missing station homepages right away." }
# type: feature
# category: ui
# version: 1.9
# depends: streamtuner2 >= 2.1.9, python:pil
# priority: standard
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABYAAAAWBAMAAAA2mnEIAAAAJ1BMVEUAAACwDw5oKh1RRU5OTSCOTxp0Um9zcyFUhSXsbwChdp/lgCNbrA7VFTQPAAAAAXRSTlMAQObYZgAAAAFiS0dEAIgFHU
#   gAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAHdElNRQffBQ4ENQJMtfdfAAAAmUlEQVQY02NgcAECYxBgYODeOXPmTKtVQLCAwXsmjL2YQRPINDNGsFclI7GXQdmzZ87MSoOyI0pnpgHVLAOy1c+c
#   mTkzeFWioBSUbQZkiy1mcPFpCXUxTksTFEtm8Ojp6OhQVDJWVFJi8DkDBIIgIARhKyKx3c8g2GfOBCKxFeHspg6EmiZFJDbEHB44W4CBwQNor5MSEDAAAGcoaQmD1t8TAAAAAElFTkSuQmCC
#
# This module fetches a favicon for each station. Some channels
# provide small logos/banners even. It sanitizes and converts
# any .ico/.png/.jpeg file prior display.
# 
# Cache files are kept in ~/.config/streamtuner2/icons/ where
# the station column display picks them up form.
#
# While it can often discover favicons directly from station
# homepages, it's mostly speedier to use the PNG conversion
# service from Google.
# Both methods depend on a recent Pillow2 python module (that
# superseded the PIL module). Else icon display may have some
# transparency fragments.


import os, os.path
from io import BytesIO
import re
import channels
from config import *
import ahttp
from PIL import Image
from uikit import gtk
#import traceback


# Ensure that we don't try to download a single favicon twice per session.
# If it's not available the first time, we won't get it after switching
# stations back and forth either. So URLs are skipped simply.
tried_urls = []



# Has recently been rewritten, is somewhat less entangled with other
# modules now:
#
#  · GenericChannel presets row["favicon"] with cache image filenames
#    in any case. It calls row_to_fn() per prepare_filters hook after
#    station list updates.
#
#  · uikit.columns() merely checks row["favicon"] for file existence
#    when redrawing a station list.
#
#  · main calls .update_playing() on hooks["play"],
#    or .update_all() per menu command



# Hook up as feature plugin
#
class favicon(object):

    # plugin attributes
    module = "favicon"
    meta = plugin_meta()
    
    
    # Register with main
    def __init__(self, parent):
    
        # Reference main, and register station .play() hook
        self.parent, self.main = parent, parent
        parent.hooks["play"].append(self.update_playing)

        # Register in channel/streams updating pipeline (to predefine row["favicon"] filename from `homepage` or `img`)
        channels.GenericChannel.prepare_filters.append(self.prepare_filter_favicon)

        # Prepare favicon cache directory
        conf.icon_dir = conf.dir + "/icons"
        if not os.path.exists(conf.icon_dir):
            os.mkdir(conf.icon_dir)
            open(icon_dir+"/.nobackup", "a").close()


    # Main menu "Update favicons": update favicon cache for complete list of station rows
    def update_all(self, *args, **kwargs):
        #kwargs[pixstore] = self.parent.channel()._ls, ...
        self.parent.thread(self.update_rows, *args, **kwargs)


    # Main [▸play] event for a single station
    def update_playing(self, row, pixstore=None, channel=None, **x):

        # Homepage search
        if conf.google_homepage and not len(row.get("homepage", "")):
            found = google_find_homepage(row)
            # Save channel list right away to preserve found homepage URL
            if found and conf.auto_save_stations:
                channel.save()
        else:
            found = False

        # Favicon only for currently playing station
        if conf.load_favicon:
            if row.get("homepage") or row.get("img"):
                self.parent.thread(self.update_rows, [row], pixstore=pixstore, fresh_homepage=found)

      
    # Run through rows[] to update "favicon" from "homepage" or "img",
    # optionally display new image right away in ListStore
    def update_rows(self, entries, pixstore=None, fresh_homepage=False, **x):
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

            try:
                # Image already exists
                if os.path.exists(favicon_fn):
                    if not fresh_homepage:
                        continue
                    else:  # For freshly added ["homepage"] when favicon already
                        ok = True  # exists in cache. Then just update pix store.

                # Download custom "img" banner/logo as favicon
                elif row.get("img"):
                    tried_urls.append(row["img"])
                    ok = banner_localcopy(row["img"], favicon_fn)

                # Fetch homepage favicon into local png
                elif row.get("homepage"):
                    tried_urls.append(row["homepage"])
                    if conf.favicon_google_first:
                        ok = fav_google_ico2png(row["homepage"], favicon_fn)
                    else:
                        ok = fav_from_homepage(row["homepage"], favicon_fn)

                # Update TreeView
                if ok:
                    self.update_pixstore(row, pixstore, i)
                    row["favicon"] = favicon_fn

            # catch HTTP Timeouts etc., so update_all() row processing just continues..
            except Exception as e:
                log.WARN("favicon.update_rows():", e)
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


    # Run after any channel .update_streams() to populate row["favicon"]
    # from `homepage` or `img` url.
    def prepare_filter_favicon(self, row):
        # if conf.show_favicons:  (do we still need that?)
        row["favicon"] = row_to_fn(row)




#--- somewhat unrelated ---
#
# Should become a distinct feature plugin. - It just depends on correct
# invocation order for both plugins to interact.
# Googling is often blocked anyway, because this is clearly a bot request.
# And requests are tagged with ?client=streamtuner2 still purposefully.
# 
def google_find_homepage(row):
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
        html = ahttp.get("http://www.google.com/search", params=dict(hl="en", q=title, client="streamtuner2"), ajax=1, timeout=3.5)
                  
        # Find first URL hit
        url = rx_u.findall(html)
        if url:
            row["homepage"] = ahttp.fix_url(url[0])
            return True
    pass
#-----------------




# Convert row["img"] or row["homepage"] into local favicon cache filename
# Use just domain for homepages, but most of the url for banner/logo imgs.
rx_strip_proto = re.compile("^\w+://|/$")
rx_just_domain = re.compile("^\w+://|[/#?].*$")
rx_non_wordchr = re.compile("[^\w._-]")
def row_to_fn(row):
    url = row.get("img")
    if url:
        url = rx_strip_proto.sub("", url)     # strip proto:// and trailing /
    else:
        url = row.get("homepage")
        if url:
            url = rx_just_domain.sub("", url) # remove proto:// and any /path
    if url:
        url = url.lower()
        url = rx_non_wordchr.sub("_", url)    # remove any non-word characters
        url = "{}/{}.png".format(conf.icon_dir, url)  # prefix cache directory
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
    

    
# Check for valid image binary, possibly convert or resize, then save to cache filename
def store_image(imgdata, fn, resize=None):

    # Convert accepted formats -- even PNG for filtering now
    if re.match(br'^(.PNG|GIF\d+|.{0,15}JFIF|\x00\x00\x01\x00|.{0,255}<svg[^>]+svg)', imgdata):
        try:
            # Read from byte/str
            image = Image.open(BytesIO(imgdata))
            log.FAVICON_IMAGE_TO_PNG(image, image.size, resize)

            # Resize
            if resize and image.size[0] > resize:
                try:
                    image.thumbnail(resize, Image.ANTIALIAS)
                except:
                    image = image.resize((resize,resize), Image.ANTIALIAS)

            # Convert to PNG via string buffer
            out = BytesIO()
            image.save(out, "PNG", quality=98)
            imgdata = out.getvalue()

        except Exception as e:
            #traceback.print_exc()
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

    # Download from service
    domain = re.sub("^\w+://|/.*$", "", url).lower()
    geturl = "http://www.google.com/s2/favicons?domain={}".format(domain)
    imgdata = ahttp.get(geturl, binary=1, timeout=3.5, quieter=1)
    
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
    r = ahttp.get(img, binary=1, content=0, timeout=4.25, quieter=1)
    if not re.match('image/(png|jpe?g|png|ico|x-ico|vnd.microsoft.ico)', r.headers["content-type"], re.I):
        log.WARN("content-type wrong", r.headers)
        return False
        
    # Convert, resize and save
    return store_image(r.content, fn, resize=16)



# Download HTML, look for favicon name in <link rel=shortcut icon>.
#
# Very rough: doesn't respect any <base href=> and manually patches
# icon path to homepage url; doesn't do much HTML entity decoding.
#
def html_link_icon(url, href="/favicon.png"):
    html = ahttp.get(url, encoding="iso-8859-1", timeout=4.5, quieter=1)
    # Extract
    for link in re.findall(r"""  <link ([^<>]+) >  """, html, re.X):
        pair = re.findall(r"""  \b(rel|href) \s*=\s* ["']? ([^<>"']+) ["']? """, link, re.X)
        pair = { name: val for name, val in pair }
        for name in ("shortcut icon", "favicon", "icon", "icon shortcut"):
            if name == pair.get("rel", "ignore").lower() and pair.get("href"):
                href = pair["href"].replace("&amp;", "&") # unhtml()
                break
    # Patch URL together
    log.DATA(url, href)
    if re.match("^https?://", href): # absolute URL
        return href
    elif href.startswith("//"): # proto-absolute
        return "http:" + href
    elif href.startswith("/"): # root path
        return re.sub("(https?://[^/]+).*$", "\g<1>", url) + href
    else: # relative path references xyz/../
        href = re.sub("[^/]+$", "", url) + href
        return re.sub("[^/]+/../", "/", href)
    




#-- test
if __name__ == "__main__":
    import sys
    favicon(None).download(sys.argv[1])


