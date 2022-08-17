persons = [
    [1, 2, 3],
    [7, 100],
    [2, 3, 4],
    [5, 6, 7],
    [7, 8, 9],
    [10, 11, 12],
    [13, 14, 1],
    [100, 42],
]


def merge(lists, results=None):

    if results is None:
        results = []

    if not lists:
        return results

    first = lists[0]
    merged = []
    output = []

    for li in lists[1:]:
        for i in first:
            if i in li:
                merged = merged + li
                break
        else:
            output.append(li)

    merged = merged + first
    results.append(list(set(merged)))

    return merge(output, results)
