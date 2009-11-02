docs: shard/assetengine.py shard/clientcoreengine.py shard/coreengine.py shard/eventprocessor.py shard/__init__.py shard/interfaces.py shard/plugin.py shard/presentationengine.py shard/run.py shard/servercoreengine.py
	rm -fv shard/*.pyc
	/home/florian/temp/pydoctor/bin/pydoctor --verbose \
	                                         --add-package shard \
	                                         --make-html \
	                                         --html-output doc/
