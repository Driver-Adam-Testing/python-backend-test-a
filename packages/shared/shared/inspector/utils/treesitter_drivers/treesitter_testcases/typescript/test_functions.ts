// Test file for TypeScript function definitions

// Basic function declarations
function functionWithTypeParams(a: number, b: number): number {
  return a + b;
}

// Optional and default parameters
function mixedRest(first: string, ...rest: number[]) {
  return first + rest.join(',');
}

// Arrow functions
const arrowFunction = () => console.log('arrow');

const arrowWithParams = (a: number, b: number) => a + b;

const arrowWithBlock = (x: number) => {
  const doubled = x * 2;
  return doubled;
};

const arrowWithTypes = (a: number, b: string): string => {
  return a + b;
};

// Single parameter arrow functions
const singleParam = x => x * 2;
const singleParamWithType = (x: number) => x * 2;

// Generic functions
function genericFunction<T>(value: T): T {
  return value;
}

function multipleGenerics<T, U>(first: T, second: U): [T, U] {
  return [first, second];
}

function constrainedGeneric<T extends string | number>(value: T): T {
  return value;
}

function genericWithDefault<T = string>(value: T): T {
  return value;
}

const genericArrow = <T>(value: T): T => value;

const genericArrowConstrained = <T extends object>(obj: T): T => obj;

// Function overloading
function overloaded(value: string): string;
function overloaded(value: number): number;
function overloaded(value: boolean): boolean;
function overloaded(value: string | number | boolean): string | number | boolean {
  return value;
}

// Async functions
async function asyncWithParams(url: string): Promise<any> {
  const response = await fetch(url);
  return response.json();
}

const asyncArrowWithReturn = async (): Promise<number> => {
  return 42;
};

// Generator functions
function* generatorWithReturn(): Generator<number, string, unknown> {
  yield 1;
  yield 2;
  return 'done';
}

const generatorArrow = function* () {
  yield 'arrow generator';
};

// Async generator functions
async function* asyncGenerator() {
  yield await Promise.resolve(1);
  yield await Promise.resolve(2);
}

async function* asyncGeneratorWithType(): AsyncGenerator<number, void, unknown> {
  yield 1;
  yield 2;
}

// Function expressions
const functionExpression = function() {
  return 'expression';
};

const namedExpression = function namedFunc() {
  return 'named expression';
};

// Immediately invoked function expressions (IIFE)
(function() {
  console.log('IIFE');
})();

(function namedIIFE() {
  console.log('Named IIFE');
})();

((x: number) => {
  console.log(x);
})(42);

// Type assertions in parameters
function assertionParams(value: unknown): value is string {
  return typeof value === 'string';
}

interface UIElement {
  addClickListener(onclick: (this: void, e: Event) => void): void;
}

// Tagged template functions
function taggedTemplate(strings: TemplateStringsArray, ...values: any[]) {
  return strings.join('');
}

// Curried functions
const curry = (a: number) => (b: number) => (c: number) => a + b + c;

// Getter and setter syntax (though typically in classes)
// const obj = {
//   _value: 0,
//   get value() {
//     return this._value;
//   },
//   set value(v: number) {
//     this._value = v;
//   }
// };

// // Method shorthand in objects
// const objectMethods = {
//   method() {
//     return 'method';
//   },
//   async asyncMethod() {
//     return 'async';
//   },
//   *generatorMethod() {
//     yield 'generator';
//   }
// };


// Optional chaining in function calls
// This should not be picked up by the parser as a function definition.
const maybeFunc = Math.random() > 0.5 ? () => 'exists' : undefined;


// Complex arrow function types
const complexArrow: <T extends object>(
  obj: T,
  key: keyof T
) => T[keyof T] = (obj, key) => obj[key];

// Function returning a function
function createMultiplier(factor: number): (value: number) => number {
  return (value: number) => value * factor;
}
