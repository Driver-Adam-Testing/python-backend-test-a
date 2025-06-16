// Test file for TypeScript variable declarations

// Const declarations
const simpleConst = 'hello';
const numberConst = 42;
const booleanConst = true;
const nullConst = null;
const undefinedConst = undefined;

// Let declarations
let simpleLet = 'world';
let numberLet = 100;
let booleanLet = false;
let uninitializedLet: string;
let explicitTypeLet: number = 5;

// Var declarations (legacy)
var simpleVar = 'legacy';
var numberVar = 200;
var booleanVar = true;
var uninitializedVar: any;

// Multiple declarations
const a = 1, b = 2, c = 3;
let x = 'x', y = 'y', z = 'z';
var m = true, n = false, o = null;

// Array declarations
const simpleArray = [1, 2, 3];
const stringArray: string[] = ['a', 'b', 'c'];
const mixedArray = [1, 'two', true, null];
const emptyArray: number[] = [];
const arrayGeneric: Array<string> = ['generic'];
const readonlyArray: readonly number[] = [1, 2, 3];
const tupleArray: [string, number] = ['tuple', 1];

// Object declarations
const simpleObject = { key: 'value' };
const nestedObject = {
  name: 'John',
  age: 30,
  address: {
    street: '123 Main St',
    city: 'NYC'
  }
};

const objectWithMethods = {
  value: 42,
  getValue() {
    return this.value;
  },
  setValue(newValue: number) {
    this.value = newValue;
  }
};

// Type annotations
const annotatedString: string = 'explicit type';
const annotatedNumber: number = 42;
const annotatedBoolean: boolean = true;
const annotatedObject: { name: string; age: number } = {
  name: 'Alice',
  age: 25
};

// Union types
let stringOrNumber: string | number = 'string';
let nullableString: string | null = null;
let optionalBoolean: boolean | undefined;
const literalUnion: 'left' | 'right' | 'center' = 'center';

// Intersection types
const intersection: { a: string } & { b: number } = {
  a: 'hello',
  b: 42
};

// Type aliases in variables
type Point = { x: number; y: number };
const point: Point = { x: 10, y: 20 };

// Interface usage
interface User {
  id: string;
  name: string;
}
const user: User = { id: '123', name: 'Bob' };

// Generic variables
const genericArray: Array<number> = [1, 2, 3];
const genericMap: Map<string, number> = new Map();
const genericSet: Set<string> = new Set(['a', 'b']);
const genericPromise: Promise<string> = Promise.resolve('done');

// Destructuring assignments
const { name, age } = { name: 'John', age: 30 };
const { prop: renamed } = { prop: 'value' };
const { nested: { value } } = { nested: { value: 42 } };
const { optional = 'default' } = {};

// Array destructuring
const [first, second] = [1, 2];
const [head, ...tail] = [1, 2, 3, 4, 5];
const [, , third] = [1, 2, 3];
const [one = 'default'] = [];

// Complex destructuring
const {
  user: { name: userName, age: userAge },
  settings: { theme = 'light' }
} = {
  user: { name: 'Alice', age: 30 },
  settings: {}
};

// Rest parameters in destructuring
const { a: extracted, ...rest } = { a: 1, b: 2, c: 3 };

// Spread operator
const spreadArray = [...[1, 2], ...[3, 4]];
const spreadObject = { ...{ a: 1 }, ...{ b: 2 } };

// Computed property names
const key = 'dynamic';
const computedObject = {
  [key]: 'value',
  [`${key}2`]: 'value2'
};

// Symbol variables
const sym = Symbol('description');
const symFor = Symbol.for('shared');
const wellKnown = Symbol.iterator;

// BigInt
const bigIntLiteral = 123n;
const bigIntConstructor = BigInt(456);
const hugeBigInt = 123456789012345678901234567890n;

// Regular expressions
const simpleRegex = /pattern/;
const flaggedRegex = /pattern/gi;
const regexConstructor = new RegExp('pattern', 'gi');

// Functions as variables
const functionVar = function() { return 'function'; };
const arrowFunction = () => 'arrow';
const asyncArrow = async () => await Promise.resolve('async');
const generatorFunction = function*() { yield 1; };

// Class expressions as variables
const ClassVar = class {
  method() { return 'class'; }
};

const NamedClass = class MyClass {
  static staticProp = 'static';
};

// Template literals
const template = `Hello ${name}!`;
const multiline = `
  Line 1
  Line 2
`;
const tagged = myTag`Tagged ${template}`;

