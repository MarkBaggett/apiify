#!/usr/bin/env python3
#apiify.py by Mark Baggett
#Twitter @MarkBaggett

import logging
import http.server
import expiring_cache
import datetime
import threading
import socketserver
import time
import urllib
import re
import json
import config
import subprocess
import functools
import resource
import pathlib
import os
import itertools
import code

config = config.config("apiify.yaml")
cacheable = lambda _:True
if config.get('no_caching_this_error'):
    cacheable = lambda x:config['no_caching_this_error'].encode() not in x.lower()

def cacheable(item):
    cache_it = config.get('no_caching_this_error').encode() not in item
    cache_it &= "-ERRORNOTCACHED".encode() not in item
    cache_it &= bool(item.strip())  #Don't cache it if it is a blank string (or all spaces)
    if config.get('debug_statements'):
        print("Cached:{} for {}".format(cache_it,item))
    return cache_it

@expiring_cache.expiring_cache(maxsize=config['cached_max_items'], cacheable=cacheable, hours_to_live=config['item_hours_in_cache'])
def exec_command(arguments):
    cli = config.get('base_command')
    cli = cli.replace("*WEBINFO*",arguments)
    try:
        if config['block_command_injection']:
            cli = cli.split()
            ph = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin= subprocess.PIPE)
        else:
            ph = subprocess.Popen(cli, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin= subprocess.PIPE)
        out,err = ph.communicate()
        if config.get('debug_statements'):
            debug_info = "Output {}\nError {}\n\n".format(out,err)
            if config.get("result_regex"):
                reopt = "|".join(itertools.compress(['re.MULTILINE','re.DOTALL','re.IGNORECASE'],
                        [config.get("regex_multiline"),config.get("regex_dotall"),config.get("regex_ignorecase")]))
                if reopt:
                    reopt = ", {}".format(reopt)
                debug_info += "re.findall('{}','{}'{}')".format(config.get('result_regex'),(out+err).decode(),reopt)
            print(debug_info)      
        result = out
        if config['combine_stderr_stdout']:
            result += err
        theregex = config.get('result_regex',"")
        if theregex:
            regex_options = 0
            if config.get("regex_multiline"):
                regex_options |= re.MULTILINE
            if config.get("regex_dotall"):
                regex_options |= re.DOTALL
            if config.get("regex_ignorecase"):
                regex_options |= re.IGNORECASE
            if config.get('regex_findall'):
                result = json.dumps( re.findall(theregex, result.decode(), regex_options)).encode()
            else:
                result = re.search(theregex, result.decode(), regex_options)
                if result:
                    result = json.dumps(result.groupdict()).encode()
                else:
                    result = b"ERROR: No result from regex match.-ERRORNOTCACHED"
    except Exception as e:
        return "ERROR: {}-ERRORNOTCACHED".format(str(e)).encode()
    return result

class apiify(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        (ignore, ignore, urlpath, urlparams, ignore) = urllib.parse.urlsplit(self.path)
        urlpath = urllib.parse.unquote_plus(urlpath)
        if urlpath=="/cache":
            self.wfile.write(exec_command.cache.cache_report().encode())
        elif urlpath=="/stats":
            self.wfile.write(exec_command.cache.cache_info().encode())
        elif re.search("[\/?](.*)", urlpath):
            part = re.search("[\/?](.*)",urlpath)
            args = part.group(1)
            result = exec_command(args)
            self.wfile.write(result)
        else:
            api_hlp = 'API Documentation\nhttp://%s:%s/arguments to pass.' % (self.server.server_address[0], self.server.server_address[1])
            self.wfile.write(api_hlp.encode())
        return

    def log_message(self, format, *args):
        return


class ThreadedApiIfy(socketserver.ThreadingMixIn, http.server.HTTPServer):
    def __init__(self, *args,**kwargs):
        self.args = ""
        self.screen_lock = threading.Lock()
        self.exitthread = threading.Event()
        self.exitthread.clear()
        http.server.HTTPServer.__init__(self, *args, **kwargs)

if __name__ == "__main__":
    if pathlib.Path(config['cache_file']).exists() and input("Load Cache?").lower().startswith("y"):
        exec_command.cache.cache_load(config['cache_file'])
    server = ThreadedApiIfy((config['local_address'], config['local_port']), apiify)
    print("Resolving command {}".format(config.get("base_command")))
    print('Server is Ready. http://%s:%s/arguments' % (config['local_address'], config['local_port']))
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    try:
        server_thread.start()
        #code.interact(local=locals())
        while True: time.sleep(100)
    except (KeyboardInterrupt, SystemExit):
        server.shutdown()
        server.server_close()     
    print("Web API Disabled...")
    print("Control-C hit: Exiting server.  Please wait..")
    exec_command.cache.cache_dump(config['cache_file'])
    
    print("Bye!")
