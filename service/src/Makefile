CFLAGS = -g
LDLIBS = -lsqlite3 -lgmp

.PHONY: all clean

all: postit cleandb

clean:
	rm postit cleandb

postit: postit.c util.c crypto.c
	$(CC) -o $@ $^ $(CFLAGS) $(LDLIBS)

cleandb: cleandb.c util.c
	$(CC) -o $@ $^ $(CFLAGS) $(LDLIBS)