// Type assertions
const assertion = <string>someValue;
const asAssertion = someValue as string;
const constAssertion = { x: 10 } as const;
const readonlyAssertion = [1, 2, 3] as readonly number[];

// Non-null assertions
const nonNull = someValue!;
const deepNonNull = obj!.prop!.value!;

// Ambient declarations
declare const GLOBAL_CONFIG: any;
declare let declaredLet: string;
declare var declaredVar: number;

// Module declarations
declare module '*.json' {
  const value: any;
  export default value;
}

// Global augmentations
declare global {
  const globalConst: string;
  let globalLet: number;
  var globalVar: boolean;
}

// Export declarations
export const exportedConst = 'exported';
export let exportedLet = 42;
export var exportedVar = true;

// Complex type annotations
const complexType: {
  method(): void;
  property: string;
  nested: {
    array: number[];
  };
} = {
  method() {},
  property: 'value',
  nested: { array: [1, 2, 3] }
};

// Conditional expressions
const conditional = condition ? 'true' : 'false';
const nestedConditional = a ? b ? 'both' : 'a' : 'neither';

// Nullish coalescing
const nullishDefault = nullValue ?? 'default';
const chainedNullish = a ?? b ?? c ?? 'fallback';

// Optional chaining
const optionalAccess = obj?.property;
const optionalMethod = obj?.method?.();
const optionalArray = arr?.[0];

// Logical assignments
let logical = false;
logical ||= true;
logical &&= false;
logical ??= 'default';

// Numeric separators
const readable = 1_000_000;
const binary = 0b1010_0001;
const hex = 0xFF_FF_FF;
const bigIntSeparator = 123_456n;

// Readonly modifiers
const readonlyObj: Readonly<{ x: number }> = { x: 10 };
const readonlyArr: ReadonlyArray<number> = [1, 2, 3];
const deepReadonly: DeepReadonly<any> = { a: { b: 1 } };

// WeakMap and WeakSet
const weakMap = new WeakMap<object, string>();
const weakSet = new WeakSet<object>();

// Proxy objects
const proxy = new Proxy({}, {
  get(target, prop) {
    return prop in target ? target[prop] : 'default';
  }
});

// Reflect usage
const reflected = Reflect.get(obj, 'property');

// Promises and async
const promise = new Promise<string>((resolve) => {
  resolve('done');
});

const asyncResult = (async () => await fetch('/api'))();

// Error objects
const error = new Error('Something went wrong');
const typeError = new TypeError('Type mismatch');
const customError = new CustomError('Custom message');

// Date objects
const now = new Date();
const specific = new Date('2024-01-01');
const timestamp = new Date(1704067200000);

// Map and Set
const map = new Map<string, number>([
  ['a', 1],
  ['b', 2]
]);

const set = new Set<string>(['unique', 'values']);

// Typed arrays
const int8 = new Int8Array(10);
const uint8 = new Uint8Array([1, 2, 3]);
const float32 = new Float32Array(5);
const buffer = new ArrayBuffer(16);
const view = new DataView(buffer);

// Iterator protocol
const iteratorResult: IteratorResult<number> = {
  value: 1,
  done: false
};

// Async iterators
const asyncIterable: AsyncIterable<number> = {
  async *[Symbol.asyncIterator]() {
    yield 1;
    yield 2;
  }
};

// Import assignments
import imported = require('./module');
const dynamicImport = import('./dynamic');

// Namespace usage
namespace MyNamespace {
  export const value = 42;
}
const namespaceValue = MyNamespace.value;

// Enum usage
enum Color { Red, Green, Blue }
const color: Color = Color.Red;

// Type guards
const isString = (value: unknown): value is string => {
  return typeof value === 'string';
};

// Index signatures
const indexed: { [key: string]: number } = {
  a: 1,
  b: 2
};

// Const enum usage
const enum ConstEnum { A = 1, B = 2 }
const constEnumValue = ConstEnum.A;

// Declare function
declare function declaredFunction(x: number): string;

// Module declaration variable
declare module MyModule {
  export const moduleVar: string;
}

// Type-only imports
import type { TypeOnly } from './types';
const typed: TypeOnly = {} as TypeOnly;

// satisfies operator
const config = {
  port: 3000,
  host: 'localhost'
} satisfies { port: number; host: string };

// using declarations (TC39 proposal)
{
  using resource = getResource();
  // resource will be disposed when block ends
}

// Record type usage
const record: Record<string, number> = {
  a: 1,
  b: 2
};