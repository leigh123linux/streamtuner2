# Requires 
# · http://fossil.include-once.org/versionnum/
# · http://fossil.include-once.org/xpm/

SHELL   := /bin/bash #(for brace expansion)
NAME    := streamtuner2
VERSION := $(shell version get:plugin st2.py || echo 2.1dev)
DEST    := /usr/share/streamtuner2
INST    := install -m 644
PACK    := xpm
DEPS    := -n $(NAME) -d python -d python-pyquery -d python-gtk2 -d python-requests -d python-keybinder
OPTS    := -s src -u man,fixperms,preprocess=py -f --prefix=$(DEST) --deb-compression xz --rpm-compression xz --exe-autoextract

# targets
.PHONY:	bin
all:	gtk3 #(most used)
pack:	all ver docs xpm src
gtk3:	gtk3.xml.gz
zip:	pyz
print-%:
	@echo $*=$($*)

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
        #@BUG: relative package references leave a /tmp/doc/ folder
	$(PACK) -u preprocess=py -DPKG_PYZ -s src -t zip -p ".pyz" --prefix=./ --verbose -f .zip.py st2.py
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
	mkdir	-p				$(DEST)/channels
	mkdir	-p				/usr/share/doc/streamtuner2/help/img
	install -m 755		bin		/usr/bin/streamtuner2
	$(INST)		*py		-t $(DEST)
	$(INST)		gtk3*		-t $(DEST)
	$(INST)		channels/*py	-t $(DEST)/channels
	$(INST)		help/*page	-t /usr/share/doc/streamtuner2/help
	$(INST)		help/img/*	-t /usr/share/doc/streamtuner2/help/img
	$(INST)		CREDITS		-t $(DEST)
	$(INST)		README		-t /usr/share/doc/streamtuner2
	$(INST)		*.desktop	-t /usr/share/applications/
	$(INST)		icon.png	/usr/share/pixmaps/streamtuner2.png
	$(INST)		help/str*2.1	-t /usr/share/man/man1/

# start locally
st2: run
run:
	./st2.py
