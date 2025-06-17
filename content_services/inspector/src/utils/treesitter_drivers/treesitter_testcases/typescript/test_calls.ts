// Test file for TypeScript function and method calls
// Multiple arguments
multipleArgs(1, 2, 3);

// Method calls on objects
const obj = {
  method() { return 'method'; },
  property: 'value'
};
obj.method();

// Chained method calls
const chainable = {
  first() { return this; },
  second() { return this; },
  third() { return 'done'; }
};
chainable.first().second().third();

// Constructor calls
class MyClass {
  constructor(public value: string) {}
}
new MyClass('instance');

// Constructor with no arguments
class EmptyClass {}
new EmptyClass();

// Super calls
class Parent {
  method() { return 'parent'; }
}
class Child extends Parent {
  method() {
    super.method();
    return super.method();
  }
  constructor() {
    super();
  }
}

// Tagged template calls
function myTag(strings: TemplateStringsArray, ...values: any[]) {
  return strings.join('');
}
myTag`Hello ${'world'}!`;

// Complex tagged template
function complexTag(strings: TemplateStringsArray, ...values: any[]) {
  return { strings, values };
}
complexTag`Line 1
Line 2 with ${42} and ${'string'}`;

// IIFE (Immediately Invoked Function Expression)
(function() { return 'iife'; })();
(function named() { return 'named iife'; })();
(() => 'arrow iife')();

// Call with spread operator
function spreadFunc(...args: number[]) { return args; }
const nums = [1, 2, 3];
spreadFunc(...nums);
spreadFunc(...[4, 5, 6]);

// Mixed spread
function mixedSpread(first: string, ...rest: number[]) { return { first, rest }; }
mixedSpread('hello', ...nums);

// Optional chaining calls
const maybeObj: any = { method: () => 'exists' };
maybeObj?.method?.();
maybeObj?.nested?.deep?.method?.();

// Multiple type parameters
function multiGeneric<T, U>(first: T, second: U) { return { first, second }; }
multiGeneric<string, number>('hello', 42);

// Async calls with await
async function asyncFunc() { return 'async result'; }
await asyncFunc();

// Async in async context
async function asyncContext() {
  await asyncFunc();
  const result = await asyncFunc();
  return await Promise.resolve('done');
}

// Function.prototype methods
const func = function(this: any, x: number) { return this.value + x; };
const context = { value: 10 };
func.call(context, 5);
func.apply(context, [5]);
const bound = func.bind(context);
bound(5);

// Array method calls
const array = [1, 2, 3, 4, 5];
array.map(x => x * 2);
array.filter(x => x > 2);
array.reduce((acc, val) => acc + val, 0);
array.forEach(x => console.log(x));
array.find(x => x === 3);
array.findIndex(x => x === 3);
array.some(x => x > 4);
array.every(x => x > 0);

// Promise method calls
const promise = Promise.resolve(42);
promise.then(value => value * 2);
promise.catch(error => console.error(error));
promise.finally(() => console.log('done'));

// Promise chaining
Promise.resolve(1)
  .then(x => x + 1)
  .then(x => x * 2)
  .catch(console.error);

// Static method calls
class StaticClass {
  static staticMethod() { return 'static'; }
  static another(x: number) { return x * 2; }
}
StaticClass.staticMethod();
StaticClass.another(21);

// Built-in static methods
Object.keys({ a: 1, b: 2 });
Object.values({ a: 1, b: 2 });
Object.entries({ a: 1, b: 2 });
Array.isArray([1, 2, 3]);
Number.parseInt('42');
Math.max(1, 2, 3);
Math.min(1, 2, 3);
Date.now();
JSON.parse('{"key": "value"}');
JSON.stringify({ key: 'value' });

// Computed property calls
const methodName = 'method';
const dynamicObj = {
  method() { return 'called'; },
  another() { return 'another'; }
};
dynamicObj[methodName]();
dynamicObj['another']();

// Nested calls
function outer(x: number) { return x * 2; }
function inner() { return 21; }
outer(inner());

// Deep nesting
function a() { return 1; }
function b(x: number) { return x + 1; }
function c(x: number) { return x * 2; }
c(b(a()));

// Symbol method calls
const sym = Symbol.iterator;
const iterableObj = {
  [Symbol.iterator]() {
    return { next: () => ({ value: 1, done: true }) };
  },
  [sym]() {
    return { next: () => ({ value: 2, done: true }) };
  }
};
iterableObj[Symbol.iterator]();
iterableObj[sym]();

// Generator calls
function* generator() {
  yield 1;
  yield 2;
  yield 3;
}
const gen = generator();
gen.next();
gen.next();
gen.return();
gen.throw(new Error());

// Async generator calls
async function* asyncGenerator() {
  yield await Promise.resolve(1);
  yield await Promise.resolve(2);
}
const asyncGen = asyncGenerator();
await asyncGen.next();
await asyncGen.return();

// Nullish coalescing with calls
const maybeFunc = null;
const defaultFunc = () => 'default';
(maybeFunc ?? defaultFunc)();

// Type assertion in calls
interface Callable {
  call(): string;
}
const unknownObj: unknown = { call: () => 'called' };
(unknownObj as Callable).call();
(<Callable>unknownObj).call();

// Non-null assertion calls
const nullableFunc: (() => string) | null = () => 'not null';
nullableFunc!();
nullableFunc!.call(null);

// Partial application / currying
function curry(a: number) {
  return function(b: number) {
    return function(c: number) {
      return a + b + c;
    };
  };
}
curry(1)(2)(3);

// Arrow function currying
const arrowCurry = (a: number) => (b: number) => (c: number) => a + b + c;
arrowCurry(1)(2)(3);

