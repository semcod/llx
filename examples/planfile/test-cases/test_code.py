
def calculate_total(items):
    total = 0
    for item in items:
        if item > 0:
            total = total + item
        else:
            total = total - item
    return total

def process_list(data):
    result = []
    for i in range(len(data)):
        if data[i] % 2 == 0:
            result.append(data[i] * 2)
        else:
            result.append(data[i] * 3)
    return result
