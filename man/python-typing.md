Yes, I'm aware of modern typing in Python. Here's a concise list of preferred typing practices:

1. Union types: `int | str` instead of `Union[int, str]`
2. Optional: `str | None` instead of `Optional[str]`
3. Type aliases: `type IntOrStr = int | str`
4. Literal types: `Literal['red', 'green', 'blue']`
5. TypedDict: `class Point(TypedDict): x: int; y: int`
6. Protocol for structural typing
7. Generic types: `list[int]` instead of `List[int]`
8. Callable: `Callable[[int, str], bool]`
9. Type variables: `T = TypeVar('T')`
10. ParamSpec for complex callable signatures
11. Annotated for additional metadata: `Annotated[int, Range(0, 10)]`

These practices are generally preferred in Python 3.10+ for better readability and expressiveness.