// Rest parameters in calls
function restFunc(first: string, second: number, ...rest: boolean[]) {
  return { first, second, rest };
}
restFunc('hello', 42, true, false, true);

// Callback calls
function withCallback(cb: (value: number) => void) {
  cb(42);
}
withCallback(value => console.log(value));
withCallback(function(value) { console.log(value); });


// Window/global method calls
window.alert('Hello');
window.setTimeout(() => {}, 1000);
window.setInterval(() => {}, 1000);
globalThis.parseInt('42');

// Console methods
console.log('log');
console.error('error');
console.warn('warning');
console.info('info');
console.debug('debug');
console.trace('trace');
console.time('timer');
console.timeEnd('timer');

// DOM method calls (type simulation)
const element = document.getElementById('myId');
element?.addEventListener('click', () => {});
document.querySelector('.class');
document.querySelectorAll('div');
document.createElement('div');

// Event handler calls
const button = document.createElement('button');
button.onclick = function(event) {
  event.preventDefault();
  event.stopPropagation();
};

// Proxy calls
const target = { value: 42 };
const proxy = new Proxy(target, {
  get(target, prop) {
    return target[prop as keyof typeof target];
  }
});
proxy.value;

// Reflect API calls
Reflect.get(target, 'value');
Reflect.set(target, 'value', 100);
Reflect.has(target, 'value');
Reflect.deleteProperty(target, 'value');


// Method calls with type parameters
class GenericClass {
  method<T>(value: T): T {
    return value;
  }
}
const genericInstance = new GenericClass();
genericInstance.method<string>('hello');
genericInstance.method<number>(42);

// Error constructor calls
new Error('message');
new TypeError('type error');
new ReferenceError('reference error');

// Set and Map method calls
const set = new Set([1, 2, 3]);
set.add(4);
set.has(2);
set.delete(1);
set.clear();

const map = new Map([['key', 'value']]);
map.get('key');
map.set('newKey', 'newValue');
map.has('key');
map.delete('key');

// WeakSet and WeakMap calls
const weakSet = new WeakSet();
const obj1 = {};
weakSet.add(obj1);
weakSet.has(obj1);

const weakMap = new WeakMap();
weakMap.set(obj1, 'value');
weakMap.get(obj1);

// ArrayBuffer and typed array calls
const buffer = new ArrayBuffer(16);
const view = new DataView(buffer);
view.getInt32(0);
view.setInt32(0, 42);

// Regular expression method calls
const regex = /pattern/g;
regex.test('pattern');
regex.exec('pattern');
'string'.match(regex);
'string'.replace(regex, 'replacement');

// Decorator calls (when enabled)
function decorator(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  return descriptor;
}

// Import calls (dynamic imports)
import('./module').then(module => module.default);

// Assertion functions
function assert(condition: any): asserts condition {
  if (!condition) {
    throw new Error('Assertion failed');
  }
}
assert(true);

// Type predicate calls
function isString(value: unknown): value is string {
  return typeof value === 'string';
}
isString('test');
isString(42);

// Recursive calls
function factorial(n: number): number {
  if (n <= 1) return 1;
  return n * factorial(n - 1);
}
factorial(5);

// Mutually recursive calls
function isEven(n: number): boolean {
  if (n === 0) return true;
  return isOdd(n - 1);
}
function isOdd(n: number): boolean {
  if (n === 0) return false;
  return isEven(n - 1);
}
isEven(4);
isOdd(3);

// Method calls in class
class MethodClass {
  method1() {
    this.method2();
    return this.method3();
  }
  private method2() { return 'private'; }
  protected method3() { return 'protected'; }
}

// Getter/setter calls (property access that triggers function)
class GetterSetter {
  private _value = 0;
  get value() { return this._value; }
  set value(v: number) { this._value = v; }
}
const gs = new GetterSetter();
gs.value;  // getter call
gs.value = 10;  // setter call

// toString/valueOf implicit calls
const objWithToString = {
  toString() { return 'string representation'; },
  valueOf() { return 42; }
};
String(objWithToString);  // calls toString
Number(objWithToString);  // calls valueOf

// Iterator protocol calls
const customIterator = {
  [Symbol.iterator]() {
    let i = 0;
    return {
      next() {
        return { value: i++, done: i > 3 };
      }
    };
  }
};
[...customIterator];  // calls Symbol.iterator and next

// Async iterator protocol calls
const customAsyncIterator = {
  async *[Symbol.asyncIterator]() {
    yield await Promise.resolve(1);
    yield await Promise.resolve(2);
  }
};

// for await...of triggers async iterator calls
async function consumeAsyncIterator() {
  for await (const value of customAsyncIterator) {
    console.log(value);
  }
}

// BigInt constructor
BigInt(123);
BigInt('123456789012345678901234567890');

// Symbol constructor and methods
Symbol('description');
Symbol.for('global');
Symbol.keyFor(Symbol.for('global'));

// Intl API calls
new Intl.DateTimeFormat('en-US').format(new Date());
new Intl.NumberFormat('de-DE').format(123456.789);
new Intl.Collator('en').compare('a', 'b');

// Performance API calls
performance.now();
performance.mark('start');
performance.measure('duration', 'start');

// URL constructor
new URL('https://example.com');
new URL('/path', 'https://example.com');

// TextEncoder/TextDecoder
new TextEncoder().encode('string');
new TextDecoder().decode(new Uint8Array([72, 101, 108, 108, 111]));

// AbortController
const controller = new AbortController();
controller.abort();

// Pipe operator simulation (function composition)
const pipe = (...fns: Function[]) => (x: any) => fns.reduce((v, f) => f(v), x);
const add1 = (x: number) => x + 1;
const mult2 = (x: number) => x * 2;
pipe(add1, mult2)(5);
