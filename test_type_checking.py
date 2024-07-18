from typing import List, Dict

def add(a: int, b: int) -> int:
    return a + b

def greet(name: str) -> str:
    return f"Hello, {name}!"

def get_item(data: List[int], index: int) -> int:
    return data[index]

def make_dict(keys: List[str], values: List[int]) -> Dict[str, int]:
    return dict(zip(keys, values))

# Intentional type errors below
def add_error(a: int, b: int) -> int:
    return a + "b"  # This should raise a type error

def greet_error(name: str) -> str:
    return f"Hello, {name + 123}!"  # This should raise a type error

def get_item_error(data: List[int], index: int) -> str:
    return data[index]  # This should raise a type error (return type mismatch)

def make_dict_error(keys: List[str], values: List[int]) -> Dict[str, str]:
    return dict(zip(keys, values))  # This should raise a type error (return type mismatch)
