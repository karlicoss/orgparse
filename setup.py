from distutils.core import setup

import orgparse

setup(
    name='orgparse',
    version=orgparse.__version__,
    packages=['orgparse'],
    author=orgparse.__author__,
    author_email='aka.tkf@gmail.com',
    url='https://github.com/tkf/orgparse',
    license=orgparse.__license__,
    description='orgparse - Emacs org-mode parser in Python',
    long_description=orgparse.__doc__,
    keywords='org-mode, Emacs, parser',
    classifiers=[
        "Development Status :: 3 - Alpha",
        # see: http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
)
