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
	@echo '    commit.txt'
	@echo '    commit'
	@echo '    sign'

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
	$(PYTHON) -m doctest tests/imports.txt && \
	$(PYTHON) -m doctest tests/entity.txt && \
	$(PYTHON) -m doctest tests/client.txt && \
	$(PYTHON) -m doctest tests/server.txt && \
	$(PYTHON) -m doctest tests/standalone.txt && \
	$(PYTHON) -m doctest tests/assets.txt && \
	$(PYTHON) -m doctest tests/pygame_user_interface.txt && \
	$(PYTHON) -m doctest tests/tiles.txt && \
	$(PYTHON) -m doctest tests/serverside_event_queue.txt && \
	$(PYTHON) -m doctest tests/tcp_networking.txt

user_install:
	$(PYTHON) setup.py install --user --record user_install-filelist.txt

sdist:
	# On April 14, 2011 11:34am, Xandar Kablandar (eternalcheesecake) hinted at 
	# symbolic links in the .tar.bz2 file. These are stored by --formats=bztar 
	# but not by --formats=zip. Since there is no setup.py option to dereference 
	# symbolic links, we only use zip for the time being.
	# Filed issue 12585 at http://bugs.python.org for this.
	#
	$(PYTHON) setup.py sdist --force-manifest --formats=zip

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
	rm -rf /mnt/win2k/Dokumente\ und\ Einstellungen/user/Eigene\ Dateien/fabula/*
	cp -r --dereference ./* /mnt/win2k/Dokumente\ und\ Einstellungen/user/Eigene\ Dateien/fabula/
	umount /mnt/win2k/

clean:
	rm -vf *.pyc
	rm -vf */*.pyc
	rm -vf */*/*.pyc
	rm -vf *.log
	rm -vf */*.log
	rm -vf */*/*.log

commit.txt:
	# single line because bzr diff returns false when there are diffs
	#
	bzr diff > commit.txt ; nano commit.txt

# Taken from the StepSim Makefile
#
commit:
	@echo RETURN to commit using commit.txt, CTRL-C to cancel:
	@read DUMMY
	bzr commit --file commit.txt && rm -v commit.txt

sign:
	rm -vf dist/*.asc
	for i in dist/*.zip ; do gpg --sign --armor --detach $$i ; done
	gpg --verify --multifile dist/*.asc

freshmeat:
	@echo RETURN to submit to freshmeat.net using freshmeat-submit.txt, CTRL-C to cancel:
	@read DUMMY
	freshmeat-submit < freshmeat-submit.txt
