import expiring_cache
import config
import argparse
import datetime
import pathlib
import sys
import requests

parser= argparse.ArgumentParser()
parser.add_argument("-s", "--sort", choices=["key","age","count","data"],help="Specify how you want the data sorted. Default is key.",default="key")
parser.add_argument("-n","--no_update",action="store_true",help="Do not force cache dump of APIify before processing cache.")
args = parser.parse_args()

config = config.config("apiify.yaml")
save_url = "http://{}:{}/save".format(config["local_address"],config["local_port"])
cache_file = pathlib.Path(config["cache_file"])


if not args.no_update:
    try:
        result = requests.get(save_url)
    except:
        print("Unable to reach {} to request the cache be save.".format(save_url))
        result = None
    else:
        print("Successfully forced apiify to save it cache. Use -n to disable this feature.")
    if result and result.status_code != 200:
        print("Unable to reach {} to request the cache be save. {}".format(save_url, result.reason))


if not cache_file.is_file():
    print("The cache file {} does not exist. You might visit {} to force the cache to save to disk.".format(str(cache_file),save_url))
    sys.exit(1)
if (datetime.datetime.now().timestamp() - cache_file.stat().st_mtime) // 60  > 10:
    print("*"*80)
    print("WARNING: Cache file is more than 10 minutes old. Consider forcing the current data in memory to disk by visiting {}".format(save_url))
    print("*"*80)
    
cache_data = expiring_cache.ExpiringCache()
cache_data.cache_load(config['cache_file'])


def sort_order(dict_item):
    if args.sort=="key":
        return dict_item[0]
    elif args.sort=="age":
        return dict_item[1][0]
    elif args.sort=="count":
        return dict_item[1][1]
    elif args.sort=="data":
        return dict_item[1][2]


print("Key, Date Cached, Cache Hit Count, Data")
for key,val in sorted(cache_data.items(), key = sort_order):
    print("{}, {}, {}, {}".format(key[0],str(val[0]),val[1], val[2]))