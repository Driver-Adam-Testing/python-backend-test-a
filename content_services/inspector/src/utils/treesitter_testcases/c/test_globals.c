// Basic primitive-typed variables
unsigned short int a;
float b;
unsigned c;
short d;

// Multiple declarations in one line or spread across lines
long int e, f = 5,
            g;
short h, i;

// Storage class variables
extern int aa, bb;
auto int cc;
register int dd;
static int ee;

// Pointer variables
char *ptr;
const char **ptr2;
int const * const restrict ptr3;

// Variables with type qualifiers
const _Atomic unsigned long int q = 5;
restrict int q2 = 6;
volatile int q3 = 7;
constexpr int q4 = 8;
__thread int q5 = 9;

// Variables with attributes
alignas(16) int ii;
_Alignas(int) int jj;
int kk [[maybe_unused]];

// Struct/union/enum variables
struct aaa bbb;
union { int ccc; } ddd;
enum { eee, fff } ggg;

// Variables with assembly/register specifics
register uint64_t rd_ asm("x" "10");

// Attributes with GNU style
extern __attribute__((visibility("hidden"))) int foo;

// Array
#define LEN 2
local const int extra_lbits[LEN] /* extra bits for each length code */
   = {0,0};

#if defined(ENABLE_DEBUG)
  #ifdef LOGGING
    int debugLogVar;
  #endif
#endif

#ifndef SRC_AD469X_H_
#define SRC_AD469X_H_
int hello = 5;
#endif

void someFunction() {
    int localVar; // Should NOT be matched
}
