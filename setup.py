from distutils.core import setup

import orgparse

setup(
    name='orgparse',
    version=orgparse.__version__,
    packages=['orgparse', 'orgparse.tests', 'orgparse.tests.data'],
    package_data={
        'orgparse.tests.data': ['*.org'],
    },
    author=orgparse.__author__,
    author_email='aka.tkf@gmail.com',
    url='https://github.com/tkf/orgparse',
    license=orgparse.__license__,
    description='orgparse - Emacs org-mode parser in Python',
    long_description=orgparse.__doc__,
    keywords='org-mode, Emacs, parser',
    classifiers=[
        "Development Status :: 3 - Alpha",
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        # see: http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
)
