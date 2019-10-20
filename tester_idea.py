
import os
import time
import requests
import json
from itertools import zip_longest

from secrets import key

from urllib.parse import urlencode

from utils import grouper, min_max

gw2_base = 'https://api.guildwars2.com'

class Uri:
    def __init__(self, base, params=None):
        self.base = base
        if params is None:
            self.params = {}
        else:
            self.params = params

    def __str__(self):
        result = self.base
        if self.params:
            result += "?"
            result += urlencode(self.params)
        
        return result

    def __call__(self, **params):
        return Uri(self.base,
                   dict(self.params, **params))

    def __getattr__(self, attr):
            return Uri(self.base + '/' + attr,
                       self.params)

    def __getitem__(self, item):
        if isinstance(item, slice):
            int_str = [i for i in range(item.stop)][item.start:item.stop:item.step]
            return self.__getattr__(','.join([str(i) for i in int_str]))
        else:
            return self.__getattr__(str(item))

    def __repr__(self):
        return f'Uri(base={self.base}, params={self.params})'

class Cacheable:
    """
    only tested on caching strings
    """
    def __init__(self, cache_location):
        self.cache_location = cache_location
        self.folder_path = os.path.dirname(self.cache_location)

    def __call__(self, call, *args, **kwargs):
        """
        Call this with a callable and results are returned from the function with items returned and cached.
        """
        cached_value = self.get_result()
        if cached_value is None:
            value = call(*args, **kwargs)
            print(f"callable result: {value}")
            self.save_result(value)
            return value
        else:
            return cached_value

    def save_result(self, result):
        if not os.path.isdir(self.folder_path):
            os.makedirs(self.folder_path)
        with open(self.cache_location, 'w') as writer:
            writer.write(result)

    def get_result(self):
        if os.path.isfile(self.cache_location):
            with open(self.cache_location, 'r') as reader:
                return reader.read()
        else:
            return None

class EndPoint:
    def __init__(self, uri, cache_handler=None):
        self.uri = uri
        self.cache_handler = cache_handler

    def get_cache_location(self):
        if self.cache_handler:
            return self.cache_handler.cache_location
        else:
            return None

DEBUG = True

class RequestHandler:
    def __init__(self, request_timeout=5):
        self._timeout = request_timeout

    def _perform_request(self, uri, headers, is_get=True):
        time.sleep(self._timeout)
        if DEBUG:
            print(uri)
        if headers is None:
            headers = {}
        if is_get:
            return requests.get(uri)
        else:
            return requests.post(uri)

    def get(self, uri, headers=None, cache_handler=None):
        if cache_handler:
            def request_cachable_ret(uri, headers):
                print(f"Perform cacheable ret: {uri}")
                value = self._perform_request(uri, headers, True)
                if value.status_code == 200:
                    return json.dumps(value.json())
                else:
                    return ""

            value = cache_handler(request_cachable_ret, 
                                  uri,
                                  headers)
            try:
                value = json.loads(value)
            except:
                value = ""
        else:
            value = self._perform_request(uri,
                                          headers,
                                          is_get=True)
        return value
        
gw2_uris = [
    Uri(gw2_base).v2.account,
    Uri(gw2_base).v2.account.achievements,
    Uri(gw2_base).v2.account.bank,
    Uri(gw2_base).v2.account.dailycrafting,
    Uri(gw2_base).v2.account.dungeons,
    Uri(gw2_base).v2.account.dyes,
    Uri(gw2_base).v2.account.finishers,
    Uri(gw2_base).v2.account.gliders,
    Uri(gw2_base).v2.account.home.cats,
    Uri(gw2_base).v2.account.home.nodes,
    Uri(gw2_base).v2.account.inventory,
    Uri(gw2_base).v2.account.luck,
    Uri(gw2_base).v2.account.mailcarries,
    Uri(gw2_base).v2.account.mapchests,
    Uri(gw2_base).v2.account.masteries,
    Uri(gw2_base).v2.account.mastery.points,
    Uri(gw2_base).v2.account.materials,
    Uri(gw2_base).v2.account.minis,
    Uri(gw2_base).v2.account.mounts.skins,
    Uri(gw2_base).v2.account.mounts.types,
    Uri(gw2_base).v2.account.novelties,
    Uri(gw2_base).v2.account.outfits,
    Uri(gw2_base).v2.account.pvp.heroes,
    Uri(gw2_base).v2.account.raids,
    Uri(gw2_base).v2.account.recipes,
    Uri(gw2_base).v2.account.skins,
    Uri(gw2_base).v2.account.titles,
    Uri(gw2_base).v2.account.wallet,
    Uri(gw2_base).v2.account.worldbosses,
    Uri(gw2_base).v2.account.characters,
    Uri(gw2_base).v2.account.commerce.transactions,
    Uri(gw2_base).v2.account.pvp.stats,
    Uri(gw2_base).v2.account.pvp.games,
    Uri(gw2_base).v2.account.pvp.standings,
    Uri(gw2_base).v2.account.tokeninfo,

    # daily rewards
    Uri(gw2_base).v2.dailycrafting,
    Uri(gw2_base).v2.mapchests,
    Uri(gw2_base).v2.worldbosses,

    # game mechanics
    (Uri(gw2_base).v2.masteries, Cacheable(os.path.join('cache', 'masteries'))),
    (Uri(gw2_base).v2.mounts, Cacheable(os.path.join('cache', 'mounts'))),
    (Uri(gw2_base).v2.mounts.skins, Cacheable(os.path.join('cache', 'mounts_skins'))),
    (Uri(gw2_base).v2.materials, Cacheable(os.path.join('cache', 'materials')))
]


def generate_endpoints_from_ids(id_listing, name, cache_path_format):
    new_endpoints = []
    pass




items_ids_endpoint = EndPoint(Uri(gw2_base).v2.items, Cacheable(os.path.join('cache', 'items_ids')))
items_stats_ids = EndPoint(Uri(gw2_base).v2.itemstats, Cacheable(os.path.join('cache', 'itemstats_ids')))
pvp_amulet_ids = EndPoint(Uri(gw2_base).v2.pvp.amulets, Cacheable(os.path.join('cache', 'pvp', 'amulets_ids')))

def build_endpoints(uri_list):
    for uri in uri_list:
        if isinstance(uri, Uri):
            yield EndPoint(uri)
        else:
            yield EndPoint(uri[0], uri[1])            

gw2_endpoints = list(build_endpoints(gw2_uris))
gw2_endpoints.extend([items_ids_endpoint, items_stats_ids,
                      pvp_amulet_ids])

global_params = {
    'access_token' : key
}

if __name__ == "__main__":

    k = Uri('hello world')
    j = k.wakka
    assert(k != j)
    assert(str(k) == str(Uri('hello world')))
    

    r = RequestHandler()

    generate_endpoints_from_ids(r, items_ids_endpoint, 'item', [Cacheable(os.path.join('cache', 'item_', i)
    #appended_id_api_gen(gw2_endpoints, 'itemstats', items_stats_ids, CacheableUri)
    #appended_id_api_gen(gw2_endpoints, 'pvp/amulets', pvp_amulet_ids, CacheableUri)
    for i in filter(lambda x: x.get_cache_location(), gw2_endpoints):
        print("Getting the things!")
        print(i.uri(**global_params))
        print(r.get(i.uri(**global_params), cache_handler=i.cache_handler))
