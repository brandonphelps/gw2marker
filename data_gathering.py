
from secrets import key

from enum import Enum
import time
import requests
import re
import os
import json

from functools import lru_cache

import hashlib

def RateLimited(maxPerSecond):
    minInterval = 1.0 / float(maxPerSecond)
    def decorate(func):
        lastTimeCalled = [0.0]
        def rateLimitedFunction(*args, **kwargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait > 0:
                time.sleep(leftToWait)
            ret = func(*args, **kwargs)
            lastTimeCalled[0] = time.clock()
            return ret
        return rateLimitedFunction
    return decorate

class Uri(Enum):
    account_materials = ('account/materials', True)
    account_bank = ('account/bank', True)
    items = ('items/{}', False, 1)
    recipes = ('recipes/{}', False, 1)
    commerce_listings = ('commerce/listings/{}', False, 1)
    commerce_prices = ('commerce/prices/{}', False, 1)
    characters = ('characters/{}', True, 1)
    character_crafting = ('characters/{}/crafting', True, 1)
    character_recipes = ('characters/{}/recipes', True, 1)


    def __init__(self, path, requires_auth, optional_param_count=0):
        self.path = path
        self.requires_auth = requires_auth
        self.optional_param_count = optional_param_count


class GW2Request:

    base_url = 'https://api.guildwars2.com'

    def __init__(self, version):
        self.version = version

    def perform_request(self, option, *args):
        uri = "{}/{}/{}".format(self.base_url, self.version, option.path)
        if option.optional_param_count != 0:
            if len(args) > 0:
                uri = uri.format(*args)
            else:
                uri = uri.replace('{', '').replace('}', '')
        if option.requires_auth:
            uri += "?access_token={}".format(key)

        return self._perform_request(uri)

    def _perform_request(self, uri):
        #print(uri)
        r = requests.get(uri)
        if r:
            return r.json()
        return None


requester = GW2Request('v2')

cached_folder = 'requests_cache'

def cache_data(func):
    def inner(*args, **kwargs):
        inter_folder = func.__name__
        m = hashlib.sha256()
        for i in args:
            m.update(str(i).encode('utf-8'))
        full_path = os.path.join(cached_folder, inter_folder, m.hexdigest())

        if not os.path.isdir(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))

        #print("filename: {}".format(full_path))
        if os.path.isfile(full_path):
            with open(full_path, 'r') as reader:
                val = json.loads(reader.read())
        else:
            val = func(*args, **kwargs)
            with open(full_path, 'w') as writer:
                writer.write(json.dumps(val))
        return val
    return inner

#todo: figure out if the cache_data function can be used in this function
#        or see if there is some common code that could be grouped 
def timed_cache_data(timeout):
    def wrapper(func):
        def inner(*args, **kwargs):
            inter_folder = func.__name__
            m = hashlib.sha256()
            for i in args:
                m.update(str(i).encode('utf-8'))
            full_path = os.path.join(cached_folder, inter_folder, m.hexdigest())

            if not os.path.isdir(os.path.dirname(full_path)):
                os.makedirs(os.path.dirname(full_path))

            #print("filename: {}".format(full_path))
            #print("Current time: {}".format(time.time()))
            # TODO: just lazy, but do a function for writing so it shared, 
            if os.path.isfile(full_path):
                with open(full_path, 'r') as reader:
                    timed_result = json.loads(reader.read())
                # check if we need to write resultant back in since we passed timeout
                #print(timed_result)
                if timed_result['rewrite_time'] <= time.time():
                    print("Recomputing: {}({})".format(func.__name__, args))
                    val = func(*args, **kwargs)
                    timed_result = {'rewrite_time': time.time() + timeout,
                                    'value' : val}
                    with open(full_path, 'w') as writer:
                        writer.write(json.dumps(timed_result))
                else:
                    val = timed_result['value']
            else:
                val = func(*args, **kwargs)
                timed_result = {'rewrite_time' : time.time() + timeout,
                                'value' : val}
                
                with open(full_path, 'w') as writer:
                    writer.write(json.dumps(timed_result))
            return val
        return inner
    return wrapper


####### data caching

class NoSellsException(Exception):
    # No available sellers
    pass
    
class NoBuyException(Exception):
    # No available buyers
    pass


@cache_data
def get_item_info(item_id):
    item_info = requester.perform_request(Uri.items, item_id)
    return item_info

@cache_data
def get_recipe_ids():
    recipe_ids = requester.perform_request(Uri.recipes)
    return recipe_ids

@cache_data
def get_recipe_info(recipe_id):
    recipe_info = requester.perform_request(Uri.recipes, recipe_id)
    return recipe_info

@cache_data
def get_recipe_max_buy_price(recipe_id):
    recipe_info = get_recipe_info(recipe_id)
    return get_item_max_buy_price(recipe_info['output_item_id'])


@timed_cache_data(3 * 60) # 3 minutes
def get_item_max_buy_price(item_id):
    item_info = requester.perform_request(Uri.commerce_listings, item_id)
    if item_info is None:
        print("Failed to get item info for id: {}".format(item_id))

    if item_info and item_info['buys']:
        return max(item_info['buys'], key=lambda x: int(x['unit_price']))['unit_price']
    else:
        return 0

@timed_cache_data(3 * 60) # 3 minutes
def get_item_min_sell_price(item_id):
    item_info = requester.perform_request(Uri.commerce_listings, item_id)
    if item_info is None:
        return 100000000
    if item_info and item_info['sells']:
        return min(item_info['sells'], key=lambda x: int(x['unit_price']))['unit_price']
    else:
        # todo add exception handling
        return 100000000

@cache_data
def get_characters(char=None):
    if char:
        return requester.perform_request(Uri.characters, char)
    else:
        return requester.perform_request(Uri.characters)

@cache_data
def get_character_crafting(char_name):
    return requester.perform_request(Uri.character_crafting, char_name)

@cache_data
def get_character_recipes(char_name):
    return requester.perform_request(Uri.character_recipes, char_name)

def get_known_recipes():
    return [(j, i) for j in get_characters() for i in get_character_recipes(j)['recipes']]

@timed_cache_data(10)
def tester(x):
    time.sleep(2)
    return x*10*10*10*(10**10)*(10**10)

if __name__ == '__main__':
    print(tester(12))
