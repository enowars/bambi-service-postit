#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>

#include "sqlite3.h"

#include "util.h"
#include "crypto.h"

static char *current_user = NULL;
static sqlite3 *db = NULL;

static const char *BANNER =
"\n"
"...........................................................\n"
": ########::: #######::: ######:: ########: ####: ########:\n"
": ##.... ##: ##.... ##: ##... ##:... ##..::. ##::... ##..::\n"
": ##:::: ##: ##:::: ##: ##:::..::::: ##::::: ##::::: ##::::\n"
": ########:: ##:::: ##:. ######::::: ##::::: ##::::: ##::::\n"
": ##.....::: ##:::: ##::..... ##:::: ##::::: ##::::: ##::::\n"
": ##:::::::: ##:::: ##: ##::: ##:::: ##::::: ##::::: ##::::\n"
": ##::::::::. #######::. ######::::: ##:::: ####:::: ##::::\n"
":..::::::::::.......::::......::::::..:::::....:::::..:::::\n"
"\n"
" Commands: help, register, users, info, login, post, posts\n"
"\n";

void
cleanup(void)
{
	sqlite3_close(db);
}

void
timeout(int sig)
{
	printf("time's up!\n");
	exit(1);
}

void
init(int argc, const char **argv)
{
	const char *dbpath, *sql;
	char *err_msg = NULL;
	int status;

	setvbuf(stdin, NULL, _IONBF, 0);
	setvbuf(stdout, NULL, _IONBF, 0);

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
		" uid INTEGER SECONDARY KEY, text TEXT,"
		" creat INTEGER);";
	status = sqlite3_exec(db, sql, 0, 0, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to create users table: %s",
		sqlite3_errmsg(db));

	signal(SIGALRM, timeout);
	alarm(120);

	atexit(cleanup);
}

int
user_id(const char *username)
{
	sqlite3_stmt *res;
	int status, uid;

	status = sqlite3_prepare_v2(db, "SELECT uid FROM users WHERE name = ?",
		-1, &res, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to fetch users from database: %s",
		sqlite3_errmsg(db));

	status = sqlite3_bind_text(res, 1, username, -1, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to bind param to sql query: %s",
		sqlite3_errmsg(db));

	uid = -1;
	if (sqlite3_step(res) == SQLITE_ROW)
		uid = sqlite3_column_int(res, 0);

	sqlite3_finalize(res);

	return uid;
}

void
user_info(const char *username, char **exp, char **mod)
{
	sqlite3_stmt *res;
	int status, uid;

	status = sqlite3_prepare_v2(db, "SELECT exp, mod FROM users WHERE name = ?",
		-1, &res, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to fetch users from database: %s",
		sqlite3_errmsg(db));

	status = sqlite3_bind_text(res, 1, username, -1, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to bind param to sql query: %s",
		sqlite3_errmsg(db));

	ASSERT(sqlite3_step(res) == SQLITE_ROW);

	*exp = strdup((void*) sqlite3_column_text(res, 0));
	ASSERT(*exp != NULL);

	*mod = strdup((void*) sqlite3_column_text(res, 1));
	ASSERT(*mod != NULL);

	sqlite3_finalize(res);
}

