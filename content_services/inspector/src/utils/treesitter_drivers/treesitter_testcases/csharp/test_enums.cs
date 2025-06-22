// Test cases for C# enum definitions
using System;

namespace Com.Example.Enums
{
    // Simple enum
    public enum Color
    {
        Red,
        Green,
        Blue
    }

    // Enum with explicit values
    public enum Status
    {
        Pending = 0,
        InProgress = 1,
        Completed = 2,
        Failed = 3,
        Cancelled = 4
    }

    // Enum with different underlying type
    public enum Priority : byte
    {
        Low = 1,
        Medium = 2,
        High = 3,
        Critical = 4
    }

    // Flags enum
    [Flags]
    public enum FileAccess
    {
        None = 0,
        Read = 1,
        Write = 2,
        Execute = 4,
        ReadWrite = Read | Write,
        All = Read | Write | Execute
    }

    // Enum with string values (using attributes)
    public enum LogLevel
    {
        Trace,
        Debug,
        Information,
        Warning,
        Error,
        Critical
    }

    // Enum with methods (via extension methods)
    public enum DayOfWeek
    {
        Monday = 1,
        Tuesday = 2,
        Wednesday = 3,
        Thursday = 4,
        Friday = 5,
        Saturday = 6,
        Sunday = 7
    }

    // Enum with calculated values
    public enum HttpStatusCode
    {
        // Information responses
        Continue = 100,
        SwitchingProtocols = 101,

        // Success responses
        OK = 200,
        Created = 201,
        Accepted = 202,

        // Client error responses
        BadRequest = 400,
        Unauthorized = 401,
        Forbidden = 403,
        NotFound = 404,

        // Server error responses
        InternalServerError = 500,
        NotImplemented = 501,
        BadGateway = 502,
        ServiceUnavailable = 503
    }

    // Complex enum with long values
    public enum Permission : long
    {
        None = 0L,
        ReadData = 1L,
        WriteData = 2L,
        ExecuteFile = 4L,
        Delete = 8L,
        ReadPermissions = 16L,
        ChangePermissions = 32L,
        TakeOwnership = 64L,
        FullControl = ReadData | WriteData | ExecuteFile | Delete | ReadPermissions | ChangePermissions | TakeOwnership
    }

    // Usage examples
    public class EnumExamples
    {
        // Enum with multiple modifiers (nested inside class)
        protected internal enum SecurityLevel
        {
            None = 0,
            Low = 1,
            Medium = 2,
            High = 3,
            Critical = 4
        }

        public void UseEnums()
        {
            // Simple enum usage
            Color favoriteColor = Color.Blue;

            // Flags enum usage
            FileAccess access = FileAccess.Read | FileAccess.Write;
            bool canRead = (access & FileAccess.Read) == FileAccess.Read;

            // Enum parsing
            if (Enum.TryParse<Status>("InProgress", out Status status))
            {
                Console.WriteLine($"Parsed status: {status}");
            }

            // Enum to string
            string statusName = Status.Completed.ToString();

            // Get all enum values
            foreach (Priority priority in Enum.GetValues<Priority>())
            {
                Console.WriteLine($"Priority: {priority} = {(byte)priority}");
            }

            // Switch on enum
            string message = GetStatusMessage(Status.InProgress);
            Console.WriteLine(message);
        }

        private string GetStatusMessage(Status status)
        {
            return status switch
            {
                Status.Pending => "Task is pending",
                Status.InProgress => "Task is in progress",
                Status.Completed => "Task is completed",
                Status.Failed => "Task has failed",
                Status.Cancelled => "Task was cancelled",
                _ => "Unknown status"
            };
        }
    }

    // Extension methods for enums
    public static class DayOfWeekExtensions
    {
        public static bool IsWeekend(this DayOfWeek day)
        {
            return day == DayOfWeek.Saturday || day == DayOfWeek.Sunday;
        }

        public static bool IsWeekday(this DayOfWeek day)
        {
            return !day.IsWeekend();
        }
    }
}
