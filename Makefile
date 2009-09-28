docs: doc/shard.html doc/shard.assetengine.html doc/shard.clientcontrolengine.html doc/shard.clientinterface.html doc/shard.visualengine.html doc/shard.servercoreengine.html doc/shard.serverinterface.html doc/shard.messagebuffer.html

doc/shard.html: shard/__init__.py
	pydoc -w shard
	mv shard.html doc/

doc/shard.assetengine.html: shard/assetengine.py
	pydoc -w shard.assetengine
	mv shard.assetengine.html doc/

doc/shard.clientcontrolengine.html: shard/clientcontrolengine.py
	pydoc -w shard.clientcontrolengine
	mv shard.clientcontrolengine.html doc/

doc/shard.clientinterface.html: shard/clientinterface.py
	pydoc -w shard.clientinterface
	mv shard.clientinterface.html doc/

doc/shard.visualengine.html: shard/visualengine.py
	pydoc -w shard.visualengine
	mv shard.visualengine.html doc/

doc/shard.servercoreengine.html: shard/servercoreengine.py
	pydoc -w shard.servercoreengine
	mv shard.servercoreengine.html doc/

doc/shard.serverinterface.html: shard/serverinterface.py
	pydoc -w shard.serverinterface
	mv shard.serverinterface.html doc/

doc/shard.messagebuffer.html: shard/messagebuffer.py
	pydoc -w shard.messagebuffer
	mv shard.messagebuffer.html doc/
