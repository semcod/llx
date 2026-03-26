
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return None
    return a / b

def calculate(operation, x, y):
    ops = {
        'add': add,
        'multiply': multiply,
        'divide': divide
    }
    if operation not in ops:
        raise ValueError(f"Unknown operation: {operation}")
    return ops[operation](x, y)
