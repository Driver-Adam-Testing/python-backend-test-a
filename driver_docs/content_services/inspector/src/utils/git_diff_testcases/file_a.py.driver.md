# Purpose
This Python script provides a narrow functionality focused on calculating and printing Fibonacci numbers. It defines a recursive function `fib` that computes the nth Fibonacci number, where `n` is a non-negative integer. The `main` function demonstrates the use of `fib` by printing the 11th Fibonacci number and the first five Fibonacci numbers in sequence. The script is designed to be executed as a standalone program, as indicated by the `if __name__ == "__main__":` block, which ensures that `main` is called only when the script is run directly. The file is marked with a comment indicating it should not be modified, suggesting it may be part of a larger system where its behavior is relied upon as-is.
# Functions

---
### fib 
The `fib` function calculates the nth Fibonacci number using a recursive approach.
- **Inputs**:
    - `n`: An integer representing the position in the Fibonacci sequence to compute.
- **Control Flow**:
    - Check if the input integer n is less than or equal to 1.
    - If n is less than or equal to 1, return n as the Fibonacci number.
    - If n is greater than 1, recursively call the fib function for (n-1) and (n-2) and return their sum.
- **Output**:
    - The function returns the nth Fibonacci number as an integer.


---
### main 
The `main` function prints the 11th Fibonacci number and the first five Fibonacci numbers.
- **Inputs**:
    - None
- **Control Flow**:
    - Calls the `fib` function with the argument 11 and prints the result.
    - Iterates over a range of numbers from 0 to 4.
    - For each number in the range, calls the `fib` function with the current number and prints the result.
- **Output**:
    - The function does not return any value; it outputs results directly to the console.


