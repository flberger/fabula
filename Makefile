FILES = shard/assetengine.py \
        shard/clientcoreengine.py \
        shard/coreengine.py \
        shard/eventprocessor.py \
        shard/__init__.py \
        shard/interfaces.py \
        shard/plugin.py \
        shard/presentationengine.py \
        shard/run.py \
        shard/servercoreengine.py

help:
	@echo Targets: docs, check, errors, doctest

docs: 
	rm -fv shard/*.pyc
	/home/florian/temp/python/pydoctor/bin/pydoctor --verbose \
	                                                --add-package shard \
	                                                --make-html \
	                                                --html-output doc/

check:
	pylint shard

errors:
	pylint --errors-only shard

doctest:
	python3 -m doctest shard-doctests.txt
