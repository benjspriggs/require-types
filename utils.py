from typing import Iterable, Callable, TypeVar
from itertools import chain

def flatten(iter: Iterable[Iterable]) -> Iterable:
    return chain.from_iterable(iter)

T = TypeVar('T')
X = TypeVar('X')

def append(l: Iterable[X], f: Callable[[T], X], inner: Iterable[Iterable[X]]):
    return chain(l, [i for i in flatten(map(f, inner))])
