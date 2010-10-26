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
	@echo Targets: docs, check, errors, doctest, win2k_update

docs: clean
	/home/florian/temp/python/pydoctor/bin/pydoctor --verbose \
	                                                --add-package shard \
	                                                --make-html \
	                                                --html-output doc/

check:
	@echo WARNING: using pylint for Python 2.x instead of 3.x.
	pylint shard

errors:
	@echo WARNING: using pylint for Python 2.x instead of 3.x.
	pylint --errors-only shard

doctest: clean
	python3 -m doctest tests/imports.txt
	python3 -m doctest tests/client.txt
	python3 -m doctest tests/server.txt
	python3 -m doctest tests/standalone.txt
	python3 -m doctest tests/assets.txt
	python3 -m doctest tests/pygame_user_interface.txt
	python3 -m doctest tests/tiles.txt

make win2k_update: clean
	mount /mnt/win2k/
	rm -rf /mnt/win2k/Dokumente\ und\ Einstellungen/user/Eigene\ Dateien/test/*
	cp -r ./* /mnt/win2k/Dokumente\ und\ Einstellungen/user/Eigene\ Dateien/test/
	cp /home/florian/programmieren/python/clickndrag/clickndrag_bzr-repo/clickndrag/clickndrag.py \
	   /mnt/win2k/Dokumente\ und\ Einstellungen/user/Eigene\ Dateien/test/
	umount /mnt/win2k/

clean:
	rm -vf *pyc
	rm -vf */*pyc
	rm -vf */*/*pyc
