#include <stdio.h>
#include "test.h"

int static foo(void) {
    return 0;
}

char *bar(int x) {
    return NULL;
}

int **baz() {
    static int *dummy_ptr = NULL;
    return &dummy_ptr;
}

static int *qux(void) {
    return NULL;
}

int __attribute__((cdecl)) wibble() {
    return 42;
}

int (myFunc)(int a, int b)
{
    return a + b;
}

void arrayParam(char arr[10]) {
    arr[0] = 'A';
}

char * const roPointerFunc() {
    static char c = 'Z';
    return &c;
}

int ***triplePtrFunc() {
    static int **dummy_double_ptr = NULL;
    return &dummy_double_ptr;
}

struct MyStruct {
    int x;
    int y;
};

struct MyStruct returnStruct() {
    struct MyStruct s;
    s.x = 1;
    s.y = 2;
    return s;
}

int main(void)
{
    struct MyOtherStruct mos;
    mos.a = 42;
    mos.b = 3.14f;

    union MyUnion u;
    u.i = 100;

    MyTypedefStruct tds;
    tds.w = 10;
    tds.z = 20;

    printf("foo() -> %d\n", foo());
    printf("bar(10) -> %p\n", (void*)bar(10));
    printf("baz() -> %p\n", (void*)baz());
    printf("qux() -> %p\n", (void*)qux());
    printf("wibble() -> %d\n", wibble());
    printf("myFunc(2, 3) -> %d\n", myFunc(2, 3));

    char arr[10];
    arrayParam(arr);
    printf("arrayParam() first char -> %c\n", arr[0]);

    char * const roPtr = roPointerFunc();
    printf("roPointerFunc() -> %c\n", *roPtr);

    int ***triplePtr = triplePtrFunc();
    printf("triplePtrFunc() -> %p\n", (void*)triplePtr);

    struct MyStruct s2 = returnStruct();
    printf("returnStruct() -> { %d, %d }\n", s2.x, s2.y);

    printf("MyEnum.MYENUM_VAL1 = %d\n", MYENUM_VAL1);
    printf("Anonymous enum g_anonEnumVar = %d\n", g_anonEnumVar);
    printf("MyOtherStruct = { %d, %.2f }\n", mos.a, mos.b);
    printf("MyUnion (int) = %d\n", u.i);
    printf("MyTypedefStruct = { %d, %d }\n", tds.w, tds.z);

    return 0;
}
