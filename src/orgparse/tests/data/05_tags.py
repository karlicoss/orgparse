# -*- coding: utf-8 -*-

def nodedict(i, tags):
    return dict(
        heading="Node {0}".format(i),
        tags=set(tags),
    )


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
        dict(heading='Heading: :with:colon:', tags=set(["tag"])),
    ] + [
        dict(heading='unicode', tags=set(['ёж', 'tag', 'háček'])),
    ]
