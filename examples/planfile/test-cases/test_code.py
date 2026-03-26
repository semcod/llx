
def calculate_total(items):
    total = 0
    for item in items:
        if item > 0:
            total = total + item
        else:
            total = total - item
    return total

def process_data(items):
    processed = []
    for item in items:
        if item > 0:
            processed.append(item * 2)
        else:
            processed.append(item * 3)
    return processed
