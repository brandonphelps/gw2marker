def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def min_max(iterable):
    min_v = max_v = next(iterable)
    for j in iterable:
        if min_v > j:
            min_v = j
        if max_v < j:
            max_v = j
    return min_v, max_v
