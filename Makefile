docs: doc/shard.html doc/shard.assetengine.html doc/shard.clientcoreengine.html doc/shard.presentationengine.html doc/shard.servercoreengine.html doc/shard.interfaces.html doc/shard.coreengine.html

doc/shard.html: shard/__init__.py
	pydoc -w shard
	mv shard.html doc/

doc/shard.assetengine.html: shard/assetengine.py
	pydoc -w shard.assetengine
	mv shard.assetengine.html doc/

doc/shard.clientcoreengine.html: shard/clientcoreengine.py
	pydoc -w shard.clientcoreengine
	mv shard.clientcoreengine.html doc/

doc/shard.presentationengine.html: shard/presentationengine.py
	pydoc -w shard.presentationengine
	mv shard.presentationengine.html doc/

doc/shard.servercoreengine.html: shard/servercoreengine.py
	pydoc -w shard.servercoreengine
	mv shard.servercoreengine.html doc/

doc/shard.interfaces.html: shard/interfaces.py
	pydoc -w shard.interfaces
	mv shard.interfaces.html doc/

doc/shard.coreengine.html: shard/coreengine.py
	pydoc -w shard.coreengine
	mv shard.coreengine.html doc/
