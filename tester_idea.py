
import os
import time
import requests
import json

from secrets import key

from urllib.parse import urlencode

gw2_base = 'https://api.guildwars2.com'


class APIEndPoint:
    def __init__(self):
        pass

class JsonAPIEndPoint:
    def __init__(self, url):
        self._url = url

class UriPathPart:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

    def __truediv__(self, other):  # python3 replacement for div
        if isinstance(other, UriPathPart):
            return UriPathPart(self.value + '/' + other.value)
        else:
            return UriPathPart(self.value + '/' + str(other))

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
        return self.__getattr__(str(item))

    def __repr__(self):
        return f'Uri(base={self.base}, params={self.params})'

class CacheableUri(Uri):
    def __init__(self, base, disk_loc, params=None):
        super().__init__(base, params)
        self.disk_loc = disk_loc

    def __call__(self, **params):
        return CacheableUri(self.base,
                            self.disk_loc,
                            dict(self.params, **params))

    def __getattr__(self, attr):
        return CacheableUri(self.base + '/' + attr,
                            self.disk_loc,
                            self.params)

    def __getitem__(self, item):
        return self.__getattr__(str(item))

        
gw2_endpoints = [
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
    CacheableUri(gw2_base, os.path.join('cache', 'masteries')).v2.masteries,
    CacheableUri(gw2_base, os.path.join('cache', 'mounts')).v2.mounts,
    CacheableUri(gw2_base, os.path.join('cache', 'mounts_skins')).v2.mounts.skins,
]

global_params = {
    'access_token' : key
}


# account
# account/achivements
# account/bank
# account/dailycrafting
# account/dungeons
# account/dyes
# account/finishers

DEBUG = True

def get(uri, headers=None):
    if headers is None:
        headers = {}
    if DEBUG:
        print(uri)

    def perform_request():
        time.sleep(2.0)
        return requests.get(uri).json()

    if isinstance(uri, CacheableUri):
        cache_path = uri.disk_loc
        print("creating cached file: {}".format(cache_path))
        if not os.path.isdir(os.path.dirname(cache_path)):
            os.makedirs(os.path.dirname(cache_path))
        if os.path.isfile(cache_path):
            with open(cache_path, 'r') as reader:
                value = json.loads(reader.read())
        else:
            value = perform_request()
            with open(cache_path, 'w') as writer:

                writer.write(json.dumps(value))
    else:
        value = perform_request()

    return value

if __name__ == "__main__":
    for i in gw2_endpoints:
        print(type(i))
    for i in filter(lambda x: isinstance(x, CacheableUri), gw2_endpoints):
    #for i in gw2_endpoints:
        print(i, i.disk_cacheable)
        print(get(i(**global_params)))
