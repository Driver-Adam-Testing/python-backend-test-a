// Test cases for Go interface definitions
package main

import (
	"fmt"
	"io"
	"time"
)

// 1) Simple interface
type SimpleInterface interface {
	DoSomething()
}

// 2) Interface with multiple methods
type complexPrivateInterface interface {
	Read(data []byte) (int, error)
	Write(data []byte) (int, error)
	Close() error
}

// 3) Interface with method parameters and return types
type ProcessorInterface interface {
	Process(input string) (output string, err error)
	Validate(data interface{}) bool
	Configure(options map[string]interface{}) error
}

// 4) Empty interface (any type)
type anyInterface interface{}
type AnyInterface interface{}

// 5) Interface composition (embedding)
type ReadWriter interface {
	io.Reader
	io.Writer
}

type ReadWriteCloser interface {
	io.Reader
	io.Writer
	io.Closer
}

// 6) Interface with embedded interfaces and additional methods
type ExtendedInterface interface {
	ReadWriteCloser
	Flush() error
	Sync() error
}

// 7) Generic interface (Go 1.18+)
type GenericInterface[T any] interface {
	Process(item T) T
	Compare(a, b T) int
}

// 8) Interface with type constraints
type ComparableInterface[T comparable] interface {
	Equal(other T) bool
	Less(other T) bool
}

// 9) Interface with union constraints
type NumericInterface[T ~int | ~int64 | ~float32 | ~float64] interface {
	Add(other T) T
	Subtract(other T) T
	Multiply(other T) T
	Divide(other T) T
}

// 10) Interface with method sets
type Stringer interface {
	String() string
}

type GoStringer interface {
	GoString() string
}

type FormatterInterface interface {
	Stringer
	GoStringer
	Format(verb rune, flag int) string
}

// 11) Interface with variadic methods
type VariadicInterface interface {
	Process(items ...string) error
	Combine(separator string, items ...interface{}) string
}

// 12) Interface with channel methods
type ChannelInterface interface {
	Send(ch chan<- interface{}, value interface{}) error
	Receive(ch <-chan interface{}) (interface{}, error)
	Close(ch chan interface{})
}

// 13) Context-like interface
type ContextLikeInterface interface {
	Deadline() (deadline time.Time, ok bool)
	Done() <-chan struct{}
	Err() error
	Value(key interface{}) interface{}
}

// 14) Event handler interface
type EventHandler interface {
	OnStart() error
	OnStop() error
	OnEvent(eventType string, data interface{}) error
}

// 15) Repository pattern interface
type Repository[T any] interface {
	Create(item T) error
	GetByID(id string) (T, error)
	Update(item T) error
	Delete(id string) error
	List(offset, limit int) ([]T, error)
}
