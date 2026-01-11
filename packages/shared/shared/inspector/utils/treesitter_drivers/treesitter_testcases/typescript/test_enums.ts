// Test file for TypeScript enum definitions

// Basic enum
enum Direction {
  Up,
  Down,
  Left,
  Right
}

// Enum with explicit values
enum StatusCode {
  OK = 200,
  Created = 201,
  Accepted = 202,
  BadRequest = 400,
  Unauthorized = 401,
  NotFound = 404,
  InternalError = 500
}

// String enum
enum Color {
  Red = 'RED',
  Green = 'GREEN',
  Blue = 'BLUE',
  Yellow = 'YELLOW'
}

// Mixed enum (numeric and string)
enum Mixed {
  No = 0,
  Yes = 'YES',
  Maybe = 1,
  Never = 'NEVER'
}

// Const enum
const enum ConstDirection {
  North,
  South,
  East,
  West
}

// Enum with const assertions
enum FileAccess {
  None = 0,
  Read = 1 << 1,
  Write = 1 << 2,
  ReadWrite = Read | Write,
  All = Read | Write | 4
}

// Ambient enum
declare enum AmbientEnum {
  A = 1,
  B,
  C = 4
}

// Module scoped enum
module ModuleScope {
  export enum ModuleEnum {
    A = 'A',
    B = 'B',
    C = 'C'
  }
}
