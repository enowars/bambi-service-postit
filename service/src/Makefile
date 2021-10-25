CFLAGS =
LDLIBS = -lsqlite3 -lgmp

.PHONY: all clean

all: postit cleandb

clean:
	rm -f postit cleandb

postit: postit.c util.c crypto.c

cleandb: cleandb.c util.c
