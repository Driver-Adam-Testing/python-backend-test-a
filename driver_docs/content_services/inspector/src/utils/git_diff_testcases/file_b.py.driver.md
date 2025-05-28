# Purpose
This Python script provides a narrow functionality focused on calculating and printing the first five numbers of the Fibonacci sequence. It defines a recursive function `fib(n)` that computes the nth Fibonacci number, where `n` is a non-negative integer. The `main()` function iterates over the first five integers, calling `fib(i)` for each and printing the result. The script is designed to be executed as a standalone program, as indicated by the `if __name__ == "__main__":` block, which ensures that `main()` is called only when the script is run directly. The file is marked with a comment indicating it should not be modified, suggesting it may be part of a larger system where its behavior is relied upon as-is.
# Functions

---
### fib 
The `fib` function calculates the nth Fibonacci number using a recursive approach.
- **Inputs**:
    - `n`: An integer representing the position in the Fibonacci sequence to compute.
- **Control Flow**:
    - Check if the input integer n is less than or equal to 1.
    - If n is less than or equal to 1, return n as the Fibonacci number.
    - If n is greater than 1, recursively call fib(n - 1) and fib(n - 2) and return their sum.
- **Output**:
    - The function returns the nth Fibonacci number as an integer.


---
### main 
The `main` function prints the first five Fibonacci numbers by calling the `fib` function in a loop.
- **Inputs**:
    - None
- **Control Flow**:
    - The function enters a for loop that iterates over the range of numbers from 0 to 4.
    - In each iteration, it calls the `fib` function with the current loop index `i` as the argument.
    - The result of the `fib` function call is printed to the console.
- **Output**:
    - The function does not return any value; it outputs the first five Fibonacci numbers to the console.


