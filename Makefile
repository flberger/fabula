FILES = fabula/assetengine.py \
        fabula/clientcoreengine.py \
        fabula/coreengine.py \
        fabula/eventprocessor.py \
        fabula/__init__.py \
        fabula/interfaces.py \
        fabula/plugin.py \
        fabula/presentationengine.py \
        fabula/run.py \
        fabula/servercoreengine.py

help:
	@echo Targets:
	@echo '    docs'
	@echo '    check'
	@echo '    errors'
	@echo '    doctest'
	@echo '    win2k_update'
	@echo '    clean'
	@echo '    user_install'
	@echo '    sdist'
	@echo '    exe'

docs: clean
	/home/florian/temp/python/pydoctor/bin/pydoctor --verbose \
	                                                --add-package fabula \
	                                                --make-html \
	                                                --html-output doc/

check:
	@echo WARNING: using pylint for Python 2.x instead of 3.x.
	pylint fabula

errors:
	@echo WARNING: using pylint for Python 2.x instead of 3.x.
	pylint --errors-only fabula

ifdef PYTHON

doctest: clean
	$(PYTHON) -m doctest tests/imports.txt
	$(PYTHON) -m doctest tests/client.txt
	$(PYTHON) -m doctest tests/server.txt
	$(PYTHON) -m doctest tests/standalone.txt
	$(PYTHON) -m doctest tests/assets.txt
	$(PYTHON) -m doctest tests/pygame_user_interface.txt
	$(PYTHON) -m doctest tests/tiles.txt

user_install:
	$(PYTHON) setup.py install --user --record user_install-filelist.txt

sdist:
	$(PYTHON) setup.py sdist --force-manifest --formats=bztar,zip

exe: sdist
	rm -rf build/exe.*
	$(PYTHON) setup.py build

else

doctest:
	@echo Please supply Python executable as PYTHON=executable.

user_install:
	@echo Please supply Python executable as PYTHON=executable.

sdist:
	@echo Please supply Python executable as PYTHON=executable.

exe: sdist
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
