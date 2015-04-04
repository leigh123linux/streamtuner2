SHELL   := /bin/bash #(for brace expansion)
NAME    := streamtuner2
VERSION := $(shell version get:plugin st2.py)
PACK    := xpm
DEPS    := -n $(NAME) -d python-pyquery -d python-gtk2 -d python-requests -d python-keybinder
OPTS    := -s src -u man,fixperms -f --prefix=/usr/share/streamtuner2 --deb-compression xz --rpm-compression xz --exe-autoextract
all: gtk3 #(most used)

# Convert between internal GtkBuilder-zlib file and uncompressed xml
# (workaround because Python2 has no working gzip support)
gtk3:
	zlib-flate -compress < gtk3.xml > gtk3.xml.zlib
glade:
	zlib-flate -uncompress < gtk3.xml.zlib > gtk3.xml
	glade gtk3.xml 2>/dev/null
	zlib-flate -compress < gtk3.xml > gtk3.xml.zlib

# Package up using fpm/xpm
pack:	gtk3, ver, docs, xpm, src

docs:	# update static files
	gzip -9c NEWS > NEWS.gz
ver:	# copy `version:` info
	version get:plugin st2.py write:control PKG-INFO
clean:
	rm *.pyc */*.pyc
	rm -r __pycache__ */__pycache__

#-- bundles
xpm: deb, pyz#, bin, rpm, exe
deb:
	$(PACK) $(OPTS) $(DEPS) -t deb -p "$(NAME)-VERSION.deb" st2.py
rpm:
	$(PACK) $(OPTS) $(DEPS) -t rpm -p "$(NAME)-VERSION.rpm" st2.py
bin:
	$(PACK) $(OPTS) $(DEPS) -t tar -p "$(NAME)-VERSION.bin.txz" st2.py
zip:pyz
pyz:
	$(PACK) -s src -t zip -p "$(NAME)-VERSION.pyz" --prefix=./ --verbose -f .zip.py st2.py
src:
	cd .. && pax -wvJf streamtuner2/streamtuner2-$(VERSION).src.txz \
		streamtuner2/*.{py,png,svg,desktop} streamtuner2/channels/*.{py,png} \
		streamtuner2/{bundle/,help/,gtk,NEWS,READ,PACK,PKG,CRED,Make,bin,.zip}*

# test .deb contents
check:
	dpkg-deb -c streamtuner2*deb
	dpkg-deb -I streamtuner2*deb
	rpm -qpil *rpm

