"""DO NOT MODIFY THIS FILE"""
# this file is 268 bytes


def fib(n: int) -> int:
    if n <= 1:
        return n
    else:
        return fib(n - 1) + fib(n - 2)


def main() -> None:
    for i in range(5):
        print(fib(i))


if __name__ == "__main__":
    main()