void
api_create_user(char *username)
{
	sqlite3_stmt *res;
	char *mod, *exp;
	int status;

	if (!username) {
		printf("Please supply a username\n");
		return;
	}

	if (user_id(username) >= 0) {
		printf("A user with that name already exists\n");
		return;
	}

	mod = NULL;
	exp = strdup(ask("Enter RSA exponent: "));
	ASSERT(exp != NULL);
	if (!is_numstr(exp)) {
		printf("Invalid RSA modulus\n");
		goto cleanup;
	}

	mod = strdup(ask("Enter RSA modulus: "));
	ASSERT(mod != NULL);
	if (!is_numstr(mod)) {
		printf("Invalid RSA modulus\n");
		goto cleanup;
	}

	status = sqlite3_prepare_v2(db,
		"INSERT INTO users (name, exp, mod, creat) VALUES (?, ?, ?, ?);",
		-1, &res, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to fetch data from database: %s",
		sqlite3_errmsg(db));

	status = sqlite3_bind_text(res, 1, username, -1, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to bind param to sql query: %s",
		sqlite3_errmsg(db));

	status = sqlite3_bind_text(res, 2, exp, -1, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to bind param to sql query: %s",
		sqlite3_errmsg(db));

	status = sqlite3_bind_text(res, 3, mod, -1, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to bind param to sql query: %s",
		sqlite3_errmsg(db));

	status = sqlite3_bind_int(res, 4, time(NULL));
	ASSERTV(status == SQLITE_OK, "Failed to bind param to sql query: %s",
		sqlite3_errmsg(db));

	ASSERTV(sqlite3_step(res) == SQLITE_DONE, "Failed to create user: %s",
		sqlite3_errmsg(db));

	sqlite3_finalize(res);

cleanup:
	free(exp);
	free(mod);
}

void
api_list_users(char *args)
{
	sqlite3_stmt *res;
	int status;

	status = sqlite3_prepare_v2(db, "SELECT name FROM users", -1, &res, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to fetch data from database: %s",
		sqlite3_errmsg(db));

	while (sqlite3_step(res) == SQLITE_ROW)
		printf("- %s\n", sqlite3_column_text(res, 0));

	sqlite3_finalize(res);
}

void
api_user_info(char *username)
{
	sqlite3_stmt *res;
	int status, uid;

	if (!username) {
		printf("Please supply a username\n");
		return;
	}

	if ((uid = user_id(username)) < 0) {
		printf("A user with that name does not exist\n");
		return;
	}

	status = sqlite3_prepare_v2(db, "SELECT name, exp, mod FROM users WHERE uid = ?",
		-1, &res, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to fetch data from database: %s",
		sqlite3_errmsg(db));

	status = sqlite3_bind_int(res, 1, uid);
	ASSERTV(status == SQLITE_OK, "Failed to bind param to sql query: %s",
		sqlite3_errmsg(db));

	ASSERTV(sqlite3_step(res) == SQLITE_ROW, "Failed to fetch user data: %s",
		sqlite3_errmsg(db));

	printf("Username: %s\n", sqlite3_column_text(res, 0));
	printf("RSA Exponent: %s\n", sqlite3_column_text(res, 1));
	printf("RSA Modulus: %s\n", sqlite3_column_text(res, 2));

	sqlite3_finalize(res);
}

void
api_login(char *username)
{
	const char *sig;
	char *chall, *exp, *mod;
	int uid;

	if (!username) {
		printf("Please supply a username\n");
		return;
	}

	if ((uid = user_id(username)) < 0) {
		printf("A user with that name does not exist\n");
		return;
	}

	exp = mod = NULL;
	chall = randstr(32);
	printf("Please verify your identity.\n");
	printf("Sign this message: %s\n", chall);

	sig = ask("Signature: ");
	if (!is_numstr(sig)) {
		printf("Invalid signature format (base 10)\n");
		goto cleanup;
	}

	user_info(username, &exp, &mod);

	if (!check_signature(chall, sig, exp, mod)) {
		printf("Invalid signature\n");
		goto cleanup;
	}

	if (current_user) free(current_user);
	current_user = strdup(username);
	ASSERT(current_user != NULL);

cleanup:
	free(chall);
	free(mod);
	free(exp);
}

