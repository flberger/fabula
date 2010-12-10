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
	@echo Targets:
	@echo '    docs'
	@echo '    check'
	@echo '    errors'
	@echo '    doctest'
	@echo '    win2k_update'
	@echo '    clean'
	@echo '    zip'
	@echo '    user_install'

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

ifdef PYTHON

doctest: clean
	$(PYTHON) -m doctest tests/imports.txt
	$(PYTHON) -m doctest tests/client.txt
	$(PYTHON) -m doctest tests/server.txt
	$(PYTHON) -m doctest tests/standalone.txt
	$(PYTHON) -m doctest tests/assets.txt
	$(PYTHON) -m doctest tests/pygame_user_interface.txt
	$(PYTHON) -m doctest tests/tiles.txt

else

doctest:
	@echo Please supply Python executable as PYTHON=executable.

endif

win2k_update: clean
	mount /mnt/win2k/
	rm -rf /mnt/win2k/Dokumente\ und\ Einstellungen/user/Eigene\ Dateien/test/*
	cp -r --dereference ./* /mnt/win2k/Dokumente\ und\ Einstellungen/user/Eigene\ Dateien/test/
	umount /mnt/win2k/

clean:
	rm -vf *.pyc
	rm -vf */*.pyc
	rm -vf */*/*.pyc
	rm -vf *.log
	rm -vf */*.log
	rm -vf */*/*.log

zip: clean
	cd .. ; rm -fv shard.zip ; zip -9 -r shard.zip main -x '*bzr*'

user_install:
	python3 setup.py install --user
