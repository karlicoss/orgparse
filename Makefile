## Run test
test: cog
	tox


## Build document
doc: cog
	make -C doc html


## Update files using cog.py
cog: orgparse/__init__.py
orgparse/__init__.py: README.rst
	cd orgparse && cog.py -r __init__.py

.PHONY: clean
clean:
	rm -rf dist/*


build: clean cog
	python3 setup.py sdist bdist_wheel

targets := $(wildcard dist/*)

check: build $(targets)
	twine check $(targets)



## https://packaging.python.org/guides/using-testpypi
.PHONY: test-upload
test-upload: check $(targets)
	twine upload --verbose --repository-url https://test.pypi.org/legacy/ $(targets)


## Upload to PyPI
.PHONY: upload
upload: check $(target)
	twine upload --verbose $(targets)

