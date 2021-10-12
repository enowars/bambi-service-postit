#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stdarg.h>

#include "gmp.h"

int check_signature(const char *msg, const char *sig,
	const char *exp, const char *mod);
