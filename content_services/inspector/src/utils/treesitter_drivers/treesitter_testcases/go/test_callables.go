// Test cases for Go function definitions and function calls
package main

import (
	"context"
	"fmt"
	"log"
	"time"
)

// 1) Simple function definition
func simpleFunction() {
	fmt.Println("simple")
}

// 2) Function with parameters
func functionWithParams(a int, b string, c float64) string {
	return fmt.Sprintf("%d %s %.2f", a, b, c)
}

// 3) Function with return values
func functionWithReturns(x, y int) (int, int) {
	return x + y, x - y
}

// 4) Function with named return values
func namedReturns(a, b int) (sum, diff int) {
	sum = a + b
	diff = a - b
	return
}

// 5) Function with variadic parameters
func variadicFunction(base int, values ...int) int {
	total := base
	for _, v := range values {
		total += v
	}
	return total
}

// 6) Function with pointer parameters
func pointerFunction(ptr *int) {
	if ptr != nil {
		*ptr = *ptr * 2
	}
}

// 7) Function with slice and map parameters
func sliceMapFunction(slice []string, m map[string]int) {
	for _, s := range slice {
		m[s] = len(s)
	}
}

// 8) Function with interface parameter
func interfaceFunction(w fmt.Stringer) string {
	return w.String()
}

// 9) Function with channel parameter
func channelFunction(ch chan<- int, values ...int) {
	for _, v := range values {
		ch <- v
	}
	close(ch)
}

// 10) Function with context
func contextFunction(ctx context.Context, timeout time.Duration) error {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-time.After(timeout / 2):
		return nil
	}
}

// 11) Anonymous functions and closures
func closureExample() func(int) int {
	multiplier := 10
	return func(x int) int {
		return x * multiplier
	}
}

// 12) Method with receiver
type Calculator struct {
	value int
}

// Pointer receiver methods
func (c *Calculator) Add(x int) {
	c.value += x
}

// Value receiver methods
func (c Calculator) GetValue() int {
	return c.value
}

// 8) Generic type with methods (Go 1.18+)
type Stack[T any] struct {
	items []T
}

func (s *Stack[T]) Push(item T) {
	s.items = append(s.items, item)
}

func (s *Stack[T]) Pop() (T, bool) {
	if len(s.items) == 0 {
		var zero T
		return zero, false
	}
	index := len(s.items) - 1
	item := s.items[index]
	s.items = s.items[:index]
	return item, true
}

// 13) Generic function (Go 1.18+)
func GenericFunction[T comparable](slice []T, target T) int {
	for i, v := range slice {
		if v == target {
			return i
		}
	}
	return -1
}

// 14) Function with constraints
func NumericOperation[T ~int | ~int64 | ~float64](a, b T) T {
	return a + b
}

// 15) Higher-order function
func HigherOrderFunction(f func(int) int, values []int) []int {
	result := make([]int, len(values))
	for i, v := range values {
		result[i] = f(v)
	}
	return result
}

// 16) Recursive function
func factorial(n int) int {
	if n <= 1 {
		return 1
	}
	return n * factorial(n-1)
}

// 17) Function with defer
func deferExample(filename string) error {
	fmt.Printf("Opening %s\n", filename)
	defer fmt.Printf("Closing %s\n", filename)

	defer func() {
		if r := recover(); r != nil {
			log.Printf("Recovered from panic: %v", r)
		}
	}()

	// Some work here
	return nil
}

// 18) Function calls as parameters
func functionCallsExample() {
	// Simple function call
	simpleFunction()

	// Function call with parameters
	result := functionWithParams(42, "test", 3.14)
	fmt.Println(result)

	// Function call with multiple return values
	sum, diff := functionWithReturns(10, 5)
	fmt.Printf("Sum: %d, Diff: %d\n", sum, diff)

	// Variadic function call
	total := variadicFunction(100, 1, 2, 3, 4, 5)
	fmt.Printf("Total: %d\n", total)

	// Method calls
	calc := &Calculator{value: 0}
	calc.Add(10)
	fmt.Printf("Calculator value: %d\n", calc.GetValue())

	// Anonymous function call
	multiply := func(x, y int) int { return x * y }
	product := multiply(6, 7)
	fmt.Printf("Product: %d\n", product)

	// Closure call
	doubler := closureExample()
	doubled := doubler(21)
	fmt.Printf("Doubled: %d\n", doubled)
}

// 19) Main function
func main() {
	functionCallsExample()
}
