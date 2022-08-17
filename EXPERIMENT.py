persons = [
    ["http://one.com"],
    ["http://one.com", "four"],
    ["http://two.com", "three"],
    ["three", "five", "six"],
]


def merge(lists, results=None):

    if results is None:
        results = []

    if not lists:
        return results

    first = sorted(lists, key=len, reverse=True)[0]
    merged = []
    output = []

    for li in sorted(lists, key=len, reverse=True)[1:]:
        for i in first:
            if i in li:
                merged = merged + li
                break
        else:
            output.append(li)

    merged = merged + first
    results.append(list(set(merged)))

    return merge(output, results)


print(merge(persons))
