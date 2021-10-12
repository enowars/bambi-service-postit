#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stdarg.h>
#include <time.h>

#define _STR(s) #s
#define STR(s) _STR(s)
#define ARRSIZE(a) (sizeof(a)/sizeof(a[0]))
#define LOC() __FILE__ ":" STR(__LINE__)
#define ASSERT(expr) assert(expr, #expr "   | " LOC() "\n")
#define ASSERTV(expr, msg, ...) assert(expr, msg "   | " LOC() "\n", __VA_ARGS__)

enum { OK, FAIL };

int is_numstr(const char *str);

char* randstr(int n);

void assert(int res, const char *fmtstr, ...);

char* ask(const char *fmtstr, ...);


