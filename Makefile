# Requires 
# · http://fossil.include-once.org/versionnum/
# · http://fossil.include-once.org/xpm/

SHELL   := /bin/bash #(for brace expansion)
NAME    := streamtuner2
VERSION := $(shell version get:plugin st2.py || echo 2.1dev)
DEST    := /usr/share/streamtuner2
INST    := install -v
PACK    := xpm
DEPS    := -n $(NAME) -d python-pyquery -d python-gtk2 -d python-requests -d python-keybinder
OPTS    := -s src -u man,fixperms -f --prefix=$(DEST) --deb-compression xz --rpm-compression xz --exe-autoextract
.PHONY:  bin
all:  gtk3 #(most used)
pack: all ver docs xpm src
gtk3: gtk3.xml.gz
zip:  pyz

# Convert between internal GtkBuilder-gzipped file and uncompressed xml
gtk3.xml.gz: gtk3.xml
	gzip -c9 < gtk3.xml > gtk3.xml.gz
glade:
	gzip -dc > gtk3.xml < gtk3.xml.gz
	glade gtk3.xml 2>/dev/null
	gzip -c9 < gtk3.xml > gtk3.xml.gz

# Prepare packaging
docs:	# update static files
	gzip -9c NEWS > NEWS.gz
ver:	# copy `version:` info
	version get:plugin st2.py write:control PKG-INFO
clean:
	rm *.pyc */*.pyc
	rm -r __pycache__ */__pycache__

#-- bundles
xpm: deb pyz bin rpm exe
deb:
	$(PACK) $(OPTS) $(DEPS) -t deb -p "$(NAME)-VERSION.deb" st2.py
rpm:
	$(PACK) $(OPTS) $(DEPS) -t rpm -p "$(NAME)-VERSION.rpm" st2.py
bin:
	$(PACK) $(OPTS) $(DEPS) -t tar -p "$(NAME)-VERSION.bin.txz" st2.py
pyz:
	$(PACK) -s src -t zip -p ".pyz" --prefix=./ --verbose -f .zip.py st2.py
	echo "#!/usr/bin/env python" | cat - ".pyz" > "$(NAME)-$(VERSION).pyz"
	chmod +x "$(NAME)-$(VERSION).pyz" ; rm ".pyz"
exe:
	$(PACK) $(OPTS) $(DEPS) -t exe -p "$(NAME)-VERSION.exe" st2.py
src:
	cd .. && pax -wvJf streamtuner2/streamtuner2-$(VERSION).src.txz \
		streamtuner2/*.{py,png,svg,desktop} streamtuner2/channels/*.{py,png} \
		streamtuner2/{bundle/,help/,gtk,NEWS,READ,PACK,PKG,CRED,Make,bin,.zip}*

# test .deb contents
check:
	dpkg-deb -c streamtuner2*deb
	dpkg-deb -I streamtuner2*deb
	rpm -qpil *rpm

# manual installation
install:
	$(INST)		bin		/usr/bin/streamtuner2
	$(INST)		*.py		-d -t $(DEST)
	$(INST)		channels/	-d -t $(DEST)
	$(INST)		CREDITS		-d -t $(DEST)
	$(INST)		gtk3.*		-d -t $(DEST)
	$(INST)		help/		-d -t /usr/share/doc/streamtuner2/
	$(INST)		*.desktop	-t /usr/share/applications/
	$(INST)		help/str*2.1	-t /usr/share/man/man1/
	$(INST)		icon.png	-t /usr/share/pixmaps/streamtuner2.png
	$(INST)		README		-d -t /usr/share/doc/streamtuner2/

# start locally
st2: run
run:
	./st2.py
