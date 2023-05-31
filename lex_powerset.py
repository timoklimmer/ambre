from typing import List

def lex_powerset(lst: List[str]) -> List[List[str]]:
    lst.sort(reverse=True)
    powerset = []
    stack = [[]]
    while stack:
        subset = stack.pop()
        if subset:
            powerset.append(subset)
            yield(subset)
        for i in range(len(lst)):
            if not subset or lst[i] > subset[-1]:
                new_subset = subset + [lst[i]]
                stack.append(new_subset)

for i in lex_powerset(["a", "b", "c"]):
    print(i)
