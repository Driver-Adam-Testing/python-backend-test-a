// Test file for TypeScript variable declarations

// Const declarations
const simpleConst = 'hello';

// Let declarations
let simpleLet = 'world';

// Var declarations (legacy)
var simpleVar = 'legacy';

// Multiple declarations
const a = 1, b = 2, c = 3;
let x = 'x', y = 'y', z = 'z';
var m = true, n = false, o = null;

// Array declarations
const simpleArray = [1, 2, 3];

// Object declarations
const simpleObject = { key: 'value' };

// Type annotations
const annotatedString: string = 'explicit type';

// Union types
let stringOrNumber: string | number = 'string';

// Intersection types
const intersection: { a: string } & { b: number } = {
  a: 'hello',
  b: 42
};

// Type aliases in variables
type Point = { x: number; y: number };

// Generic variables
const genericArray: Array<number> = [1, 2, 3];

// Spread operator
const spreadArray = [...[1, 2], ...[3, 4]];
const spreadObject = { ...{ a: 1 }, ...{ b: 2 } };

// Symbol variables
// const sym = Symbol('description');
// const symFor = Symbol.for('shared');
// const wellKnown = Symbol.iterator;

// // Functions as variables
// const functionVar = function() { return 'function'; };
// const arrowFunction = () => 'arrow';
// const asyncArrow = async () => await Promise.resolve('async');
// const generatorFunction = function*() { yield 1; };

// Template literals
const template = `Hello ${name}!`;
const multiline = `
  Line 1
  Line 2
`;
const tagged = myTag`Tagged ${template}`;

// Export declarations
export const exportedConst = 'exported';
export let exportedLet = 42;
export var exportedVar = true;


// Conditional expressions
const conditional = condition ? 'true' : 'false';

// Readonly modifiers
const readonlyObj: Readonly<{ x: number }> = { x: 10 };

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
