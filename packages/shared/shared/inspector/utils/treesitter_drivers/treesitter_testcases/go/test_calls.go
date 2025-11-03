// Test cases for Go function and method calls
package main

import (
	"fmt"
	"math"
	"strings"
	"time"
)

// Test types for method calls
type Calculator struct {
	value float64
}

type Counter struct {
	count int
}

// Methods for testing
func (c *Calculator) Add(x float64) {
	c.value += x
}

func (c Calculator) GetValue() float64 {
	return c.value
}

func (c *Counter) Increment() {
	c.count++
}

func (c Counter) Value() int {
	return c.count
}

// 1) Basic function calls
func basicCalls() {
	// Built-in function calls
	length := len("hello")
	slice := make([]int, 3)
	fmt.Printf("Length: %d, Slice: %v\n", length, slice)

	// Standard library calls
	abs := math.Abs(-42.5)
	upper := strings.ToUpper("hello")
	fmt.Printf("Abs: %.1f, Upper: %s\n", abs, upper)
}

// 2) Method calls on structs
func methodCalls() {
	// Pointer receiver methods
	calc := &Calculator{value: 10}
	calc.Add(5)
	fmt.Printf("Calculator value: %.1f\n", calc.GetValue())

	// Method chaining
	counter := &Counter{}
	counter.Increment()
	counter.Increment()
	fmt.Printf("Counter value: %d\n", counter.Value())
}

// 3) Function calls with multiple arguments and returns
func multipleArgsReturns() {
	// Multiple arguments
	fmt.Printf("Name: %s, Age: %d\n", "Alice", 25)
	joined := strings.Join([]string{"a", "b", "c"}, "-")
	fmt.Printf("Joined: %s\n", joined)

	// Multiple return values
	quotient, remainder := divide(17, 5)
	fmt.Printf("17 ÷ 5 = %d remainder %d\n", quotient, remainder)
}

func divide(a, b int) (int, int) {
	return a / b, a % b
}

// 4) Variadic function calls
func variadicCalls() {
	result1 := sum(1, 2, 3, 4, 5)
	result2 := sum()
	numbers := []int{1, 2, 3}
	result3 := sum(numbers...)
	fmt.Printf("Sums: %d, %d, %d\n", result1, result2, result3)
}

func sum(numbers ...int) int {
	total := 0
	for _, n := range numbers {
		total += n
	}
	return total
}

// 5) Anonymous function calls
func anonymousCalls() {
	// Immediate call
	result := func(x, y int) int {
		return x * y
	}(5, 6)
	fmt.Printf("Anonymous result: %d\n", result)

	// Closure
	multiplier := 10
	scale := func(x int) int {
		return x * multiplier
	}
	fmt.Printf("Scaled: %d\n", scale(5))
}

// 6) Generic function calls
func genericCalls() {
	intMax := Max(10, 20)
	stringMax := Max("apple", "banana")
	fmt.Printf("Max int: %d, string: %s\n", intMax, stringMax)

	// Explicit type parameter
	explicitMax := Max[float64](1.5, 2.5)
	fmt.Printf("Explicit max: %.1f\n", explicitMax)
}

func Max[T comparable](a, b T) T {
	if fmt.Sprintf("%v", a) > fmt.Sprintf("%v", b) {
		return a
	}
	return b
}

func sendValues(ch chan<- int) {
	ch <- 1
	ch <- 2
	close(ch)
}

// 7) Goroutine and channel calls
func goroutineCalls() {
	ch := make(chan int, 2)

	// Goroutine with standard function
	go sendValues(ch)

	// Channel operations
	for value := range ch {
		fmt.Printf("Received: %d\n", value)
	}

	// Goroutine with anonymous function
	timeoutCh := make(chan string, 1)
	go func() {
		time.Sleep(10 * time.Millisecond)
		timeoutCh <- "message"
	}()

	select {
	case msg := <-timeoutCh:
		fmt.Printf("Message: %s\n", msg)
	case <-time.After(50 * time.Millisecond):
		fmt.Println("Timeout")
	}
}

// 8) Nested and chained calls
func nestedCalls() {
	// Nested function calls
	result := fmt.Sprintf("Length: %d", len(strings.ToUpper("hello")))
	fmt.Println(result)

	// Method chaining
	timestamp := time.Now().Add(1 * time.Hour).Format("15:04:05")
	fmt.Printf("Future time: %s\n", timestamp)
}

func main() {
	basicCalls()

	methodCalls()

	multipleArgsReturns()

	variadicCalls()

	anonymousCalls()

	genericCalls()

	goroutineCalls()

	errorCalls()

	nestedCalls()
}
