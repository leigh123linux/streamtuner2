#
# encoding: utf-8
# api: python
# title: favicon download
# description: retrieves favicons for station homepages, plus utility code for display preparation
# config:
#    <var name="always_google" value="1" description="always use google favicon to png conversion service" />
#    <var name="only_google" value="1" description="don't try other favicon retrieval methods, if google service fails" />
#    <var name="delete_google_stub" value="1" description="delete placeholder favicons" />
# type: module
#
#
#  This module fetches favicon.ico files and prepares .png images for each domain
#  in the stations list. Homepage URLs are used for this.
#
#  Files end up in:
#     /home/user/.config/streamtuner2/icons/www.example.org.png
#
#  Currently relies on Google conversion service, because urllib+PIL conversion
#  method is still flaky, and a bit slower. Future version might use imagemagick.
#


always_google = 1      # use favicon service for speed
only_google = 1        # if that fails, try our other/slower methods?
delete_google_stub = 1   # don't keep placeholder images
google_placeholder_filesizes = (726,896)


import os, os.path
from compat2and3 import xrange, urllib
import re
from config import conf
try: from processing import Process as Thread
except: from threading import Thread
import ahttp



# ensure that we don't try to download a single favicon twice per session,
# if it's not available the first time, we won't get it after switching stations back and forth
tried_urls = []




# walk through entries
def download_all(entries):
  t = Thread(target= download_thread, args= ([entries]))
  t.start()
def download_thread(entries):
    for e in entries:
        # try just once
        if e.get("homepage") in tried_urls:
            continue
        # retrieve specific img url as favicon
        elif e.get("img"):
            localcopy(e["img"], True)
            continue
        # favicon from homepage URL
        elif e.get("homepage"):
            download(e["homepage"])
        # remember
        tried_urls.append(e.get("homepage"))
    pass

# download a single favicon for currently playing station
def download_playing(row):
    if conf.google_homepage and not row.get("homepage"):
        google_find_homepage(row)
    if conf.load_favicon and row.get("homepage"):
        download_all([row])
    pass



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
    if url.startswith("http"):
        fn = re.sub("[:/]", "_", url)
        fn = conf.dir + "/icons/" + fn
        if os.path.exists(fn):
            return fn
        elif download:
            imgdata = ahttp.get(url, binary=1)
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
    #print("favicon.ico")
    direct_download("http://"+domain(url)+"/favicon.ico", file(url))

  except:
    try:    # extract facicon filename from website <link rel>
      #print("html <rel favicon>")
      html_download(url)

    except:    # fallback
      #print("google ico2png")
      google_ico2png(url)




# retrieve PNG via Google ico2png
def google_ico2png(url):

  #try:
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

#  try: 
    # URL download
    r = urllib.urlopen(favicon)
    headers = r.info()
    
    # abort on
    if r.getcode() >= 300:
       raise Error("HTTP error" + r.getcode())
    if not headers["Content-Type"].lower().find("image/"):
       raise Error("can't use text/* content")
       
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

 # except:
  #  "File not found" and False


  
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
    
    # url or
    if favicon.startswith("http://"):
       None
    # just /pathname
    else:
       favicon = ahttp.urlparse.urljoin(url, favicon)
       #favicon = "http://" + domain(url) + "/" + favicon

    # download
    direct_download(favicon, file(url))






#
# title: workaround for PIL.Image to preserve the transparency for .ico import
#
# http://stackoverflow.com/questions/987916/how-to-determine-the-transparent-color-index-of-ico-image-with-pil
# http://djangosnippets.org/snippets/1287/
#
# Author: dc
# Posted: January 17, 2009
# Languag: Python
# Django Version: 1.0
# Tags: pil image ico 
# Score: 2 (after 2 ratings)
#
         
import operator
import struct

try:
    from PIL import BmpImagePlugin, PngImagePlugin, Image
except Exception as e:
    print("no PIL", e)
    always_google = 1
    only_google = 1


def load_icon(file, index=None):
    '''
    Load Windows ICO image.

    See http://en.wikipedia.org/w/index.php?oldid=264332061 for file format
    description.
    '''
    if isinstance(file, basestring):
        file = open(file, 'rb')

    try:
        header = struct.unpack('<3H', file.read(6))
    except:
        raise IOError('Not an ICO file')

    # Check magic
    if header[:2] != (0, 1):
        raise IOError('Not an ICO file')

    # Collect icon directories
    directories = []
    for i in xrange(header[2]):
        directory = list(struct.unpack('<4B2H2I', file.read(16)))
        for j in xrange(3):
            if not directory[j]:
                directory[j] = 256

        directories.append(directory)

    if index is None:
        # Select best icon
        directory = max(directories, key=operator.itemgetter(slice(0, 3)))
    else:
        directory = directories[index]

    # Seek to the bitmap data
    file.seek(directory[7])

    prefix = file.read(16)
    file.seek(-16, 1)

    if PngImagePlugin._accept(prefix):
        # Windows Vista icon with PNG inside
        image = PngImagePlugin.PngImageFile(file)
    else:
        # Load XOR bitmap
        image = BmpImagePlugin.DibImageFile(file)
        if image.mode == 'RGBA':
            # Windows XP 32-bit color depth icon without AND bitmap
            pass
        else:
            # Patch up the bitmap height
            image.size = image.size[0], image.size[1] >> 1
            d, e, o, a = image.tile[0]
            image.tile[0] = d, (0, 0) + image.size, o, a

            # Calculate AND bitmap dimensions. See
            # http://en.wikipedia.org/w/index.php?oldid=264236948#Pixel_storage
            # for description
            offset = o + a[1] * image.size[1]
            stride = ((image.size[0] + 31) >> 5) << 2
            size = stride * image.size[1]

            # Load AND bitmap
            file.seek(offset)
            string = file.read(size)
            mask = Image.fromstring('1', image.size, string, 'raw',
                                    ('1;I', stride, -1))

            image = image.convert('RGBA')
            image.putalpha(mask)

    return image




# convert .ico file to .png format
def ico2png(ico, png_fn):
  #print("ico2png", ico, png, image)
  
  try:  # .ico
    image = load_icon(ico, None)
  except:  # automatic img file type guessing
    image = Image.open(ico)
       
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


