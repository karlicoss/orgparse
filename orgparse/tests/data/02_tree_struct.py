def nodedict(parent, children=[], previous=None, next=None):
    return dict(parent_heading=parent,
                children_heading=children,
                previous_same_level_heading=previous,
                next_same_level_heading=next)


data = [nodedict(*args) for args in [
    # G0
    (None, [], None, 'G1-H1'),
    # G1
    (None, ['G1-H2'], 'G0-H1', 'G2-H1'),
    ('G1-H1', ['G1-H3']),
    ('G1-H2',),
    # G2
    (None, ['G2-H2', 'G2-H3'], 'G1-H1', 'G3-H1'),
    ('G2-H1',),
    ('G2-H1',),
    # G3
    (None, ['G3-H2', 'G3-H3'], 'G2-H1', 'G4-H1'),
    ('G3-H1',),
    ('G3-H1',),
    # G4
    (None, ['G4-H2', 'G4-H3', 'G4-H4'], 'G3-H1', 'G5-H1'),
    ('G4-H1',),
    ('G4-H1',),
    ('G4-H1',),
    # G5
    (None, ['G5-H2', 'G5-H4'], 'G4-H1', 'G6-H1'),
    ('G5-H1', ['G5-H3'], None, 'G5-H4'),
    ('G5-H2',),
    ('G5-H1', [], 'G5-H2'),
    # G6
    (None, ['G6-H2', 'G6-H5'], 'G5-H1', 'G7-H1'),
    ('G6-H1', ['G6-H3', 'G6-H4'], None, 'G6-H5'),
    ('G6-H2',),
    ('G6-H2',),
    ('G6-H1', [], 'G6-H2'),
]]
