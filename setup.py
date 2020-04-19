# see https://github.com/karlicoss/pymplate for up-to-date reference
#
from setuptools import setup, find_packages # type: ignore


def main():
    import orgparse
    setup(
        name='orgparse',
        use_scm_version={
            'version_scheme': 'python-simplified-semver',
            'local_scheme': 'dirty-tag',
        },
        setup_requires=['setuptools_scm'],

        zip_safe=False,

        packages=[
            'orgparse',
            'orgparse.utils',
            'orgparse.tests',
            'orgparse.tests.data',
        ],
        package_data={
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
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Topic :: Text Processing :: Markup',
            # see: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        ],
    )


if __name__ == '__main__':
    main()