void
api_create_post(char *args)
{
	sqlite3_stmt *res;
	const char *msg;
	int uid, status;

	if (!current_user) {
		printf("Not logged in!\n");
		return;
	}

	ASSERT((uid = user_id(current_user)) >= 0);

	msg = ask("Enter message: ");
	if (!*msg) {
		printf("Message can not be empty\n");
		return;
	}

	status = sqlite3_prepare_v2(db,
		"INSERT INTO posts (uid, text, creat) VALUES (?, ?, ?);",
		-1, &res, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to fetch data from database: %s",
		sqlite3_errmsg(db));

	status = sqlite3_bind_int(res, 1, uid);
	ASSERTV(status == SQLITE_OK, "Failed to bind param to sql query: %s",
		sqlite3_errmsg(db));

	status = sqlite3_bind_text(res, 2, msg, -1, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to bind param to sql query: %s",
		sqlite3_errmsg(db));

	status = sqlite3_bind_int(res, 3, time(NULL));
	ASSERTV(status == SQLITE_OK, "Failed to bind param to sql query: %s",
		sqlite3_errmsg(db));

	ASSERTV(sqlite3_step(res) == SQLITE_DONE, "Failed to create post: %s",
		sqlite3_errmsg(db));

	sqlite3_finalize(res);
}

void
api_list_posts(char *args)
{
	sqlite3_stmt *res;
	const char post_text;
	int uid, status;

	if (!current_user) {
		printf("Not logged in!\n");
		return;
	}

	ASSERT((uid = user_id(current_user)) >= 0);

	status = sqlite3_prepare_v2(db, "SELECT text FROM posts WHERE uid = ?",
		-1, &res, NULL);
	ASSERTV(status == SQLITE_OK, "Failed to fetch posts from database: %s",
		sqlite3_errmsg(db));

	status = sqlite3_bind_int(res, 1, uid);
	ASSERTV(status == SQLITE_OK, "Failed to bind param to sql query: %s",
		sqlite3_errmsg(db));

	while (sqlite3_step(res) == SQLITE_ROW)
		printf("> %s\n", sqlite3_column_text(res, 0));

	sqlite3_finalize(res);
}

void
api_help(char *command)
{
	struct {
		const char *cmd, *args, *desc;
	} descs[] = {
		{ "help", "COMMAND", "Returns usage information" },
		{ "register", "USER", "Create a new user" },
		{ "login", "USER", "Login as a user" },
		{ "users", "", "Lists all registered users" },
		{ "post", "", "Create a new post as the current user" },
		{ "posts", "", "Lists posts created by the current user" },
	};
	int i;

	if (!command) {
		printf("Supply a command to view usage info\n");
		return;
	}

	for (i = 0; i < ARRSIZE(descs); i++) {
		if (!strcmp(descs[i].cmd, command)) {
			printf("%s %s%s: %s\n", descs[i].cmd, descs[i].args,
				*descs[i].args ? " " : "", descs[i].desc);
			break;
		}
	}

	if (i == ARRSIZE(descs))
		printf("Unknown command: %s\n", command);
}

int
main(int argc, const char **argv)
{
	struct {
		const char *name;
		void (*func)(char *args);
	} cmds[] = {
		{ "register", api_create_user },
		{ "users", api_list_users },
		{ "info", api_user_info },
		{ "login", api_login },
		{ "post", api_create_post },
		{ "posts", api_list_posts },
		{ "help", api_help },
	};
	char *cmd, *tok, *args;
	int exit, i;

	init(argc, argv);

	printf("%s", BANNER);

	exit = 0;
	while (!exit) {
		cmd = ask("\r$ ");
		if (!*cmd) continue;

		cmd = strdup(cmd);
		ASSERT(cmd != NULL);

		tok = strchr(cmd, ' ');
		if (tok) *tok = '\0';
		args = tok ? tok + 1 : NULL;
		if (args && !*args) args = NULL;

		for (i = 0; i < ARRSIZE(cmds); i++) {
			if (!strcmp(cmd, cmds[i].name)) {
				cmds[i].func(args);
				break;
			}
		}

		if (i == ARRSIZE(cmds))
			printf("Unknown command: %s\n", cmd);

		free(cmd);
	}

	printf("bye!\n");
}
