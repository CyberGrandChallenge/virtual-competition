BIN_DIR     = $(DESTDIR)/usr/bin
MANDIR      = $(DESTDIR)/usr/share/man/man1
MAN         = ti-server.1.gz ti-rotate.1.gz ti-client.1.gz
PYLIB_DIR   = $(DESTDIR)/usr/lib/python2.7/dist-packages

all: man

%.1.gz: %.md
	pandoc -s -t man $< -o $<.tmp
	gzip -9 < $<.tmp > $@

man: $(MAN)

install:
	install -d $(BIN_DIR)
	install -d $(MANDIR)
	install bin/* $(BIN_DIR)
	install $(MAN) $(MANDIR)
	install -d $(PYLIB_DIR)
	install -m 444 lib/*.py $(PYLIB_DIR)

clean:
	-@rm -f *.tmp $(MAN)
	@echo nothing to clean
