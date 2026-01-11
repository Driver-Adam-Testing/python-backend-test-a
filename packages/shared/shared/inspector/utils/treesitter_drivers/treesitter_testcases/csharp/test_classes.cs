// Test cases for C# class definitions
using System;
using System.Collections.Generic;

namespace Com.Example.Classes
{
    // Simple class
    public class SimpleClass
    {
        private int value;
        private static readonly string CONSTANT = "test";

        public SimpleClass(int value)
        {
            this.value = value;
        }

        public int GetValue()
        {
            return value;
        }

        public void SetValue(int value)
        {
            this.value = value;
        }

        // Nested class
        public static class InnerClass
        {
            private string name;

            public InnerClass(string name)
            {
                this.name = name;
            }
        }
    }

    // Abstract class
    public abstract class AbstractClass
    {
        protected abstract void DoSomething();

        public virtual void VirtualMethod()
        {
            Console.WriteLine("Virtual method");
        }
    }

    // Inheritance and interface implementation
    public class ConcreteClass : AbstractClass, IComparable<ConcreteClass>
    {
        public override void DoSomething()
        {
            Console.WriteLine("Doing something");
        }

        public override void VirtualMethod()
        {
            Console.WriteLine("Overridden virtual method");
        }

        public int CompareTo(ConcreteClass other)
        {
            return 0;
        }
    }

    // Generic class
    public class GenericClass<T, U> where T : class, new() where U : struct
    {
        private T item1;
        private U item2;

        public GenericClass(T item1, U item2)
        {
            this.item1 = item1;
            this.item2 = item2;
        }

        public T GetItem1() => item1;
        public U GetItem2() => item2;
    }

    // Partial class
    public partial class PartialClass
    {
        private string name;

        public string Name
        {
            get => name;
            set => name = value;
        }
    }

    // Static class
    public static class StaticUtilities
    {
        public static void DoStaticWork()
        {
            Console.WriteLine("Static work");
        }
    }

    // Sealed class
    public sealed class SealedClass : AbstractClass
    {
        protected override void DoSomething()
        {
            Console.WriteLine("Sealed implementation");
        }
    }

    // Record class (C# 9+)
    public record PersonRecord(string FirstName, string LastName);

    // Record class with properties
    public record PersonRecordWithProps
    {
        public string FirstName { get; init; }
        public string LastName { get; init; }
        public int Age { get; set; }
    }

    // Class with attributes
    [Serializable]
    [Obsolete("This class is deprecated, use NewAttributedClass instead")]
    public class AttributedClass
    {
        [JsonPropertyName("user_name")]
        public string UserName { get; set; }

        [Required]
        [StringLength(100, MinimumLength = 1)]
        public string Description { get; set; }

        [Range(1, 100)]
        public int Priority { get; set; }

        [JsonIgnore]
        public string InternalData { get; set; }

        [HttpGet("/api/users/{id}")]
        [Authorize(Roles = "Admin")]
        public string GetUser(int id)
        {
            return $"User {id}";
        }
    }
}
