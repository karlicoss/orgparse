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
