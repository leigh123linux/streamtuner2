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
DEPS_A  := -n $(NAME) -d pygtk -d python2 -d python2-cssselect -d python2-keybinder2 -d python2-lxml -d python2-pillow -d python2-pyquery -d python2-xdg -d python2-requests
OPTS    := -s src -u packfile,man,fixperms -f --prefix=$(DEST) --deb-compression xz --rpm-compression xz --exe-autoextract

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
docs:
ver:	# copy `version:` info
	version get:plugin st2.py write:control PKG-INFO
clean:
	rm *.pyc */*.pyc
	rm -r __pycache__ */__pycache__

#-- bundles
xpm: deb pyz tar rpm exe
deb:
	$(PACK) $(OPTS) $(DEPS) -t $@ -p "$(NAME)-VERSION.deb" st2.py
rpm:
	$(PACK) $(OPTS) $(DEPS) -t $@ -p "$(NAME)-VERSION.rpm" st2.py
tar:
	$(PACK) $(OPTS) $(DEPS) -t $@ -p "$(NAME)-VERSION.bin.txz" st2.py
exe:
	$(PACK) $(OPTS) $(DEPS) -t $@ -p "$(NAME)-VERSION.exe" st2.py
arch:
	$(PACK) $(OPTS) $(DEPS_A) -t $@ -p "$(NAME)-VERSION.arch.txz" st2.py
pyz:
        #@BUG: relative package references leave a /tmp/doc/ folder
	$(PACK) -u packfile -s src -t zip --zip-shebang "/usr/bin/env python"	\
		-f -p "$(NAME)-$(VERSION).pyz" --prefix=./  .zip.py st2.py
src:
	cd .. && pax -wvJf streamtuner2/streamtuner2-$(VERSION).src.txz \
		streamtuner2/*.{py,png,svg,desktop} streamtuner2/channels/*.{py,png} \
		streamtuner2/{bundle/,contrib/,help/,gtk,NEWS,READ,PACK,PKG,CRED,Make,bin,.zip}*

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
	./st2.py -D

