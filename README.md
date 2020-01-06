# apiify
Wrap any binary into a cached webserver.  Intended for SEIM implementation.  Its also useful for CTF's if you want to easily stand up a server with a command injection vulnerability.  See 'block_command_injection'

This program will execute the command specified in the YAML "base_command" and pass any "arguments" from the web interface.  Responses are stored in a higly tuneable cache.  Subsuquent requests for the same arguments will be pulled from the cache until they expire.  Expiration is also controlled by yaml.  Additionally a LRU "Lease Recently Used" size limition is implemented.  When the cache reaches its maximum size the least recently used item is dropped form the cache.

The sample YAML configuration will who a whois query.

To try it out start the server
$ python3 apiify.py

And send it a request
$ wget -q -O- http://127.0.0.1:8000/google.com

