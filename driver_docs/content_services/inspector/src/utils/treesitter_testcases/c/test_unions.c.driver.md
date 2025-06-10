# Purpose
This C source code file demonstrates the use of unions, a data structure that allows storing different data types in the same memory location. The file includes various examples of union declarations, definitions, and usage, showcasing both named and unnamed unions, as well as typedefs for creating type aliases. The code illustrates how unions can be used to manage memory efficiently by allowing different data types to share the same memory space, which is particularly useful in scenarios where memory constraints are a concern.

The file contains a [`main`](#main) function, indicating that it is an executable program rather than a library or header file. Within [`main`](#main), several union variables are declared and initialized, demonstrating how to access and manipulate union members. The code also highlights the behavior of unions, where writing to one member affects the entire memory space of the union, as shown in the example with the `union Outer` and its anonymous nested struct. The program outputs the values of the union members to the console, providing a clear illustration of how unions operate in practice. This file serves as an educational resource for understanding the concept and practical application of unions in C programming.
# Imports and Dependencies

---
- `stdio.h`


# Global Variables

---
### global_data 
- **Type**: `union`
- **Description**: The `global_data` variable is a global unnamed union that can store either an integer (`int u`) or a floating-point number (`float v`). This union allows for the storage of one of these two types at any given time, sharing the same memory location for both types.
- **Use**: `global_data` is used to store either an integer or a float globally, accessible throughout the program.


---
### combo1 
- **Type**: `union Combined`
- **Description**: The variable `combo1` is a global variable of type `union Combined`, which can store either an integer (`ci`) or a float (`cf`). This union allows for the storage of different data types in the same memory location, but only one type can be stored at a time.
- **Use**: `combo1` is used to store an integer value, as demonstrated by the assignment `combo1.ci = 777;` in the `main` function.


---
### combo2 
- **Type**: `union Combined`
- **Description**: The variable `combo2` is a global variable of type `union Combined`, which can store either an integer (`ci`) or a float (`cf`). It is initialized with the float value 3.14f, meaning the `cf` member is currently active.
- **Use**: `combo2` is used to store a floating-point number, specifically initialized to 3.14f, and can be accessed globally within the file.


# Data Structures

---
### Named 
- **Type**: `union`
- **Members**:
    - `a`: An integer member of the union.
    - `b`: A float member of the union.
- **Description**: The 'Named' union is a data structure that allows storage of either an integer or a float in the same memory location, but not both simultaneously. This union is tagged with the name 'Named', allowing for easy reference and use in the code. The union's purpose is to provide a way to store different data types in the same memory space, with the constraint that only one of the members can hold a value at any given time.


---
### ForwardDecl 
- **Type**: `union`
- **Members**:
    - `c`: An array of 4 characters.
    - `l`: A long integer.
- **Description**: The 'ForwardDecl' union is a data structure that allows storage of either a character array of size 4 or a long integer, but not both simultaneously. This union is initially forward-declared and later defined, demonstrating the ability to declare a union type before providing its full definition. The union is useful for scenarios where a variable may need to store different data types at different times, sharing the same memory location.


---
### MyUnion 
- **Type**: `union`
- **Members**:
    - `x`: An integer member of the union.
    - `y`: A float member of the union.
- **Description**: The `MyUnion` data structure is a union that allows storage of either an integer (`x`) or a float (`y`) in the same memory location. This means that at any given time, `MyUnion` can hold a value of type `int` or `float`, but not both simultaneously. The use of a union is beneficial when you need to store different data types in the same memory space, optimizing memory usage.


---
### MyAnonUnion 
- **Type**: `union`
- **Members**:
    - `ll`: A member of type long long, used to store integer values.
    - `dd`: A member of type double, used to store floating-point values.
- **Description**: MyAnonUnion is an unnamed union that allows storage of either a long long integer or a double floating-point number, but not both simultaneously. This union is useful for saving memory when you need to store one of two different types of data at different times, as it shares the same memory location for both members.


---
### Outer 
- **Type**: `union`
- **Members**:
    - `i`: An integer member of the union.
    - `x`: A double member of the anonymous nested struct within the union.
    - `y`: Another double member of the anonymous nested struct within the union.
- **Description**: The `Outer` union is a compound data structure that can store either an integer `i` or a pair of double precision floating-point numbers `x` and `y` through an anonymous nested struct. This design allows for flexible data storage, where the union's memory can be used to store either a single integer or two doubles, but not simultaneously, as only one of the union's members can be active at any given time.


---
### Combined 
- **Type**: `union`
- **Members**:
    - `ci`: An integer member of the union.
    - `cf`: A float member of the union.
- **Description**: The 'Combined' union is a data structure that allows storage of either an integer or a float in the same memory location, but not both simultaneously. This union is defined with two variables, 'combo1' and 'combo2', where 'combo2' is initialized with a float value of 3.14. The union is useful for memory-efficient storage when only one of the types is needed at a time.


---
### Point2 
- **Type**: `union`
- **Members**:
    - `x`: An integer member of the union.
    - `y`: Another integer member of the union.
- **Description**: The `Point2` data structure is a union that allows for the storage of either an integer `x` or an integer `y`, but not both simultaneously, as unions share the same memory space for all their members. This union is typedef'd to `Point2` for ease of use and can also be referenced through a pointer type `Point2Ptr`. It is typically used to represent a 2D point with integer coordinates, where only one coordinate is needed at a time.


# Functions

---
### main <!-- {{#callable:main}} -->
The `main` function demonstrates the usage of various union types and prints their values, highlighting how unions share memory.
- **Inputs**:
    - None
- **Control Flow**:
    - Declare and initialize a `Named` union variable `namedVar` and set its `a` member to 42.
    - Declare and initialize a `ForwardDecl` union variable `fdVar` and set its `l` member to 123456789L.
    - Declare and initialize a `MyUnion` typedef union variable `myVar` and set its `y` member to 1.2345f.
    - Declare and initialize a `MyAnonUnion` typedef union variable `anonVar` and set its `dd` member to 2.71828.
    - Set the `u` member of the global unnamed union `global_data` to 100.
    - Declare a `Outer` union variable `outVar`, set its `i` member to 10, then overwrite it by setting `x` to 11.11, and finally overwrite `x` by setting `y` to 12.22.
    - Declare and initialize a `Combined` union variable `combo1` and set its `ci` member to 777.
    - Print the values of all initialized union members, noting that only the last written member in a union is valid due to shared storage.
    - Return 0 to indicate successful execution.
- **Output**:
    - The function outputs the values of the union members to the console, demonstrating the effect of shared storage in unions where only the last written member retains its value.


