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
	@echo '    winxp_update'
	@echo '    clean'
	@echo '    user_install'
	@echo '    sdist'
	@echo '    exe'
	@echo '    commit.txt'
	@echo '    commit'
	@echo '    sign'
	@echo '    freecode'
	@echo '    pypi'
	@echo '    lp'

docs: clean
	pydoctor --verbose \
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
	@echo --------------------------- && \
	echo Testing  tests/imports.txt && \
	echo --------------------------- && \
	$(PYTHON) -m doctest tests/imports.txt && \
	echo --------------------------- && \
	echo Testing  tests/entity.txt && \
	echo --------------------------- && \
	$(PYTHON) -m doctest tests/entity.txt && \
	echo --------------------------- && \
	echo Testing  tests/client.txt && \
	echo --------------------------- && \
	$(PYTHON) -m doctest tests/client.txt && \
	echo --------------------------- && \
	echo Testing  tests/server.txt && \
	echo --------------------------- && \
	$(PYTHON) -m doctest tests/server.txt && \
	echo --------------------------- && \
	echo Testing  tests/standalone.txt && \
	echo --------------------------- && \
	$(PYTHON) -m doctest tests/standalone.txt && \
	echo --------------------------- && \
	echo Testing  tests/assets.txt && \
	echo --------------------------- && \
	$(PYTHON) -m doctest tests/assets.txt && \
	echo --------------------------- && \
	echo Testing  tests/pygame_user_interface.txt && \
	echo --------------------------- && \
	$(PYTHON) -m doctest tests/pygame_user_interface.txt && \
	echo --------------------------- && \
	echo Testing  tests/tiles.txt && \
	echo --------------------------- && \
	$(PYTHON) -m doctest tests/tiles.txt && \
	echo --------------------------- && \
	echo Testing  tests/serverside_event_queue.txt && \
	echo --------------------------- && \
	$(PYTHON) -m doctest tests/serverside_event_queue.txt && \
	echo --------------------------- && \
	echo Testing  tests/tcp_networking.txt && \
	echo --------------------------- && \
	$(PYTHON) -m doctest tests/tcp_networking.txt && \
	echo --------------------------- && \
	echo Testing  tests/json.txt && \
	echo --------------------------- && \
	$(PYTHON) -m doctest tests/json.txt && \
	echo --------------------------- && \
	echo Testing  tests/json_rpc.txt && \
	echo --------------------------- && \
	$(PYTHON) -m doctest tests/json_rpc.txt && \
	echo --------------------------- && \
	echo Done testing. && \
	echo ---------------------------

user_install:
	$(PYTHON) setup.py install --user --record user_install-filelist.txt

sdist:
	@# On April 14, 2011 11:34am, Xandar Kablandar (eternalcheesecake) hinted at 
	@# symbolic links in the .tar.bz2 file. These are stored by --formats=bztar 
	@# but not by --formats=zip. Since there is no setup.py option to dereference 
	@# symbolic links, we only use zip for the time being.
	@# Filed issue 12585 at http://bugs.python.org for this.
	@#
	rm -fv MANIFEST
	$(PYTHON) setup.py sdist --force-manifest --formats=zip

exe: sdist
	rm -rf build/exe.*
	$(PYTHON) setup.py build

pypi:
	$(PYTHON) setup.py register

else

doctest:
	@echo Please supply Python executable as PYTHON=executable.

user_install:
	@echo Please supply Python executable as PYTHON=executable.

sdist:
	@echo Please supply Python executable as PYTHON=executable.

exe: sdist
	@echo Please supply Python executable as PYTHON=executable.

pypi:
	@echo Please supply Python executable as PYTHON=executable.

endif

winxp_update: clean
	mount /mnt/winxp/
	rm -vrf /mnt/winxp/Documents\ and\ Settings/winxp/My\ Documents/fabula/*
	cp -v -r --dereference ./COPYING \
	                       ./doc \
	                       ./fabula \
	                       ./Makefile \
	                       ./MANIFEST \
	                       ./NEWS \
	                       ./README \
	                       ./scripts \
	                       ./setup.py \
	                       ./tests \
	                       /mnt/winxp/Documents\ and\ Settings/winxp/My\ Documents/fabula/
	umount /mnt/winxp/

clean:
	@echo About to remove all log files. RETURN to proceed && read DUMMY && rm -vf `find . -iname '*.log'`
	rm -rvf `find . -type d -iname '__pycache__'`
	rm -vf `find . -iname '*.pyc'`

commit.txt:
	# single line because bzr diff returns false when there are diffs
	#
	bzr diff > commit.txt ; nano commit.txt

# First taken from the StepSim Makefile
#
commit:
	@echo commit.txt:
	@echo ------------------------------------------------------
	@cat commit.txt
	@echo ------------------------------------------------------
	@echo RETURN to commit using commit.txt, CTRL-C to cancel:
	@read DUMMY
	bzr commit --file commit.txt && rm -v commit.txt

sign:
	rm -vf dist/*.asc
	for i in dist/*.zip ; do gpg --sign --armor --detach $$i ; done
	gpg --verify --multifile dist/*.asc

freecode:
	@echo RETURN to submit to freecode.com using freecode-submit.txt, CTRL-C to cancel:
	@read DUMMY
	freecode-submit < freecode-submit.txt

lp:
	bzr launchpad-login fberger-fbmd
	bzr push lp:~fberger-fbmd/fabula/trunk
