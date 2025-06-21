// Test cases for C# method definitions
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace Com.Example.Methods
{
    public class MethodExamples
    {
        // Constructor
        public MethodExamples()
        {
        }

        // Parameterized constructor
        public MethodExamples(string name, int value)
        {
            Name = name;
            Value = value;
        }

        // Properties
        public string Name { get; set; }
        public int Value { get; private set; }

        // Auto-implemented property with initializer
        public DateTime CreatedAt { get; } = DateTime.Now;

        // Property with backing field
        private string _description;
        public string Description
        {
            get => _description ?? "No description";
            set => _description = value?.Trim();
        }

        // Static method
        public static void StaticMethod()
        {
            Console.WriteLine("Static method");
        }

        // Instance method with parameters
        public string ProcessData(string input, int count)
        {
            var result = new System.Text.StringBuilder();
            for (int i = 0; i < count; i++)
            {
                result.Append(input);
            }
            return result.ToString();
        }

        // Private method
        private void PrivateHelper()
        {
            // Implementation
        }

        // Method with generic parameters
        public List<T> CreateList<T>(params T[] items)
        {
            return new List<T>(items);
        }

        // Override method
        public override string ToString()
        {
            return $"MethodExamples: {Name}";
        }

        // Virtual method
        public virtual void VirtualMethod()
        {
            Console.WriteLine("Virtual method");
        }

        // Abstract method (would be in abstract class)
        public abstract void AbstractMethod();

        // Async method
        public async Task<string> AsyncMethod()
        {
            await Task.Delay(100);
            return "Async result";
        }

        // Method with out parameter
        public bool TryGetValue(string key, out int value)
        {
            value = 42;
            return true;
        }

        // Method with ref parameter
        public void ModifyValue(ref int value)
        {
            value *= 2;
        }

        // Method with in parameter (C# 7.2+)
        public void ProcessReadOnly(in DateTime timestamp)
        {
            Console.WriteLine($"Processing: {timestamp}");
        }

        // Extension method (must be static in static class)
        public static string Reverse(this string str) => new string(str.Reverse().ToArray());

        // Operator overloading
        public static MethodExamples operator +(MethodExamples left, MethodExamples right)
        {
            return new MethodExamples(left.Name + right.Name, left.Value + right.Value);
        }

        // Implicit conversion operator
        public static implicit operator string(MethodExamples obj)
        {
            return obj.ToString();
        }

        // Explicit conversion operator
        public static explicit operator int(MethodExamples obj)
        {
            return obj.Value;
        }

        // Finalizer/destructor
        ~MethodExamples()
        {
            // Cleanup code
        }

        // Event
        public event Action<string> ValueChanged;

        // Method with expression body
        public string GetDisplayName() => $"{Name} ({Value})";

        // Local function example
        public int CalculateComplex(int x, int y)
        {
            int LocalHelper(int a, int b)
            {
                return a * b + 10;
            }

            return LocalHelper(x, y) + LocalHelper(y, x);
        }
    }

    // Static class with extension methods
    public static class StringExtensions
    {
        public static string Reverse(this string str)
        {
            if (string.IsNullOrEmpty(str))
                return str;

            char[] chars = str.ToCharArray();
            Array.Reverse(chars);
            return new string(chars);
        }

        public static bool IsNullOrWhiteSpace(this string str)
        {
            return string.IsNullOrWhiteSpace(str);
        }
    }
}
