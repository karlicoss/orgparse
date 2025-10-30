def nodedict(i, tags):
    return {
        "heading": f"Node {i}",
        "tags": set(tags),
    }


data = [
    nodedict(i, *vals) for (i, vals) in enumerate([
        [["tag"]],
        [["@tag"]],
        [["tag1", "tag2"]],
        [["_"]],
        [["@"]],
        [["@_"]],
        [["_tag_"]],
    ])] + [
        {"heading": 'Heading: :with:colon:', "tags": {"tag"}},
    ] + [
        {"heading": 'unicode', "tags": {'ёж', 'tag', 'háček'}},
    ]  # fmt: skip
