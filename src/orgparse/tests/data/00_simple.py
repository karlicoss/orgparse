from typing import Any


def nodedict(i, level, todo=None, shallow_tags=None, tags=None) -> dict[str, Any]:
    if tags is None:
        tags = set()
    if shallow_tags is None:
        shallow_tags = set()
    return {
        "heading": f"Heading {i}",
        "level": level,
        "todo": todo,
        "shallow_tags": shallow_tags,
        "tags": tags,
    }


def tags(nums) -> set[str]:
    return set(map('TAG{0}'.format, nums))


data = [
    nodedict(i, *vals) for (i, vals) in enumerate([  # type: ignore[misc]
        [1, 'TODO1', tags([1])   , tags(range(1, 2))],
        [2, 'TODO2', tags([2])   , tags(range(1, 3))],
        [3, 'TODO3', tags([3])   , tags(range(1, 4))],
        [4, 'TODO4', tags([4])   , tags(range(1, 5))],
        [2, None   , tags([])    , tags([1])        ],
        [2, None   , tags([])    , tags([1])        ],
        [1, None   , tags([2])   , tags([2])        ],
        [2, None   , tags([2])   , tags([2])        ],
        [3, None   , tags([])    , tags([2])        ],
        [5, None   , tags([3, 4]), tags([2, 3, 4])  ],
        [4, None   , tags([1])   , tags([1, 2])     ],
        [2, None   , tags([])    , tags([2])        ],
        [1],
    ])]
