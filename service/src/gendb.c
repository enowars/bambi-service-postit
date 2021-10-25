#include <stdlib.h>
#include <stdio.h>

#include "sqlite3.h"

#include "util.h"

static sqlite3 *db = NULL;

int
main(int argc, const char **argv)
{
	const char *dbpath, *sql;
	char *err_msg = NULL;
	int status;

	dbpath = "db.sqlite3";
	if (argc > 1) dbpath = argv[1];

	status = sqlite3_open(dbpath, &db);
	ASSERTV(status == SQLITE_OK, "Cannot access database: %s",
		sqlite3_errmsg(db));

	sql = "CREATE TABLE IF NOT EXISTS users(uid INTEGER PRIMARY KEY,"
		" name TEXT, mod TEXT, exp TEXT, creat INTEGER);";
	status = sqlite3_exec(db, sql, 0, 0, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to create users table: %s",
		sqlite3_errmsg(db));

	sql = "CREATE TABLE IF NOT EXISTS posts(pid INTEGER PRIMARY KEY,"
		" uid INTEGER SECONDARY KEY, text TEXT, creat INTEGER);";
	status = sqlite3_exec(db, sql, 0, 0, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to create posts table: %s",
		sqlite3_errmsg(db));

	sqlite3_close(db);
}
