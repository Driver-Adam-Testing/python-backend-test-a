// Test cases for C# using directives (imports)
using System;
using System.Collections.Generic;
using System.Linq;

// Using with alias
using Dict = System.Collections.Generic.Dictionary<string, object>;
using StringBuilder = System.Text.StringBuilder;
using Sys = System;

// Static using
using static System.Math;
using static System.Console;

// Global using (C# 10+)
global using System.Threading.Tasks;

// Using for file-scoped namespace
using MyAlias = System.Collections.Concurrent.ConcurrentDictionary<string, int>;

// Global namespace using (to avoid namespace conflicts)
using global::System.Text.Json;
using JsonSerializer = global::System.Text.Json.JsonSerializer;

namespace Com.Example.Usings
{
    public class UsingExamples
    {
        public void UseImports()
        {
            // Using System types
            var list = new List<string>();
            var date = DateTime.Now;

            // Using aliases
            var dict = new Dict();
            var sb = new StringBuilder();

            // Using static methods
            var result = Sqrt(16);
            WriteLine("Hello World");

            // Using global
            var task = Task.CompletedTask;

            // Using alias
            var concurrent = new MyAlias();

            // Using global namespace reference
            var jsonOptions = new JsonSerializerOptions();
            string json = JsonSerializer.Serialize(new { Name = "Test" });
        }
    }
}
