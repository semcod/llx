
def calculate(a, b, c, d, e):
    x = a + b
    y = x + c
    z = y + d
    result = z + e
    return result

def process_data(items):
    processed = []
    for item in items:
        if item > 0:
            processed.append(item * 2)
        else:
            processed.append(item * 3)
    return processed
