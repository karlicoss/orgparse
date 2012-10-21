from orgparse.date import OrgDate, OrgDateDeadline


data = [dict(
    heading='Pay the rent',
    todo='TODO',
    deadline=OrgDateDeadline((2005, 10, 1)),
    repeated_tasks=[('DONE', 'TODO', OrgDate((2005, 9, 1, 16, 10, 0))),
                    ('DONE', 'TODO', OrgDate((2005, 8, 1, 19, 44, 0))),
                    ('DONE', 'TODO', OrgDate((2005, 7, 1, 17, 27, 0)))]
)]
