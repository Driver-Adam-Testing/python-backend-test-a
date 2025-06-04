#include <stdio.h>

/* 1) Named enumeration with a tag. */
enum Color {
    RED,
    GREEN,
    BLUE
};

/* 2) Typedef of a named enumeration. */
typedef enum _Weekday {
    MON,
    TUE,
    WED,
    THU,
    FRI
} Weekday;

/* 3) Typedef of an unnamed enumeration. */
typedef enum {
    ALPHA,
    BETA,
    GAMMA
} MyAnonEnum;

/* 4) Unnamed enumeration at global (file) scope.
   Declares a variable (globalEnum) of this unnamed enum type. */
enum {
    XX,
    YY
} globalEnum;

/* 5) Combined enumeration definition + variable declarations.
   Defines enum Direction and declares dir1 and dir2 in one statement. */
enum Direction {
    NORTH,
    SOUTH,
    EAST,
    WEST
} dir1, dir2 = EAST;

/* 6) Typedef with instance type and instance ptr type def. */
typedef enum {
    ALPHA,
    BETA,
    GAMMA
} Kind, *KindPtr;


int main(void) {
    /* Using the named enum with a tag. */
    enum Color c = GREEN;

    /* Using the typedef'd named enum. */
    Weekday w = WED;

    /* Using the typedef'd unnamed enum. */
    MyAnonEnum e = BETA;

    /* Using the unnamed enum variable declared at global scope. */
    globalEnum = XX;

    /* Using the combined definition + declaration. */
    dir1 = NORTH;

    /* Print out the integer values (implementation-defined). */
    printf("c          = %d\n", c);
    printf("w          = %d\n", w);
    printf("e          = %d\n", e);
    printf("globalEnum = %d\n", globalEnum);
    printf("dir1       = %d, dir2 = %d\n", dir1, dir2);

    return 0;
}
