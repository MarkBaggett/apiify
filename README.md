# apiify
Wrap any binary into a cached webserver.  Intended for SEIM implementation.  Its also useful for CTF's if you want to easily stand up a server with a command injection vulnerability.  See 'block_command_injection'

## Installation and Use

![alt text](./apiify.gif "Installation and use")

This program will execute the command specified in the YAML "base_command" and pass any "arguments" from the web interface.  Responses are stored in a higly tuneable cache.  Subsuquent requests for the same arguments will be pulled from the cache until they expire.  Expiration is also controlled by yaml.  Additionally a LRU "Lease Recently Used" size limition is implemented.  When the cache reaches its maximum size the least recently used item is dropped form the cache.

Download and install apiify. You can git clone it or download the [zip](https://github.com/MarkBaggett/apiify/archive/master.zip).

```
git clone http://github.com/markbaggett/apiify
cd apiify
sudo python3 apiify
```

Then send it a request
`$ wget -q -O- http://127.0.0.1:8000/google.com`

Also check how your cache performance is going..
`$ wget -q -O- http://127.0.0.1:8000/stats`

Or see everything in your cache
`$ wget -q -O- http://127.0.0.1:8000/cache`

## Configuration

All configuration of this tool is done by editing apiify.yaml.  Enter the command you want to run by setting the "base_command" option in the yaml file.  In the base_command the string *WEBINFO* will be replaced by the arguments that are typed on the URL.  For example

If base_command is set to `base_command: ping -c1 *WEBINFO*` and you visit the url `http://127.0.0.1:8000/127.0.0.1` then APIIFY will run the command `ping -c1 127.0.0.1` and return the response to the web browswer.

Most likely you will not want ALL of the output from a command so you can specify a regular expression that uses Python Named Capture Groups.  For more information on how to develop these regular expressions see the [Python Documentation](https://docs.python.org/3/howto/regex.html#non-capturing-and-named-groups) or take [SANS SEC573 Automating Information Security with Python](https://www.sans.org/course/automating-information-security-with-python) where the subject is covered in-depth. So in addition to the `base_command` you will likely want to define a `result_regex` using Python Named Capture groups. This will cause APIify to return a JSON response where they KEY is the Python Named Group and the VALUE is the matching data. Setting result_regex like this `result_regex: (?:Creation Date.|created.)\s+(?P<creationdate>[\d:T -]+)` will result in a JSON response containing `{"creationdate": "1996-01-29T05:00:00"}`.

If you do not use Python Named Captured Groups you will still get a response in the form of a list.  To do so you set the `regex_findall` option in the yaml file to True.  For example, the YAML contains an example traceroute configuration that captures all of the responsive hops. The output looks something like this `[["5", "12.242.113.19"], ["6", "12.255.10.8"], ["7", "172.253.71.63"], ["8", "108.170.249.98"], ["9", "216.239.59.153"], ["10", "108.170.228.161"], ["11", "216.239.48.107"], ["21", "64.233.177.113"]]`

Regular Expression modifiers re.IGNORECASE, re.MULTILINE and re.DOTALL can also be set to True or False in the YAML file.

**NOTE: Because colon (":") has special meaning in a YAML file you can not simply include a colon in a regular expression. One technique to get around this limitation to match on any character (".") or a non-space character ("\S") instead of the colon (":").**

There are additional configuration options which are also explained in the YAML file.

The included YAML that has (commented out) examples of base_command and result_regex strings that will execute WHOIS, PING and TRACEROUTE but these are just examples.  You can configure any command line option you would like.



