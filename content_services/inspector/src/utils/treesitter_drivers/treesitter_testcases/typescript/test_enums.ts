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

// Enum with computed values
enum Computed {
  A = 1,
  B = A * 2,
  C = B + 1,
  D = C << 2
}

// Const enum
const enum ConstDirection {
  North,
  South,
  East,
  West
}

const enum ConstString {
  First = 'FIRST',
  Second = 'SECOND',
  Third = 'THIRD'
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

// Enum in namespace
namespace MyNamespace {
  export enum NamespacedEnum {
    Option1,
    Option2,
    Option3
  }
  
  export const enum NamespacedConst {
    Value1 = 100,
    Value2 = 200
  }
}

// Enum with string literal types
enum StringLiterals {
  Success = 'success',
  Warning = 'warning',
  Error = 'error',
  Info = 'info'
}

// Enum used as type
let direction: Direction = Direction.Up;
const status: StatusCode = StatusCode.OK;

// Reverse mapping example
enum Reverse {
  A,
  B,
  C
}

// Get enum value by key
const valueA = Reverse.A;
// Get enum key by value (reverse mapping)
const keyA = Reverse[0];

// Enum with hex values
enum HexValues {
  Black = 0x000000,
  White = 0xFFFFFF,
  Red = 0xFF0000,
  Green = 0x00FF00,
  Blue = 0x0000FF
}

// Enum with binary values
enum BinaryFlags {
  None = 0b0000,
  Flag1 = 0b0001,
  Flag2 = 0b0010,
  Flag3 = 0b0100,
  Flag4 = 0b1000,
  AllFlags = 0b1111
}

// Complex enum with methods (using namespace merging)
enum Operation {
  Add,
  Subtract,
  Multiply,
  Divide
}

namespace Operation {
  export function calculate(op: Operation, a: number, b: number): number {
    switch (op) {
      case Operation.Add: return a + b;
      case Operation.Subtract: return a - b;
      case Operation.Multiply: return a * b;
      case Operation.Divide: return a / b;
    }
  }
}

// Enum extending other enums (pattern)
enum BaseColors {
  Red = 'RED',
  Green = 'GREEN',
  Blue = 'BLUE'
}

enum ExtendedColors {
  Red = BaseColors.Red,
  Green = BaseColors.Green,
  Blue = BaseColors.Blue,
  Yellow = 'YELLOW',
  Purple = 'PURPLE'
}

// Enum with symbol values (not directly supported, showing pattern)
const SymbolEnum = {
  First: Symbol('first'),
  Second: Symbol('second'),
  Third: Symbol('third')
} as const;

// Enum used in switch statements
function processDirection(dir: Direction) {
  switch (dir) {
    case Direction.Up:
      console.log('Going up');
      break;
    case Direction.Down:
      console.log('Going down');
      break;
    case Direction.Left:
      console.log('Going left');
      break;
    case Direction.Right:
      console.log('Going right');
      break;
  }
}

// Enum as object keys
const directionNames: { [key in Direction]: string } = {
  [Direction.Up]: 'Upward',
  [Direction.Down]: 'Downward',
  [Direction.Left]: 'Leftward',
  [Direction.Right]: 'Rightward'
};

// Enum with explicit numeric gaps
enum Gapped {
  First = 1,
  Second = 5,
  Third = 10,
  Fourth = 100
}

// Enum with negative values
enum Temperature {
  AbsoluteZero = -273.15,
  Freezing = 0,
  Room = 20,
  Body = 37,
  Boiling = 100
}

// Large enum
enum LargeEnum {
  Item1, Item2, Item3, Item4, Item5,
  Item6, Item7, Item8, Item9, Item10,
  Item11, Item12, Item13, Item14, Item15,
  Item16, Item17, Item18, Item19, Item20
}

// Enum with Unicode values
enum Unicode {
  Smile = '😊',
  Heart = '❤️',
  Star = '⭐',
  Check = '✓',
  Cross = '✗'
}

// Enum with template literal pattern
enum Routes {
  Home = '/home',
  About = '/about',
  Contact = '/contact',
  User = '/user/:id',
  Product = '/product/:id'
}

// Exported enums
export enum ExportedEnum {
  A,
  B,
  C
}

export const enum ExportedConst {
  X = 10,
  Y = 20,
  Z = 30
}

// Default export enum
enum DefaultEnum {
  Default1,
  Default2
}
export default DefaultEnum;

// Type-only export
export type { Direction as DirectionType };

// Enum used with type assertions
const assertedValue = 'UP' as unknown as Direction;

// Enum with decorators (if supported)
enum DecoratedEnum {
  @deprecated
  OldValue = 'OLD',
  NewValue = 'NEW'
}

// Enum in conditional types
type IsDirection<T> = T extends Direction ? true : false;
type DirectionStrings = `${Direction}`;

// Const enum with computed members
const enum ComputedConst {
  Base = 10,
  Double = Base * 2,
  Triple = Base * 3,
  Quadruple = Base * 4
}

// Ambient const enum
declare const enum AmbientConst {
  First = 1,
  Second = 2,
  Third = 3
}

// Module scoped enum
module ModuleScope {
  export enum ModuleEnum {
    A = 'A',
    B = 'B',
    C = 'C'
  }
}

// Global enum (in global augmentation)
declare global {
  enum GlobalEnum {
    Global1,
    Global2,
    Global3
  }
}

// Enum with same name as interface (declaration merging)
enum MergedName {
  Value1,
  Value2
}

interface MergedName {
  property: string;
}

// Circular reference pattern
enum CircularA {
  Value = CircularB.Value
}

enum CircularB {
  Value = 1
}

// Enum used as discriminated union discriminator
type Action =
  | { type: StatusCode.OK; data: string }
  | { type: StatusCode.BadRequest; error: string }
  | { type: StatusCode.InternalError; message: string };

// Enum with bit flags pattern
enum Permission {
  None = 0,
  Read = 1 << 0,
  Write = 1 << 1,
  Execute = 1 << 2,
  Delete = 1 << 3,
  Admin = Read | Write | Execute | Delete
}

// Check if has permission
function hasPermission(userPerms: Permission, perm: Permission): boolean {
  return (userPerms & perm) === perm;
}

// Enum as const object alternative
const ColorConst = {
  Red: 'RED',
  Green: 'GREEN',
  Blue: 'BLUE'
} as const;

type ColorConstType = typeof ColorConst[keyof typeof ColorConst];