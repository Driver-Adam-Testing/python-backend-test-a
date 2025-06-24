// Test cases for C# namespace definitions
using System;
using System.Collections.Generic;

// Global namespace declarations
public class GlobalClass
{
    public void GlobalMethod()
    {
        Console.WriteLine("Global method");
    }
}

// Traditional namespace
namespace Com.Example.Traditional
{
    public class TraditionalClass
    {
        public void TraditionalMethod()
        {
            Console.WriteLine("Traditional namespace method");
        }
    }

    // Nested namespace (traditional style)
    namespace Nested
    {
        public class NestedClass
        {
            public void NestedMethod()
            {
                Console.WriteLine("Nested namespace method");
            }
        }

        namespace DeeplyNested
        {
            public class DeeplyNestedClass
            {
                public void DeeplyNestedMethod()
                {
                    Console.WriteLine("Deeply nested method");
                }
            }
        }
    }
}

// File-scoped namespace (C# 10+)
namespace Com.Example.FileScoped;

public class FileScopedClass
{
    public void FileScopedMethod()
    {
        Console.WriteLine("File-scoped namespace method");
    }
}

public interface IFileScopedInterface
{
    void InterfaceMethod();
}

public enum FileScopedEnum
{
    Value1,
    Value2,
    Value3
}

public struct FileScopedStruct
{
    public int Value { get; set; }

    public FileScopedStruct(int value)
    {
        Value = value;
    }
}

// Multiple classes in file-scoped namespace
public static class FileScopedUtilities
{
    public static void UtilityMethod()
    {
        Console.WriteLine("File-scoped utility method");
    }

    public static string FormatValue(object value)
    {
        return value?.ToString() ?? "null";
    }
}

public record FileScopedRecord(string Name, int Value);

// Abstract class in file-scoped namespace
public abstract class FileScopedAbstractClass
{
    protected abstract void AbstractMethod();

    public virtual void VirtualMethod()
    {
        Console.WriteLine("Virtual method in file-scoped namespace");
    }
}

// Implementation of abstract class
public class FileScopedConcreteClass : FileScopedAbstractClass, IFileScopedInterface
{
    protected override void AbstractMethod()
    {
        Console.WriteLine("Implemented abstract method");
    }

    public void InterfaceMethod()
    {
        Console.WriteLine("Implemented interface method");
    }
}
