#include <stdio.h>

/* 1) Basic typedefs for primitive types */
typedef int MyInt;
typedef float MyFloat;

/* 2) Typedef for a struct and a union */
typedef struct {
    int a;
    int b;
} MyStructAlias;

typedef union {
    double x;
    char y[8];
} MyUnionAlias;

/* 3) Typedef chaining */
typedef MyStructAlias NestedAlias;

/* 4) Typedef for an array */
typedef int ArrayAlias[10];

/* 5) Typedef for a pointer */
typedef int *PointerAlias;

/* 6) Multiple typedefs in one statement */
typedef long CombinedTypedef1, CombinedTypedef2;

/* 7) Recursive struct typedef */
typedef struct RecursiveStruct {
    int value;
    struct RecursiveStruct *next;
} RecursiveStruct;

/* 8) Complex typedef with multiple pointers */
typedef const volatile unsigned long long *ComplexAlias;

int main(void) {
    MyInt a = 42;
    MyFloat b = 3.14f;

    MyStructAlias s = {1, 2};
    MyUnionAlias u;
    u.x = 2.71828;

    NestedAlias nested = s;
    ArrayAlias arr = {0};

    PointerAlias ptr = &a;
    CombinedTypedef1 c1 = 123;
    CombinedTypedef2 c2 = 456;

    RecursiveStruct node1 = {1, NULL};
    RecursiveStruct node2 = {2, &node1};

    ComplexAlias complex_ptr = (ComplexAlias)&b;

    printf("a = %d\n", a);
    printf("b = %.2f\n", b);
    printf("s = (%d, %d)\n", s.a, s.b);
    printf("nested = (%d, %d)\n", nested.a, nested.b);
    printf("arr[0] = %d\n", arr[0]);
    printf("ptr = %p\n", (void*)ptr);
    printf("c1 = %ld\n", c1);
    printf("c2 = %ld\n", c2);
    printf("node1.value = %d, node2.value = %d\n", node1.value, node2.value);
    printf("complex_ptr = %p\n", (void*)complex_ptr);

    return 0;
}
