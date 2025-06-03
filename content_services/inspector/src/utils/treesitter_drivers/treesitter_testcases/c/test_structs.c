#include <stdio.h>

/* 1) Forward declaration of a struct (no definition yet). */
struct ForwardDecl;

/* 2) Named struct with a tag. */
struct Named {
    int a;
    int b;
};

/* 3) Now define the previously forward-declared struct. */
struct ForwardDecl {
    int c;
    float d;
};

/* 4) Typedef of a named struct. */
typedef struct _MyStruct {
    int x;
    int y;
} MyStruct;

/* 5) Typedef of an unnamed struct. */
typedef struct {
    int z;
} MyAnonTypedef;

/* 6) Unnamed struct at global (file) scope. */
struct {
    int u;
    int v;
} global_data;

/* 7) Struct containing an anonymous (unnamed) nested struct. */
// struct Outer { // NOTE: we will test this in C++ for nesting
//     int i;
//     struct {
//         float x;
//         float y;
//     };
// };

/* 8) Combined struct definition + variable declarations. */
struct Point {
    int px;
    int py;
} p1, p2 = { 3, 4 };

/* 9) Typedef of a struct and a pointer to that struct in one go!. */
typedef struct {
    int x;
    int y;
}
Point2, *Point2Ptr;


int main(void) {
    /* Using the named struct. */
    struct Named namedVar = { .a = 1, .b = 2 };

    /* Using the now-defined forward-declared struct. */
    struct ForwardDecl fdVar = { .c = 3, .d = 4.5f };

    /* Using the typedef'd named struct. */
    MyStruct myVar = { .x = 5, .y = 6 };

    /* Using the typedef'd unnamed struct. */
    MyAnonTypedef anonVar = { .z = 7 };

    /* Using the global unnamed struct. */
    global_data.u = 8;
    global_data.v = 9;

    /* Using the struct with an anonymous nested struct. */
    struct Outer outVar = { .i = 10, .x = 11.0f, .y = 12.0f };

    /* Working with variables declared along with the struct definition. */
    p1.px = 1;
    p1.py = 2;

    /* Print everything to verify usage. */
    printf("namedVar       = (%d, %d)\n", namedVar.a, namedVar.b);
    printf("fdVar          = (%d, %.2f)\n", fdVar.c, fdVar.d);
    printf("myVar          = (%d, %d)\n", myVar.x, myVar.y);
    printf("anonVar        = (%d)\n", anonVar.z);
    printf("global_data    = (%d, %d)\n", global_data.u, global_data.v);
    printf("outVar         = (i=%d, x=%.2f, y=%.2f)\n", outVar.i, outVar.x, outVar.y);
    printf("p1             = (%d, %d)\n", p1.px, p1.py);
    printf("p2             = (%d, %d)\n", p2.px, p2.py);

    return 0;
}
