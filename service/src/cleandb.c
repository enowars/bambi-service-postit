#include <sqlite3.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>

#include "util.h"

int
main(int argc, const char **argv)
{
	sqlite3 *db;
	sqlite3_stmt *user_res, *del_res;
	int status, uid, now, creat, verbose;
	const char *dbpath;

	dbpath = "db.sqlite3";
	if (argc > 1) dbpath = argv[1];

	status = sqlite3_open(dbpath, &db);
	ASSERTV(status == SQLITE_OK, "Cannot access database: %s",
		sqlite3_errmsg(db));

	status = sqlite3_busy_timeout(db, 10000);
	ASSERTV(status == SQLITE_OK, "Failed to set busy timeout: %s",
		sqlite3_errmsg(db));

	status = sqlite3_prepare_v2(db, "SELECT uid, name, creat FROM users",
		-1, &user_res, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to fetch data from database: %s",
		sqlite3_errmsg(db));

	now = time(NULL);

	while (sqlite3_step(user_res) == SQLITE_ROW) {
		uid = sqlite3_column_int(user_res, 0);
		creat = sqlite3_column_int(user_res, 2);

		if (now - creat < 60 * 12)
			continue;

		printf("Removing user '%s'\n", sqlite3_column_text(user_res, 1));

		/* delete posts */
		status = sqlite3_prepare_v2(db, "DELETE FROM posts WHERE uid = ?",
			-1, &del_res, NULL);
		ASSERTV(status == SQLITE_OK, "Failed to delete posts from db: %s",
			sqlite3_errmsg(db));

		status = sqlite3_bind_int(del_res, 1, uid);
		ASSERTV(status == SQLITE_OK, "Failed to bind param to sql query: %s",
			sqlite3_errmsg(db));

		ASSERTV(sqlite3_step(del_res) == SQLITE_DONE,
			"Failed to delete posts of user: %s", sqlite3_errmsg(db));

		sqlite3_finalize(del_res);

		/* delete user */
		status = sqlite3_prepare_v2(db, "DELETE FROM users WHERE uid = ?",
			-1, &del_res, NULL);
		ASSERTV(status == SQLITE_OK, "Failed to delete users from db: %s",
			sqlite3_errmsg(db));

		status = sqlite3_bind_int(del_res, 1, uid);
		ASSERTV(status == SQLITE_OK, "Failed to bind param to sql query: %s",
			sqlite3_errmsg(db));

		ASSERTV(sqlite3_step(del_res) == SQLITE_DONE,
			"Failed to delete posts of user: %s", sqlite3_errmsg(db));

		sqlite3_finalize(del_res);
	}

	sqlite3_finalize(user_res);
	sqlite3_close(db);
}

