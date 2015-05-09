# encoding: utf-8
# api: streamtuner2
# title: favicon download
# description: retrieves favicons for station homepages, plus utility code for display preparation
# config:
#    { name: favicon_google_first, type: bool, value: 1, description: "always use google favicon to png conversion service" }
#    { name: favicon_google_only,  type: bool, value: 1, description: "don't try other favicon retrieval methods, if google service fails" }
#    { name: favicon_delete_stub , type: bool, value: 1, description: "delete placeholder favicons" }
# type: function
# category: ui
# priority: standard
#
# This module fetches favicon.ico files and prepares .png images for each domain
# in the stations list. Homepage URLs are used for this.
#
# Files end up in:
#    /home/user/.config/streamtuner2/icons/www.example.org.png
#
# Currently relies on Google conversion service, because urllib+PIL conversion
# method is still flaky, and a bit slower. Future version might use imagemagick.


always_google = 1      # use favicon service for speed
only_google = 1        # if that fails, try our other/slower methods?
delete_google_stub = 1   # don't keep placeholder images
google_placeholder_filesizes = (726,896)


import os, os.path
from compat2and3 import xrange, urllib
import re
from config import *
from threading import Thread
import ahttp
import compat2and3
from PIL import Image
from uikit import gtk



# ensure that we don't try to download a single favicon twice per session,
# if it's not available the first time, we won't get it after switching stations back and forth
tried_urls = []




# walk through entries
def download_all(*args, **kwargs):
  t = Thread(target=download_thread, args=args, kwargs=kwargs)
  t.start()
def download_thread(entries, pixstore=None):
    for i,e in enumerate(entries):
        # try just once
        if e.get("homepage") in tried_urls:
            continue

        # retrieve specific img url as favicon
        elif e.get("img"):
            localcopy(e["img"], True)
            tried_urls.append(e.get("img"))
        # favicon from homepage URL
        elif e.get("homepage"):
            download(e["homepage"])
            tried_urls.append(e.get("homepage"))

        # Update TreeView
        update_pixstore(e, pixstore, i)
    pass

# download a single favicon for currently playing station
def download_playing(row, pixstore=None):
    if conf.google_homepage and not row.get("homepage"):
        google_find_homepage(row)
    if conf.load_favicon and row.get("homepage"):
        download_all([row], pixstore=pixstore)
    pass


# Update favicon in treeview/liststore
def update_pixstore(row, pixstore=None, row_i=None):
    log.PIXSTORE(pixstore, row_i)
    if pixstore:
        ls, pix_entry, i = pixstore
        if i is None:
            i = row_i
        fn = None
        if row.get("favicon"):
            fn = row["favicon"]
        elif row.get("img"):
            fn = localcopy(row["img"], False)
        elif row.get("homepage"):
            fn = file(row["homepage"])
        if fn and os.path.exists(fn):
            p = gtk.gdk.pixbuf_new_from_file(fn)
            ls[i][pix_entry] = p


#--- unrelated ---
def google_find_homepage(row):
    """ Searches for missing homepage URL via Google. """
    if row.get("url") not in tried_urls:
        tried_urls.append(row.get("url"))

        rx_t = re.compile('^(([^-:]+.?){1,2})')
        rx_u = re.compile('"(http://[^"]+)" class=l')

        # extract first title parts
        title = rx_t.search(row["title"])
        if title:
            title = title.group(0).replace(" ", "%20")
            
            # do a google search
            html = ahttp.get("http://www.google.de/search?hl=de&q="+title, params={}, ajax=1)
            
            # find first URL hit
            url = rx_u.search(html)
            if url:
                row["homepage"] = ahttp.fix_url(url.group(1))
    pass
#-----------------



# extract domain name
def domain(url):
    if url.startswith("http://"):
        return url[7:url.find("/", 8)]  # we assume our URLs are fixed already (http://example.org/ WITH trailing slash!)
    else:
        return "null"

# local filename
def name(url):
    return domain(url) + ".png"
  
# local filename
def file(url):
    icon_dir = conf.dir + "/icons"
    if not os.path.exists(icon_dir):
        os.mkdir(icon_dir)
        open(icon_dir+"/.nobackup", "w").close()
    return icon_dir + "/" + name(url)

