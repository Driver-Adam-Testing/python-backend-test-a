// Test file for TypeScript interfaces and type aliases

// Basic interfaces
interface InterfaceWithOptional {
  required: string;
  optional?: number;
  optionalMethod?(): void;
}

// Readonly properties
interface ReadonlyInterface {
  readonly id: string;
  readonly data: number[];
  readonly nested: {
    readonly value: string;
  };
}

// Index signatures
interface StringIndex {
  [key: string]: any;
}

interface NumberIndex {
  [index: number]: string;
}

interface MixedIndex {
  [key: string]: string | number;
  [index: number]: string;
  length: number;
}

// Interface inheritance
interface Animal {
  name: string;
  age: number;
}

interface Dog extends Animal {
  breed: string;
  bark(): void;
}

// Multiple inheritance
interface Flyable {
  fly(): void;
  altitude: number;
}

interface Swimmable {
  swim(): void;
  depth: number;
}

interface Duck extends Animal, Flyable, Swimmable {
  quack(): void;
}

// Generic interfaces
interface Pair<T, U> {
  first: T;
  second: U;
}

// Nested interfaces
interface OuterInterface {
  outer: string;
  inner: {
    nested: string;
    deep: {
      value: number;
    };
  };
}

// Interface merging
interface MergedInterface {
  property1: string;
}

interface MergedInterface {
  property2: number;
}

interface MergedInterface {
  method(): void;
}

// Type aliases - basic
// type StringAlias = string;
// type NumberAlias = number;
// type BooleanAlias = boolean;
//
// // Union types
// type StringOrNumber = string | number;
// type Status = 'active' | 'inactive' | 'pending';
// type Mixed = string | number | boolean | null | undefined;
//
// // Intersection types
// type PersonName = { firstName: string; lastName: string };
// type PersonAge = { age: number };
// type Person = PersonName & PersonAge;
//
// type ComplexIntersection = Animal & Flyable & { id: string };
//
// // Tuple types
// type Pair = [string, number];
// type Triple = [string, number, boolean];
// type NamedTuple = [x: number, y: number, z?: number];
// type RestTuple = [string, ...number[]];
// type LeadingRest = [...string[], number];
//
// // Function types
// type SimpleFunction = () => void;
// type FunctionWithParams = (a: number, b: string) => boolean;
// type GenericFunction = <T>(value: T) => T;
// type OverloadedFunction = {
//   (x: string): string;
//   (x: number): number;
// };
//
// // Object types
// type Point = {
//   x: number;
//   y: number;
// };
//
// type ReadonlyPoint = {
//   readonly x: number;
//   readonly y: number;
// };
//
// type OptionalPoint = {
//   x?: number;
//   y?: number;
// };
//
// // Mapped types
// type Readonly<T> = {
//   readonly [P in keyof T]: T[P];
// };
//
// type Partial<T> = {
//   [P in keyof T]?: T[P];
// };
//
// type Nullable<T> = {
//   [P in keyof T]: T[P] | null;
// };
//
// // Key remapping
// type Getters<T> = {
//   [P in keyof T as `get${Capitalize<string & P>}`]: () => T[P];
// };
//
// type RemovePrefix<T> = {
//   [P in keyof T as P extends `_${infer R}` ? R : P]: T[P];
// };
//
// // Conditional types
// type IsString<T> = T extends string ? true : false;
// type NonNullable<T> = T extends null | undefined ? never : T;
// type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never;
// type UnpackArray<T> = T extends (infer U)[] ? U : T;
//
// // Template literal types
// type EventName = `on${string}`;
// type Greeting = `Hello ${string}!`;
// type Color = 'red' | 'blue' | 'green';
// type ColorShade = `${Color}-${number}`;
//
// // Intrinsic string manipulation
// type Uppercase<S extends string> = intrinsic;
// type Lowercase<S extends string> = intrinsic;
// type Capitalize<S extends string> = intrinsic;
// type Uncapitalize<S extends string> = intrinsic;
//
// // Utility types usage
// type MyPartial = Partial<Person>;
// type MyRequired = Required<Person>;
// type MyReadonly = Readonly<Person>;
// type MyRecord = Record<string, number>;
// type MyPick = Pick<Person, 'firstName' | 'age'>;
// type MyOmit = Omit<Person, 'age'>;
//
// // Complex generic constraints
// interface Lengthwise {
//   length: number;
// }
//
// type ConstrainedGeneric<T extends Lengthwise> = {
//   value: T;
//   getLength(): number;
// };
//
// // Recursive types
// type JSONValue =
//   | string
//   | number
//   | boolean
//   | null
//   | JSONValue[]
//   | { [key: string]: JSONValue };
//
// type LinkedList<T> = {
//   value: T;
//   next?: LinkedList<T>;
// };
//
// // Discriminated unions
// type Shape =
//   | { kind: 'circle'; radius: number }
//   | { kind: 'square'; sideLength: number }
//   | { kind: 'rectangle'; width: number; height: number };
//
// type Result<T> =
//   | { success: true; value: T }
//   | { success: false; error: Error };
//
// // Type guards and predicates
// type TypePredicate<T> = (value: unknown) => value is T;
//
// // Generic constraints with keyof
// type PropertyGetter<T, K extends keyof T> = () => T[K];
// type PropertySetter<T, K extends keyof T> = (value: T[K]) => void;
//
// // Distributive conditional types
// type ToArray<T> = T extends any ? T[] : never;
// type ExtractArrayType<T> = T extends (infer U)[] ? U : never;
//
// // Infer in conditional types
// type UnpackPromise<T> = T extends Promise<infer U> ? U : T;
// type FunctionArgs<T> = T extends (...args: infer A) => any ? A : never;
//
// // Never type
// type Never = string & number;
// type ExcludeNull<T> = T extends null ? never : T;
//
// // Literal types
// type StringLiteral = 'literal';
//
// // This type
// type FluentInterface = {
//   method(): this;
//   chain(): this;
// };

// Module augmentation interfaces
declare module 'express' {
  interface Request {
    user?: {
      id: string;
      name: string;
    };
  }
}

// Global augmentation
declare global {
  interface Window {
    myGlobal: string;
  }

  interface Array<T> {
    customMethod(): T[];
  }
}

// Ambient interfaces
declare interface AmbientInterface {
  ambientProperty: string;
  ambientMethod(): void;
}

// Type-only exports
export interface ExportedInterface {
  exported: true;
}

// Complex real-world types
// type APIResponse<T> = {
//   data: T;
//   status: number;
//   headers: Record<string, string>;
//   timestamp: Date;
// };
//
// type Middleware<T = any> = (
//   req: Request,
//   res: Response,
//   next: (err?: Error) => void
// ) => void;
//
// type DeepPartial<T> = {
//   [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
// };
//
// type DeepReadonly<T> = {
//   readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P];
// };
//
