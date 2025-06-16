// Test file for TypeScript function definitions

// Basic function declarations
function simpleFunction() {
  console.log('simple');
}

function functionWithParams(a: number, b: string) {
  return a + b;
}

function functionWithReturn(): string {
  return 'hello';
}

function functionWithTypeParams(a: number, b: number): number {
  return a + b;
}

// Optional and default parameters
function optionalParams(required: string, optional?: number) {
  return optional ? required + optional : required;
}

function defaultParams(a: string, b: number = 42) {
  return a + b;
}

function mixedParams(required: string, optional?: number, defaultParam: boolean = true) {
  console.log(required, optional, defaultParam);
}

// Rest parameters
function restParams(...args: number[]): number {
  return args.reduce((a, b) => a + b, 0);
}

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

// Complex overloading
function processValue(value: string, options?: { uppercase: boolean }): string;
function processValue(value: number, options?: { round: boolean }): number;
function processValue(
  value: string | number,
  options?: { uppercase?: boolean; round?: boolean }
): string | number {
  if (typeof value === 'string') {
    return options?.uppercase ? value.toUpperCase() : value;
  }
  return options?.round ? Math.round(value) : value;
}

// Async functions
async function asyncFunction(): Promise<void> {
  await new Promise(resolve => setTimeout(resolve, 1000));
}

async function asyncWithReturn(): Promise<string> {
  return 'async result';
}

async function asyncWithParams(url: string): Promise<any> {
  const response = await fetch(url);
  return response.json();
}

const asyncArrow = async () => {
  await delay(1000);
};

const asyncArrowWithReturn = async (): Promise<number> => {
  return 42;
};

// Generator functions
function* generatorFunction() {
  yield 1;
  yield 2;
  yield 3;
}

function* generatorWithParam(max: number) {
  for (let i = 0; i < max; i++) {
    yield i;
  }
}

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

const genericExpression = function<T>(value: T): T {
  return value;
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

function assertNever(value: never): never {
  throw new Error('Unexpected value: ' + value);
}

// This parameter
function thisParam(this: HTMLElement, event: Event) {
  console.log(this.innerHTML);
}

interface UIElement {
  addClickListener(onclick: (this: void, e: Event) => void): void;
}

// Destructuring parameters
function destructuredParams({ x, y }: { x: number; y: number }) {
  return x + y;
}

function destructuredArray([first, second]: [string, number]) {
  return first + second;
}

function nestedDestructure({ data: { value } }: { data: { value: string } }) {
  return value;
}

// Function types in parameters
function higherOrder(callback: (x: number) => number): number {
  return callback(42);
}

function complexCallback(
  fn: (a: string, b: number) => Promise<boolean>
): void {
  fn('test', 123);
}

// Constructor functions (old style)
function ConstructorFunction(this: any, name: string) {
  this.name = name;
}

// Conditional types in return
function conditionalReturn<T extends boolean>(
  value: T
): T extends true ? string : number {
  return (value ? 'true' : 42) as any;
}

// Variadic functions
function variadic<T extends any[]>(...args: T): T {
  return args;
}

// Tagged template functions
function taggedTemplate(strings: TemplateStringsArray, ...values: any[]) {
  return strings.join('');
}

const result = taggedTemplate`Hello ${name}!`;

// Function with union return types
function unionReturn(type: string): string | number | null {
  switch (type) {
    case 'string': return 'hello';
    case 'number': return 42;
    default: return null;
  }
}

// Curried functions
const curry = (a: number) => (b: number) => (c: number) => a + b + c;

const partiallyApplied = curry(1)(2);
const fullyApplied = curry(1)(2)(3);

// Function with intersection types
function intersectionParam(value: { a: string } & { b: number }) {
  return value.a + value.b;
}

// Getter and setter syntax (though typically in classes)
const obj = {
  _value: 0,
  get value() {
    return this._value;
  },
  set value(v: number) {
    this._value = v;
  }
};

// Method shorthand in objects
const objectMethods = {
  method() {
    return 'method';
  },
  async asyncMethod() {
    return 'async';
  },
  *generatorMethod() {
    yield 'generator';
  }
};

// Type predicates
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function isNotNull<T>(value: T | null): value is T {
  return value !== null;
}

// Abstract function signatures (in abstract classes)
abstract class AbstractClass {
  abstract abstractMethod(): void;
  abstract asyncAbstract(): Promise<void>;
}

// Function with readonly parameters
function readonlyParam(readonly arr: readonly number[]) {
  return arr.reduce((a, b) => a + b, 0);
}

// Optional chaining in function calls
const maybeFunc = Math.random() > 0.5 ? () => 'exists' : undefined;
const result = maybeFunc?.();

// Private/protected in function context (typically in classes)
class FunctionContext {
  private privateMethod() {
    return 'private';
  }
  
  protected protectedMethod() {
    return 'protected';
  }
  
  public publicMethod() {
    return 'public';
  }
}

// Function declaration merging
function merged(x: string): string;
function merged(x: number): number;
function merged(x: string | number): string | number {
  return x;
}

namespace merged {
  export const version = '1.0.0';
}

// Async function with generic constraint
async function fetchData<T extends { id: string }>(id: string): Promise<T> {
  const response = await fetch(`/api/${id}`);
  return response.json();
}

// Complex arrow function types
const complexArrow: <T extends object>(
  obj: T,
  key: keyof T
) => T[keyof T] = (obj, key) => obj[key];

// Function returning a function
function createMultiplier(factor: number): (value: number) => number {
  return (value: number) => value * factor;
}

const double = createMultiplier(2);
const triple = createMultiplier(3);

// Recursive function
function factorial(n: number): number {
  return n <= 1 ? 1 : n * factorial(n - 1);
}

// Mutually recursive functions
function isEven(n: number): boolean {
  return n === 0 ? true : isOdd(n - 1);
}

function isOdd(n: number): boolean {
  return n === 0 ? false : isEven(n - 1);
}

// Function with branded types
type UserId = string & { readonly __brand: 'UserId' };

function processUser(id: UserId): void {
  console.log(id);
}

// Never type in exhaustive checks
type Action = { type: 'increment' } | { type: 'decrement' };

function reducer(action: Action) {
  switch (action.type) {
    case 'increment':
      return 1;
    case 'decrement':
      return -1;
    default:
      const exhaustive: never = action;
      return exhaustive;
  }
}