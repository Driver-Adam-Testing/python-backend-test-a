// Test cases for Go data structures (structs, type aliases, and new types)
package main

import (
	"fmt"
	"time"
)

// 1) Simple struct
type SimpleStruct struct {
	Name  string
	Value int
}

type simpleStructPrivate struct {
	Name string
	Value int
}

// 2) Struct with various field types
type ComplexStruct struct {
	ID          uint64
	Name        string
	IsActive    bool
	Score       float64
	Tags        []string
	Metadata    map[string]interface{}
	CreatedAt   time.Time
	UpdatedAt   *time.Time
	NestedStruct SimpleStruct
}

// 3) Struct with embedded fields (composition)
type BaseStruct struct {
	ID   int
	Name string
}

type ExtendedStruct struct {
	BaseStruct // Embedded struct
	Extra      string
}

// 4) Struct with anonymous fields
type AnonymousFieldStruct struct {
	string // Anonymous string field
	int    // Anonymous int field
	bool   // Anonymous bool field
}

// 5) Struct with struct tags (for JSON, etc.)
type TaggedStruct struct {
	ID          int       `json:"id" db:"id" validate:"required"`
	Name        string    `json:"name" db:"name" validate:"required,min=1,max=100"`
	Email       string    `json:"email" db:"email" validate:"required,email"`
	IsActive    bool      `json:"is_active" db:"is_active"`
	Score       float64   `json:"score,omitempty" db:"score"`
	Tags        []string  `json:"tags,omitempty" db:"tags"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
	PrivateData string    `json:"-" db:"-"` // Ignored in JSON
}

// 6) Empty struct
type EmptyStruct struct{}

// 7) Struct with pointer fields
type PointerStruct struct {
	Value     *int
	Name      *string
	Nested    *SimpleStruct
	SlicePtr  *[]string
	MapPtr    *map[string]int
}

// 8) Struct with function fields
type FunctionStruct struct {
	Handler    func(string) error
	Callback   func(int, int) int
	Validator  func(interface{}) bool
	Middleware func(func()) func()
}

// 9) Struct with channel fields
type ChannelStruct struct {
	Input  <-chan string // Receive-only channel
	Output chan<- int    // Send-only channel
	Bidirectional chan bool
}

// 10) Struct with interface fields
type InterfaceStruct struct {
	Processor interface{} // Empty interface
	Logger    fmt.Stringer
	Closer    interface {
		Close() error
	}
}

// 11) Generic struct (Go 1.18+)
type GenericStruct[T any] struct {
	Value T
	Slice []T
	Map   map[string]T
}

type GenericConstrainedStruct[T comparable] struct {
	Key   T
	Value T
	Set   map[T]bool
}

// 12) Struct with generic constraints
type NumericStruct[T ~int | ~int64 | ~float32 | ~float64] struct {
	Values []T
	Sum    T
	Avg    T
}

// 13) Nested structs
type NestedStructs struct {
	Person struct {
		Name string
		Age  int
		Address struct {
			Street  string
			City    string
			Country string
			Coordinates struct {
				Lat float64
				Lng float64
			}
		}
	}
	Company struct {
		Name      string
		Employees int
	}
}

// 14) Struct with multiple embedded structs
type MultipleEmbedded struct {
	BaseStruct
	ComplexStruct
	Timestamp time.Time
}

// 17) Struct initialization examples
func structInitializationExamples() {
	// Zero value initialization
	var s1 SimpleStruct
	fmt.Printf("Zero value: %+v\n", s1)

	// Literal initialization
	s2 := SimpleStruct{
		Name:  "example",
		Value: 42,
	}
	fmt.Printf("Literal: %+v\n", s2)

	// Pointer initialization
	s3 := &SimpleStruct{
		Name:  "pointer example",
		Value: 100,
	}
	fmt.Printf("Pointer: %+v\n", s3)

	// Partial initialization
	s4 := ComplexStruct{
		ID:   1,
		Name: "partial",
		Tags: []string{"tag1", "tag2"},
	}
	fmt.Printf("Partial: %+v\n", s4)

	// Anonymous struct
	anonymous := struct {
		X int
		Y int
	}{
		X: 10,
		Y: 20,
	}
	fmt.Printf("Anonymous: %+v\n", anonymous)

	// Generic struct initialization
	intGeneric := GenericStruct[int]{
		Value: 42,
		Slice: []int{1, 2, 3},
		Map:   map[string]int{"key": 123},
	}
	fmt.Printf("Generic int: %+v\n", intGeneric)

	stringGeneric := GenericStruct[string]{
		Value: "hello",
		Slice: []string{"a", "b", "c"},
		Map:   map[string]string{"key": "value"},
	}
	fmt.Printf("Generic string: %+v\n", stringGeneric)
}

// 18) Struct with bit fields simulation (using constants)
type BitFieldStruct struct {
	Flags uint32
}

const (
	FlagA = 1 << iota
	FlagB
	FlagC
	FlagD
)

// 19) Type aliases - alternative names for existing types (using =)
type UserID = int64
type JSONData = map[string]interface{}

// 20) New types - distinct types based on existing types (no =)
type Temperature float64
type Distance int
type Status string

// Constants for new types
const (
	StatusActive   Status = "active"
	StatusInactive Status = "inactive"
	StatusPending  Status = "pending"
)

func (b *BitFieldStruct) SetFlag(flag uint32) {
	b.Flags |= flag
}

func (b *BitFieldStruct) HasFlag(flag uint32) bool {
	return b.Flags&flag != 0
}

func main() {
	structInitializationExamples()

	// Test bit fields
	bf := BitFieldStruct{}
	bf.SetFlag(FlagA | FlagC)
	fmt.Printf("Has FlagA: %t\n", bf.HasFlag(FlagA))
	fmt.Printf("Has FlagB: %t\n", bf.HasFlag(FlagB))
	fmt.Printf("Has FlagC: %t\n", bf.HasFlag(FlagC))

	// Test shapes
	shapes := []Shape{
		Rectangle{Width: 10, Height: 5},
		Circle{Radius: 3},
	}

	for _, shape := range shapes {
		fmt.Printf("Area: %.2f, Perimeter: %.2f\n", shape.Area(), shape.Perimeter())
	}
}
