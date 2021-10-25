CFLAGS =
LDLIBS = -lsqlite3 -lgmp

.PHONY: all clean

all: postit cleandb gendb

clean:
	rm postit cleandb

postit: postit.c util.c crypto.c

cleandb: cleandb.c util.c

gendb: gendb.c util.c
