// Test cases for C# struct definitions
using System;
using System.Collections.Generic;

namespace Com.Example.Structs
{
    // Simple struct
    public struct Point
    {
        public int X;
        public int Y;

        public Point(int x, int y)
        {
            X = x;
            Y = y;
        }

        public override string ToString()
        {
            return $"({X}, {Y})";
        }
    }

    // Struct with properties
    public struct Rectangle
    {
        public int Width { get; set; }
        public int Height { get; set; }

        // Computed property
        public int Area => Width * Height;
        public int Perimeter => 2 * (Width + Height);

        public Rectangle(int width, int height)
        {
            Width = width;
            Height = height;
        }

        public bool IsSquare => Width == Height;
    }

    // Readonly struct (C# 7.2+)
    public readonly struct ImmutablePoint
    {
        public readonly int X;
        public readonly int Y;

        public ImmutablePoint(int x, int y)
        {
            X = x;
            Y = y;
        }

        // Methods in readonly struct must not modify state
        public double DistanceFromOrigin()
        {
            return Math.Sqrt(X * X + Y * Y);
        }

        public ImmutablePoint Translate(int dx, int dy)
        {
            return new ImmutablePoint(X + dx, Y + dy);
        }
    }

    // Ref struct (C# 7.2+) - can only live on stack
    public ref struct StackOnlyStruct
    {
        private readonly Span<byte> data;

        public StackOnlyStruct(Span<byte> data)
        {
            this.data = data;
        }

        public byte this[int index]
        {
            get => data[index];
            set => data[index] = value;
        }

        public int Length => data.Length;
    }

    // Generic struct
    public struct GenericPair<T, U> where T : struct where U : class
    {
        public T First { get; set; }
        public U Second { get; set; }

        public GenericPair(T first, U second)
        {
            First = first;
            Second = second;
        }

        public void Deconstruct(out T first, out U second)
        {
            first = First;
            second = Second;
        }
    }

    // Struct implementing interfaces
    public struct Complex : IEquatable<Complex>, IComparable<Complex>
    {
        public double Real { get; }
        public double Imaginary { get; }

        public Complex(double real, double imaginary)
        {
            Real = real;
            Imaginary = imaginary;
        }

        // Operator overloading
        public static Complex operator +(Complex left, Complex right)
        {
            return new Complex(left.Real + right.Real, left.Imaginary + right.Imaginary);
        }

        public static Complex operator -(Complex left, Complex right)
        {
            return new Complex(left.Real - right.Real, left.Imaginary - right.Imaginary);
        }

        public static Complex operator *(Complex left, Complex right)
        {
            return new Complex(
                left.Real * right.Real - left.Imaginary * right.Imaginary,
                left.Real * right.Imaginary + left.Imaginary * right.Real
            );
        }

        // Equality implementation
        public bool Equals(Complex other)
        {
            return Real.Equals(other.Real) && Imaginary.Equals(other.Imaginary);
        }

        public override bool Equals(object obj)
        {
            return obj is Complex other && Equals(other);
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Real, Imaginary);
        }

        public static bool operator ==(Complex left, Complex right)
        {
            return left.Equals(right);
        }

        public static bool operator !=(Complex left, Complex right)
        {
            return !left.Equals(right);
        }

        // Comparison implementation
        public int CompareTo(Complex other)
        {
            double thisMagnitude = Math.Sqrt(Real * Real + Imaginary * Imaginary);
            double otherMagnitude = Math.Sqrt(other.Real * other.Real + other.Imaginary * other.Imaginary);
            return thisMagnitude.CompareTo(otherMagnitude);
        }

        public override string ToString()
        {
            if (Imaginary >= 0)
                return $"{Real} + {Imaginary}i";
            else
                return $"{Real} - {Math.Abs(Imaginary)}i";
        }
    }

    // Struct with nested types
    public struct Container
    {
        private readonly object[] items;

        public Container(params object[] items)
        {
            this.items = items ?? new object[0];
        }

        // Nested enum
        public enum ContainerType
        {
            Array,
            List,
            Dictionary
        }

        // Nested struct
        public struct Metadata
        {
            public ContainerType Type { get; set; }
            public DateTime CreatedAt { get; set; }
            public string Description { get; set; }
        }

        public Metadata GetMetadata()
        {
            return new Metadata
            {
                Type = ContainerType.Array,
                CreatedAt = DateTime.Now,
                Description = $"Container with {items.Length} items"
            };
        }
    }

    // Struct with constants and static members
    public struct MathConstants
    {
        public const double PI = 3.14159265358979323846;
        public const double E = 2.71828182845904523536;

        public static readonly MathConstants Empty = new MathConstants();

        private readonly double value;

        public MathConstants(double value)
        {
            this.value = value;
        }

        public double Value => value;

        // Static methods
        public static double DegreesToRadians(double degrees)
        {
            return degrees * PI / 180.0;
        }

        public static double RadiansToDegrees(double radians)
        {
            return radians * 180.0 / PI;
        }
    }

    // Record struct (C# 10+)
    public record struct PersonInfo(string Name, int Age)
    {
        public string Email { get; set; } = "";

        // Computed property
        public string DisplayName => $"{Name} ({Age})";

        // Method
        public bool IsAdult() => Age >= 18;
    }

    // Readonly record struct (C# 10+)
    public readonly record struct ImmutablePersonInfo(string Name, int Age)
    {
        public string DisplayName => $"{Name} ({Age})";
        public bool IsAdult() => Age >= 18;
    }

    // Regular record (not a struct) - should not be parsed when looking for structs
    public record Employee(string Name, string Department);

    // Usage examples
    public class StructExamples
    {
        // Nested struct with multiple modifiers
        private protected readonly ref struct MultiModifierStruct
        {
            private readonly Span<int> data;

            public MultiModifierStruct(Span<int> data)
            {
                this.data = data;
            }

            public int Length => data.Length;

            public ref int this[int index] => ref data[index];
        }
        public void UseStructs()
        {
            // Simple struct usage
            var point = new Point(10, 20);
            Console.WriteLine($"Point: {point}");

            // Struct with properties
            var rect = new Rectangle(5, 10);
            Console.WriteLine($"Rectangle area: {rect.Area}");

            // Readonly struct
            var immutablePoint = new ImmutablePoint(3, 4);
            double distance = immutablePoint.DistanceFromOrigin();

            // Generic struct
            var pair = new GenericPair<int, string>(42, "Hello");
            var (number, text) = pair; // Deconstruction

            // Complex struct with operators
            var c1 = new Complex(1, 2);
            var c2 = new Complex(3, 4);
            var sum = c1 + c2;

            // Record struct
            var person = new PersonInfo("Alice", 25) { Email = "alice@example.com" };
            Console.WriteLine($"Person: {person.DisplayName}");

            // Struct equality
            var point1 = new Point(1, 2);
            var point2 = new Point(1, 2);
            bool areEqual = point1.Equals(point2); // True for value types
        }
    }
}
