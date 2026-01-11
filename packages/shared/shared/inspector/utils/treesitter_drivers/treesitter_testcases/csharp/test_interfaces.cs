// Test cases for C# interface definitions
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace Com.Example.Interfaces
{
    // Simple interface
    public interface IDrawable
    {
        void Draw();
        void Draw(int x, int y);

        // Property
        string Name { get; set; }

        // Read-only property
        int Width { get; }

        // Event
        event Action<string> DrawCompleted;
    }

    // Generic interface
    public interface IRepository<T> where T : class
    {
        Task<T> GetByIdAsync(int id);
        Task<IEnumerable<T>> GetAllAsync();
        Task<T> AddAsync(T entity);
        Task UpdateAsync(T entity);
        Task DeleteAsync(int id);
    }

    // Interface inheritance
    public interface IResizable : IDrawable
    {
        void Resize(int width, int height);

        // New property
        int Height { get; }

        // Nested interface
        interface IResizeListener
        {
            void OnResize(int oldWidth, int oldHeight, int newWidth, int newHeight);
        }
    }

    // Interface with default implementation (C# 8.0+)
    public interface ICalculator
    {
        int Add(int a, int b);
        int Subtract(int a, int b);

        // Default implementation
        int Multiply(int a, int b) => a * b;

        // Static method
        static int Divide(int a, int b)
        {
            if (b == 0) throw new DivideByZeroException();
            return a / b;
        }

        // Protected method (C# 8.0+)
        protected int Square(int x) => x * x;
    }

    // Multiple interface inheritance
    public interface IAdvancedDrawable : IDrawable, IResizable
    {
        void DrawWithEffects();
        bool IsVisible { get; set; }
    }

    // Interface with generic constraints
    public interface IComparable<in T>
    {
        int CompareTo(T other);
    }

    // Covariant interface
    public interface IProducer<out T>
    {
        T Produce();
        IEnumerable<T> ProduceMany();
    }

    // Contravariant interface
    public interface IConsumer<in T>
    {
        void Consume(T item);
        void ConsumeMany(IEnumerable<T> items);
    }

    // Interface with indexer
    public interface IIndexable<T>
    {
        T this[int index] { get; set; }
        int Count { get; }
    }

    // Functional interface equivalent
    public interface IProcessor<TInput, TOutput>
    {
        TOutput Process(TInput input);
    }

    // Internal interface
    internal interface IInternalService
    {
        void DoInternalWork();
        string InternalProperty { get; }
    }

    // Partial interface
    public partial interface IPartialInterface
    {
        void Method1();
        string Property1 { get; set; }
    }

    public partial interface IPartialInterface
    {
        void Method2();
        int Property2 { get; }
    }

    // Unsafe interface (requires unsafe context)
    public unsafe interface IUnsafeOperations
    {
        void* GetPointer();
        void ProcessPointer(byte* data, int length);
    }

    // Nested interfaces with various modifiers
    public interface IOuterInterface
    {
        void OuterMethod();

        // Private nested interface
        private interface IPrivateNested
        {
            void PrivateNestedMethod();
        }

        // Protected nested interface
        protected interface IProtectedNested
        {
            void ProtectedNestedMethod();
        }
    }

    // Class with nested interfaces demonstrating different accessibility
    public class ClassWithNestedInterfaces
    {
        // Public nested interface
        public interface IPublicNested
        {
            void PublicMethod();
        }

        // Internal nested interface
        internal interface IInternalNested
        {
            void InternalMethod();
        }

        // Protected internal nested interface
        protected internal interface IProtectedInternalNested
        {
            void ProtectedInternalMethod();
        }

        // Private protected nested interface
        private protected interface IPrivateProtectedNested
        {
            void PrivateProtectedMethod();
        }
    }

    // Interface with mixed modifiers and complex nesting
    internal partial interface IComplexInterface
    {
        void ComplexMethod();

        // Nested interface within partial interface
        public interface INestedInPartial
        {
            void NestedPartialMethod();

            // Deeply nested interface
            private interface IDeeplyNested
            {
                void DeeplyNestedMethod();
            }
        }
    }

    // Example implementations
    public class Rectangle : IAdvancedDrawable
    {
        public string Name { get; set; }
        public int Width { get; private set; }
        public int Height { get; private set; }
        public bool IsVisible { get; set; } = true;

        public event Action<string> DrawCompleted;

        public void Draw()
        {
            Console.WriteLine($"Drawing rectangle: {Name}");
            DrawCompleted?.Invoke("Draw completed");
        }

        public void Draw(int x, int y)
        {
            Console.WriteLine($"Drawing rectangle at ({x}, {y})");
        }

        public void Resize(int width, int height)
        {
            Width = width;
            Height = height;
        }

        public void DrawWithEffects()
        {
            if (IsVisible)
            {
                Console.WriteLine("Drawing with effects");
            }
        }
    }

    // Generic implementation
    public class InMemoryRepository<T> : IRepository<T> where T : class
    {
        private readonly List<T> _items = new List<T>();

        public Task<T> GetByIdAsync(int id)
        {
            // Simplified implementation
            return Task.FromResult(_items.Count > id ? _items[id] : null);
        }

        public Task<IEnumerable<T>> GetAllAsync()
        {
            return Task.FromResult<IEnumerable<T>>(_items);
        }

        public Task<T> AddAsync(T entity)
        {
            _items.Add(entity);
            return Task.FromResult(entity);
        }

        public Task UpdateAsync(T entity)
        {
            // Simplified - would need proper ID matching
            return Task.CompletedTask;
        }

        public Task DeleteAsync(int id)
        {
            if (id < _items.Count)
                _items.RemoveAt(id);
            return Task.CompletedTask;
        }
    }
}
