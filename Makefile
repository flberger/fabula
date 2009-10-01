docs: doc/shard.html doc/shard.assetengine.html doc/shard.clientcoreengine.html doc/shard.presentationengine.html doc/shard.servercoreengine.html doc/shard.interfaces.html doc/shard.coreengine.html doc/shard.plugin.html

doc/shard.html: shard/__init__.py
	rm -fv shard/__init__.pyc
	pydoc -w shard
	mv shard.html doc/

doc/shard.assetengine.html: shard/assetengine.py
	rm -fv shard/assetengine.pyc
	pydoc -w shard.assetengine
	mv shard.assetengine.html doc/

doc/shard.clientcoreengine.html: shard/clientcoreengine.py
	rm -fv shard/clientcoreengine.pyc
	pydoc -w shard.clientcoreengine
	mv shard.clientcoreengine.html doc/

doc/shard.presentationengine.html: shard/presentationengine.py
	rm -fv shard/presentationengine.pyc
	pydoc -w shard.presentationengine
	mv shard.presentationengine.html doc/

doc/shard.servercoreengine.html: shard/servercoreengine.py
	rm -fv shard/servercoreengine.pyc
	pydoc -w shard.servercoreengine
	mv shard.servercoreengine.html doc/

doc/shard.interfaces.html: shard/interfaces.py
	rm -fv shard/interfaces.pyc
	pydoc -w shard.interfaces
	mv shard.interfaces.html doc/

doc/shard.coreengine.html: shard/coreengine.py
	rm -fv shard/coreengine.pyc
	pydoc -w shard.coreengine
	mv shard.coreengine.html doc/

doc/shard.plugin.html: shard/plugin.py
	rm -fv shard/plugin.pyc
	pydoc -w shard.plugin
	mv shard.plugin.html doc/
