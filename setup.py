# see https://github.com/karlicoss/pymplate for up-to-date reference
#
from setuptools import setup, find_namespace_packages # type: ignore


def main():
    pkg = 'orgparse'
    subpkgs = find_namespace_packages('.', include=(pkg + '.*',))

    import orgparse
    setup(
        name=pkg,
        use_scm_version={
            'version_scheme': 'python-simplified-semver',
            'local_scheme': 'dirty-tag',
        },
        setup_requires=['setuptools_scm'],

        zip_safe=False,

        packages=[pkg, *subpkgs],
        package_data={
            pkg: ['py.typed'], # todo need the rest as well??
            'orgparse.tests.data': ['*.org'],
        },

        author=orgparse.__author__,
        author_email='aka.tkf@gmail.com',
        maintainer='Dima Gerasimov (@karlicoss)',
        maintainer_email='karlicoss@gmail.com',

        url='https://github.com/karlicoss/orgparse',
        license=orgparse.__license__,

        description='orgparse - Emacs org-mode parser in Python',
        long_description=orgparse.__doc__,

        keywords='org org-mode emacs',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'License :: OSI Approved :: BSD License',
            'Topic :: Text Processing :: Markup',
            # see: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        ],

        extras_require={
            'testing': ['pytest'],
            'linting': ['pytest', 'mypy', 'lxml'], # lxml for mypy coverage report
        },
    )


if __name__ == '__main__':
    main()