# does the favicon exist
def available(url):
    return os.path.exists(file(url))
    
    
# copy image from url into icons/ directory
def localcopy(url, download=False):
    if url and url.startswith("http"):
        fn = re.sub("[:/]", "_", url)
        fn = conf.dir + "/icons/" + fn
        if os.path.exists(fn):
            return fn
        elif download:
            imgdata = ahttp.get(url, binary=1, verify=False)
            with open(fn, "wb") as f:
                f.write(imgdata)
                f.close()
        if os.path.exists(fn):    
            return fn
    else:
        return url




# download favicon for given URL
def download(url):

  # skip if .png for domain already exists
  if available(url):
    return


  # fastest method, so default to google for now
  if always_google:
      google_ico2png(url)
      if available(url) or only_google:
         return

  try:    # look for /favicon.ico first
    log.FAVICON("try /favicon.ico")
    direct_download("http://"+domain(url)+"/favicon.ico", file(url))

  except:
    try:    # extract facicon filename from website <link rel>
      log.FAVICON("html <rel favicon>")
      html_download(url)

    except Exception as e:    # fallback
      log.ERR(e)
      google_ico2png(url)




# retrieve PNG via Google ico2png
def google_ico2png(url):
    log.FAVICON("google ico2png")

    GOOGLE = "http://www.google.com/s2/favicons?domain="
    (fn, headers) = urllib.urlretrieve(GOOGLE+domain(url), file(url))

    # test for stub image
    if delete_google_stub and (filesize(fn) in google_placeholder_filesizes):
       os.remove(fn)

  
def filesize(fn):
   return os.stat(fn).st_size



# mime magic
def filetype(fn):
   f = open(fn, "rb")
   bin = f.read(4)
   f.close()
   if bin[1:3] == "PNG":
      return "image/png"
   else:
      return "*/*"



# favicon.ico
def direct_download(favicon, fn):

    # URL download
    r = urllib.urlopen(favicon)
    headers = r.info()
    log.HTTP(headers)
    
    # abort on
    if r.getcode() >= 300:
       raise Exception("HTTP error %s" % r.getcode())
    if not headers["Content-Type"].lower().find("image/") == 0:
       raise Exception("can't use text/* content")
       
    # save file
    fn_tmp = fn+".tmp"
    f = open(fn_tmp, "wb")
    f.write(r.read(32768))
    f.close()
        
    # check type
    if headers["Content-Type"].lower()=="image/png" and favicon.find(".png") and filetype(fn)=="image/png":
       pngresize(fn_tmp)
       os.mv(fn_tmp, fn)
    else:
       ico2png(fn_tmp, fn)
       os.remove(fn_tmp)


  
# peek at URL, download favicon.ico <link rel>
def html_download(url):


  # <link rel>
  #try:
    # download html, look for @href in <link rel=shortcut icon>
    r = urllib.urlopen(url)
    html = r.read(4096)
    r.close()
    rx = re.compile("""<link[^<>]+rel\s*=\s*"?\s*(?:shortcut\s+|fav)?icon[^<>]+href=["'](?P<href>[^<>"']+)["'<>\s].""")
    favicon = "".join(rx.findall(html))
    log.DATA(favicon)
    
    # url or
    if favicon.startswith("http://"):
       None
    # just /pathname
    else:
       favicon = compat2and3.urlparse.urljoin(url, favicon)
       log.FAVICON(favicon)
       #favicon = "http://" + domain(url) + "/" + favicon

    # download
    direct_download(favicon, file(url))



# convert .ico file to .png format
def ico2png(ico, png_fn):
    image = Image.open(ico)
    log.FAVICON_ICO2PNG(ico, png, image)
    # resize
    if image.size[0] > 16:
        image.resize((16, 16), Image.ANTIALIAS)
    # .png format
    image.save(png_fn, "PNG", quality=98)


# resize an image
def pngresize(fn, x=16, y=16):
    image = Image.open(fn)
    if image.size[0] > x:
        image.resize((x, y), Image.ANTIALIAS)
        image.save(fn, "PNG", quality=98)




#-- test
if __name__ == "__main__":
    import sys
    download(sys.argv[1])


