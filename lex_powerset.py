from typing import List

def lex_powerset(lst: List[str]) -> List[List[str]]:
    lst = list(set(lst))
    lst.sort(reverse=True)
    stack = [[]]
    while stack:
        subset = stack.pop()
        if subset:
            yield(subset)
        for i in range(len(lst)):
            if not subset or lst[i] > subset[-1]:
                new_subset = subset + [lst[i]]
                stack.append(new_subset)

items = ["a", "b", "c", "d", "e"]

counter = 0
for i in lex_powerset(items):
    print(i)
    counter += 1

print(counter)

expected_counter = 2 ** len(items) - 1
print(expected_counter)

assert(counter == expected_counter)
