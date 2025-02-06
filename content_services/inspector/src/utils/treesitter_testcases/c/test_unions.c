#include <stdio.h>

/* 1) Forward declaration of a union (no definition yet). */
union ForwardDecl;

/* 2) Named union with a tag. */
union Named {
    int   a;
    float b;
};

/* 3) Define the previously forward-declared union. */
union ForwardDecl {
    char c[4];
    long l;
};

/* 4) Typedef of a named union. */
typedef union _MyUnion {
    int   x;
    float y;
} MyUnion;

/* 5) Typedef of an unnamed union. */
typedef union {
    long long ll;
    double    dd;
} MyAnonUnion;

/* 6) Unnamed union at global (file) scope + global variable. */
union {
    int   u;
    float v;
} global_data;

/* 7) Union containing an anonymous (unnamed) nested struct.
   The embedded struct has no tag and no name, so its members
   are referenced as outVar.x and outVar.y if we switch to
   that part of the union. */
union Outer {
    int i;
    struct {
        double x;
        double y;
    };
};

/* 8) Combined union definition + variable declarations in one statement. */
union Combined {
    int   ci;
    float cf;
} combo1, combo2 = { .cf = 3.14f };

typedef union {
    int x;
    int y;
}
Point2, *Point2Ptr;

int main(void) {
    /* Using the named union with a tag. */
    union Named namedVar;
    namedVar.a = 42;

    /* Using the now-defined forward-declared union. */
    union ForwardDecl fdVar;
    fdVar.l = 123456789L;

    /* Using the typedef'd named union. */
    MyUnion myVar;
    myVar.y = 1.2345f;

    /* Using the typedef'd unnamed union. */
    MyAnonUnion anonVar;
    anonVar.dd = 2.71828;

    /* Using the global unnamed union. */
    global_data.u = 100;

    /* Using the union with an anonymous nested struct. */
    union Outer outVar;
    outVar.i = 10;     /* Storing an int overwrites the union’s entire memory. */
    outVar.x = 11.11;  /* Now storing 'x' overwrites 'i'. */
    outVar.y = 12.22;  /* Storing 'y' overwrites 'x'. */

    /* Using the combined definition + variable declarations. */
    combo1.ci = 777;

    printf("namedVar.a        = %d\n", namedVar.a);
    printf("fdVar.l           = %ld\n", fdVar.l);
    printf("myVar.y           = %f\n", myVar.y);
    printf("anonVar.dd        = %lf\n", anonVar.dd);
    printf("global_data.u     = %d\n", global_data.u);

    /* Because a union shares storage, only the last write is “current.” */
    printf("outVar.i          = %d   (overwritten by outVar.x, outVar.y)\n", outVar.i);
    printf("outVar.x          = %f   (overwritten by outVar.y)\n", outVar.x);
    printf("outVar.y          = %f\n", outVar.y);

    printf("combo1.ci         = %d\n", combo1.ci);
    printf("combo2.cf         = %f\n", combo2.cf);

    return 0;
}
