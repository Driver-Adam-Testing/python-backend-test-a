// Test cases for C# method invocations/call sites
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace Com.Example.Invocations
{
    public class InvocationExamples
    {
        private MethodExamples _instance;
        private Dictionary<string, object> _data;

        public void TestAllInvocations()
        {
            // Constructor invocations
            var obj1 = new MethodExamples();
            var obj2 = new MethodExamples("test", 42);

            // Static method invocation
            MethodExamples.StaticMethod();

            // Instance method invocations
            _instance = new MethodExamples("example", 100);
            string result = _instance.ProcessData("input", 5);

            // Property access/invocations
            _instance.Name = "new name";
            string name = _instance.Name;
            int value = _instance.Value;
            DateTime created = _instance.CreatedAt;
            _instance.Description = "test description";
            string desc = _instance.Description;

            // Generic method invocation
            var stringList = _instance.CreateList<string>("a", "b", "c");
            var intList = _instance.CreateList(1, 2, 3, 4);

            // Override method invocation
            string str = _instance.ToString();

            // Virtual method invocation
            _instance.VirtualMethod();

            // Async method invocation
            Task<string> asyncTask = _instance.AsyncMethod();
            string asyncResult = asyncTask.Result;

            // Method with out parameter invocation
            if (_instance.TryGetValue("key", out int outValue))
            {
                Console.WriteLine($"Got value: {outValue}");
            }

            // Method with ref parameter invocation
            int refValue = 10;
            _instance.ModifyValue(ref refValue);

            // Method with in parameter invocation
            DateTime now = DateTime.Now;
            _instance.ProcessReadOnly(in now);

            // Operator invocations
            var left = new MethodExamples("left", 1);
            var right = new MethodExamples("right", 2);
            var combined = left + right;

            // Conversion operator invocations
            string implicitConversion = _instance;
            int explicitConversion = (int)_instance;

            // System method invocations
            var sb = new System.Text.StringBuilder();
            sb.Append("text");
            string built = sb.ToString();

            // LINQ method invocations (method chaining)
            var numbers = new[] { 1, 2, 3, 4, 5 };
            var evenNumbers = numbers.Where(n => n % 2 == 0).ToList();

            // Delegate invocations
            Action<string> action = s => Console.WriteLine(s);
            action("delegate call");
            action.Invoke("explicit delegate call");

            Func<int, int, int> add = (x, y) => x + y;
            int sum = add(5, 3);
            int sum2 = add.Invoke(10, 20);

            // Event invocations (subscription/unsubscription)
            _instance.ValueChanged += OnValueChanged;
            _instance.ValueChanged -= OnValueChanged;

            // Indexer invocations
            var indexerExample = new IndexerAndEventExamples();
            indexerExample["key1"] = "value1";
            object retrievedValue = indexerExample["key1"];

            // Event handler invocations
            indexerExample.DataChanged += IndexerExample_DataChanged;
            indexerExample.StatusChanged += IndexerExample_StatusChanged;

            // Nested method invocations
            int nestedResult = Math.Max(Math.Min(10, 5), Math.Abs(-3));

            // Interface method invocations
            IExampleInterface interfaceInstance = new ImplementationClass();
            interfaceInstance.InterfaceMethod();

            // Static constructor is invoked implicitly
            StaticConstructorExample.DoSomething();

            // Null-conditional method invocations
            string nullableString = null;
            int? length = nullableString?.Length;
            string trimmed = nullableString?.Trim();

            // Method group conversions (delegate creation)
            Func<string, int> lengthFunc = GetStringLength;
            int len = lengthFunc("hello");

            // Anonymous method invocations
            var anonymous = delegate(string input) { return input.ToUpper(); };
            string upperAnonymous = anonymous("test");

            // Lambda expression invocations
            Func<int, bool> isEven = x => x % 2 == 0;
            bool evenCheck = isEven(4);
        }

        private void OnValueChanged(string value)
        {
            Console.WriteLine($"Value changed: {value}");
        }

        private void IndexerExample_DataChanged(object sender, EventArgs e)
        {
            Console.WriteLine("Data changed");
        }

        private void IndexerExample_StatusChanged(object sender, EventArgs e)
        {
            Console.WriteLine("Status changed");
        }

        private int GetStringLength(string input)
        {
            return input?.Length ?? 0;
        }

        private async Task TestAsyncInvocations()
        {
            // Async/await invocations
            string result = await _instance.AsyncMethod();

            // Task.Run invocation
            await Task.Run(() => Console.WriteLine("Background work"));

            // Task.Delay invocation
            await Task.Delay(100);

            // ConfigureAwait invocation
            string configuredResult = await _instance.AsyncMethod().ConfigureAwait(false);
        }
    }

    // Supporting classes for comprehensive testing
    public class DerivedClass : MethodExamples
    {
        public DerivedClass(string name) : base(name, 0)
        {
        }

        public void BaseMethod()
        {
            // Base constructor invocation via : base() is shown above
            base.VirtualMethod();
        }

        public override void VirtualMethod()
        {
            base.VirtualMethod();
            Console.WriteLine("Derived implementation");
        }

        public override void AbstractMethod()
        {
            Console.WriteLine("Abstract method implementation");
        }
    }

    public interface IExampleInterface
    {
        void InterfaceMethod();
    }

    public class ImplementationClass : IExampleInterface
    {
        public void InterfaceMethod()
        {
            Console.WriteLine("Interface method implementation");
        }
    }

    public static class StaticConstructorExample
    {
        static StaticConstructorExample()
        {
            Console.WriteLine("Static constructor invoked");
        }

        public static void DoSomething()
        {
            Console.WriteLine("Static method");
        }
    }

    // Generic method invocations
    public class GenericInvocations<T, U>
    {
        public void TestGenericCalls()
        {
            // Generic method invocations
            var genericInstance = new GenericInvocations<string, int>();
            genericInstance.GenericMethod("test");

            // Constraint-based generic invocations
            var constraintInstance = new ConstrainedGeneric<List<int>, string>();
        }

        public void GenericMethod(T item)
        {
            Console.WriteLine($"Generic method with {item}");
        }
    }

    public class ConstrainedGeneric<T> where T : ICollection<int>
    {
        public void ProcessCollection(T collection)
        {
            // Method invocations on constrained generic type
            collection.Add(42);
            int count = collection.Count;
            bool contains = collection.Contains(42);
        }
    }
}
