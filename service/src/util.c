#include "util.h"

int
is_numstr(const char *str)
{
	int i;

	if (!*str) return 0;

	for (i = 0; str[i]; i++) {
		if (str[i] < '0' || str[i] > '9')
			return 0;
	}

	return 1;
}

char*
randstr(int n)
{
	const char alphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
		"abcdefghijklmnopqrstuvwxyz0123456789";
	char *msg;
	int i;

	srand(time(NULL));

	msg = malloc(n + 1);
	ASSERT(msg != NULL);

	for (i = 0; i < n; i++)
		msg[i] = alphabet[rand() % (ARRSIZE(alphabet)-1)];
	msg[n] = '\0';

	return msg;
}

void
assert(int res, const char *fmtstr, ...)
{
	va_list ap;

	if (!res) {
		va_start(ap, fmtstr);
		vfprintf(stderr, fmtstr, ap);
		va_end(ap);
		exit(1);
	}
}

char*
ask(const char *fmtstr, ...)
{
	static char buf[1024];
	va_list ap;
	char *tok;

	va_start(ap, fmtstr);
	vprintf(fmtstr, ap);
	va_end(ap);

	if (fgets(buf, ARRSIZE(buf), stdin)) {
		tok = strchr(buf, '\n');
		if (tok) *tok = '\0';
	} else {
		*buf = '\0';
	}

	return buf;
}
