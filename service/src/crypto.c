#include "crypto.h"
#include "util.h"

char*
int_to_str(mpz_t n)
{
	char* res;
	int len;

	len = (int) mpz_sizeinbase(n, 256);
	res = malloc(len + 1);
	ASSERT(res != NULL);
	mpz_export(res, NULL, 1, 1, 0, 0, n);
	res[len] = '\0';

	return res;
}

int
check_signature(const char *msg, const char *sig_str,
	const char *exp_str, const char *mod_str)
{
	mpz_t m, e, n, sig;
	char *_msg;
	int valid;

	mpz_init_set_str(e, exp_str, 0);
	mpz_init_set_str(n, mod_str, 0);
	mpz_init_set_str(sig, sig_str, 0);

	mpz_init(m);
	mpz_powm(m, sig, e, n);

	_msg = int_to_str(m);
	valid = !strcmp(msg, _msg);

	mpz_clear(n);
	mpz_clear(e);
	mpz_clear(sig);
	mpz_clear(m);
	free(_msg);

	return valid;
}
