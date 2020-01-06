#!/usr/bin/env python3
#domain_stats.py by Mark Baggett
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
import code

config = config.config("apiify.yaml")
cacheable = lambda _:True
if config['no_caching_when_stderr']:
    cacheable = lambda x:config['no_caching_when_stderr'].encode() not in x.lower()

def dateconverter(o):
    if isinstance(o, datetime.datetime):
        return o.strftime("%Y-%m-%d %H:%M:%S")

@expiring_cache.expiring_cache(maxsize=config['cached_max_items'], cacheable=cacheable, hours_to_live=config['item_hours_in_cache'])
def exec_command(arguments):
    try:
        if config['block_command_injection']:
            cli = config['base_command'].split()+ arguments.split()
            ph = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin= subprocess.PIPE)
        else:
            cli = config['base_command']+ " " + arguments
            ph = subprocess.Popen(cli, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin= subprocess.PIPE)
        out,err = ph.communicate()
        result = out
        if config['combine_stderr_stdout']:
            result += err
        print("Command output:", result.decode())
        theregex = config.get('result_regex',"")
        #import pdb;pdb.set_trace()
        if theregex:
            result = re.search(theregex.encode(), result, re.MULTILINE|re.IGNORECASE)
            if result:
                result = str(result.groupdict()).encode()
            else:
                result = b"No result from regex match. Command probably failed."
        print('After regex', result)
    except Exception as e:
        return str(e).encode()
    return result

class apiify(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global base_command
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        cmd = config['base_command']
        (ignore, ignore, urlpath, urlparams, ignore) = urllib.parse.urlsplit(self.path)
        urlpath = urllib.parse.unquote_plus(urlpath)
        if re.search("[\/?](.*)", urlpath):
            part = re.search("[\/?](.*)",urlpath)
            args = part.group(1)
            print("Executing",cmd, args)
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
    server = ThreadedApiIfy((config['local_address'], config['local_port']), apiify)
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
    print("Bye!")