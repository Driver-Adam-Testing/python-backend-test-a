// Test cases for Go global variables and constants (package-level declarations)
package main

import (
	"fmt"
	"time"
)

// 1) Global variables with explicit types
var GlobalInt int = 42
var GlobalString string = "global"

// 2) Private package variables
var packageInt = 42
var packageBool bool = true

// 3) Global variables with type inference
var (
	InferredInt    = 100
	InferredString = "inferred"
	InferredSlice  = []string{"a", "b", "c"}
	InferredMap    = map[string]int{"key": 123}
)

// 4) Private package variables on group
var (
	packageInt    = 100
	packageString = "inferred"
)

// 5) Mixed exported/private in group
var (
	GlobalNumber int = 1
	packageNumber int = 2
)

// 6) Global pointers and complex types
var (
	StringPtr    *string
	PersonPtr    *Person
	IntChan      chan int
	BufferedChan = make(chan string, 5)
)

// 7) Simple constants
const SimpleString = "hello"
const SimpleBool = true

// 8) Private package constants
const packageConstString = "world"
const packageConstInt = 10

// 9) Grouped constants
const (
	MaxUsers    = 1000
	DefaultPort = 8080
	AppName     = "MyApp"
	Version     = "1.0.0"
)

// 10) Private package constants in group
const (
	packageMaxUsers = 1000
	packageAppName  = "MyApp"
)

// 11) Mixed exported/private in group
const (
	GlobalConstNumber = 10
	packageConstNumber = 11
)

// 12) Iota constants
const (
	Sunday = iota
	Monday
	Tuesday
	Wednesday
)

// 13) Iota with expressions (bit flags)
const (
	FlagRead = 1 << iota
	FlagWrite
	FlagExecute
)

// 14) Typed constants
const (
	TypedInt    int     = 123
	TypedFloat  float64 = 3.14159
	TypedString string  = "typed"
)

// 15) Custom type constants
type Status string

const (
	StatusPending   Status = "pending"
	StatusActive    Status = "active"
	StatusCompleted Status = "completed"
)

// 16) Global struct type and variable
type Person struct {
	Name string
	Age  int
}

var (
	DefaultPerson = Person{Name: "Default", Age: 0}
	PersonList    = []Person{
		{Name: "Alice", Age: 30},
		{Name: "Bob", Age: 25},
	}
)

// 17) Configuration constants
const (
	DefaultTimeout = 30 * time.Second
	MaxRetries     = 3
	BufferSize     = 1024
)

// 18) String expression constants
const (
	Greeting = "Hello"
	Target   = "World"
	message  = Greeting + ", " + Target + "!"
)

// Local variable examples (should NOT be parsed as globals)
func localExamples() {
	// Local constants
	const localConst = "local constant"
	const (
		localInt  = 10
		localBool = false
	)

	// Local variables
	localVar := "local variable"
	x, y := 1, 2
	var localSlice []int
	var localMap map[string]int

	// These should not appear in global symbol parsing
	fmt.Printf("Local examples: %s, %s, %d, %t, %d, %d\n",
		localConst, localVar, localInt, localBool, x, y)
	fmt.Printf("Local collections: %v, %v\n", localSlice, localMap)
}

func main() {
	fmt.Printf("Global variables: %d, %s, %t\n", GlobalInt, GlobalString, GlobalBool)
	fmt.Printf("Inferred: %d, %s, %v, %v\n", InferredInt, InferredString, InferredSlice, InferredMap)
	fmt.Printf("Constants: %s, %d, %t\n", SimpleString, SimpleInt, SimpleBool)
	fmt.Printf("App: %s v%s (port: %d)\n", AppName, Version, DefaultPort)
	fmt.Printf("Days: %d, %d, %d\n", Sunday, Monday, Tuesday)
	fmt.Printf("Flags: %d, %d, %d\n", FlagRead, FlagWrite, FlagExecute)
	fmt.Printf("Status: %s\n", StatusActive)
	fmt.Printf("Person: %+v\n", DefaultPerson)
	fmt.Printf("Message: %s\n", Message)

	localExamples()
}
