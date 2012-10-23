def nodedict(i, level, todo=None, shallow_tags=set([]), tags=set([])):
    return dict(
        heading="Heading {0}".format(i),
        level=level,
        todo=todo,
        shallow_tags=shallow_tags,
        tags=tags,
    )


def tags(nums):
    return set(map('TAG{0}'.format, nums))


data = [
    nodedict(i, *vals) for (i, vals) in enumerate([
        [1, 'TODO1', tags([1]), tags(range(1, 2))],
        [2, 'TODO2', tags([2]), tags(range(1, 3))],
        [3, 'TODO3', tags([3]), tags(range(1, 4))],
        [4, 'TODO4', tags([4]), tags(range(1, 5))],
        [2, None, tags([]), tags([1])],
        [2, None, tags([]), tags([1])],
        [1, None, tags([2]), tags([2])],
        [2, None, tags([2]), tags([2])],
        [3, None, tags([]), tags([2])],
        [5, None, tags([3, 4]), tags([2, 3, 4])],
        [4, None, tags([1]), tags([1, 2])],
        [2, None, tags([]), tags([2])],
        [1],
    ])]
