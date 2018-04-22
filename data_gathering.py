
from pprint import pprint
from secrets import key
import math

from enum import Enum
import time
import requests
import re
import os
import json

from functools import lru_cache

from cache_funcs import cache_data, timed_cache_data, get_hash_folder


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
    character_items = ('characters/{}/inventory', True, 1)
    build = ('build', False)

    def __init__(self, path, requires_auth, optional_param_count=0):
        self.path = path
        self.requires_auth = requires_auth
        self.optional_param_count = optional_param_count

class GW2Request:

    base_url = 'https://api.guildwars2.com'

    def __init__(self, version):
        self.version = version
        self.uri = None

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
        # print(self.uri)
        self.uri = uri
        r = requests.get(self.uri)
        if r:
            return r.json()
        return None


requester = GW2Request('v2')


def build_conditional():
    # fetches the build number, compares it to the stored value, if greater, returns true else false
    build_num = get_build()['id']
    full_path = get_hash_folder(build_conditional)
    value = write_or_load(full_path, build_num)
    if int(build_num) > int(value):
        with open(full_path, 'w') as writer:
            writer.write(str(build_num))
        return True
    else:
        return False


####### data caching
class NoSellsException(Exception):
    # No available sellers
    pass
    
class NoBuyException(Exception):
    # No available buyers
    pass

@cache_data(None)
def get_item_info(item_id):
    item_info = requester.perform_request(Uri.items, item_id)
    return item_info

@cache_data(build_conditional)
def get_recipe_ids():
    recipe_ids = requester.perform_request(Uri.recipes)
    return recipe_ids

@cache_data(build_conditional)
def get_recipe_info(recipe_id):
    recipe_info = requester.perform_request(Uri.recipes, recipe_id)
    return recipe_info

@cache_data(None)
def get_recipe_max_buy_price(recipe_id):
    recipe_info = get_recipe_info(recipe_id)
    # print("{}: {}".format(recipe_id, recipe_info))
    return get_item_max_buy_price(recipe_info['output_item_id'])

item_price_time = 10 * 60

@timed_cache_data(item_price_time) # 3 minutes
def get_item_max_buy_price(item_id, wait=False, reduc=.1):
    item_info = requester.perform_request(Uri.commerce_listings, item_id)
    if item_info is None:
        # print("Failed to get item info for id: {}".format(item_id))
        pass
    if wait:
        if item_info and item_info['sells']:
            value =  min(item_info['sells'], key=lambda x: int(x['unit_price']))['unit_price']
            return math.floor(value - (reduc * value))
    else:
        if item_info and item_info['buys']:
            return max(item_info['buys'], key=lambda x: int(x['unit_price']))['unit_price']
    return 0

@timed_cache_data(item_price_time) # 3 minutes
def get_item_min_sell_price(item_id):
    item_info = requester.perform_request(Uri.commerce_listings, item_id)
    if item_info is None:
        return 100000000
    if item_info and item_info['sells']:
        return min(item_info['sells'], key=lambda x: int(x['unit_price']))['unit_price']
    else:
        # todo add exception handling
        return 100000000

@cache_data(None)
def get_characters(char=None):
    if char:
        return requester.perform_request(Uri.characters, char)
    else:
        return requester.perform_request(Uri.characters)

@timed_cache_data(60 * 60)
def get_character_crafting(char_name):
    return requester.perform_request(Uri.character_crafting, char_name)

@timed_cache_data(60 * 60)
def get_character_recipes(char_name):
    value = requester.perform_request(Uri.character_recipes, char_name) 
    if not value:
        value = {'recipes': []}
        
    return value

def get_known_recipes():
    return [(j, i) for j in get_characters() for i in get_character_recipes(j)['recipes']]

@timed_cache_data(10 * 60)
def get_all_items():
    return [(j, i) for j in get_characters() for i in get_character_items(j)]

@timed_cache_data(24 * 60 * 60) # one hour
def get_build():
    print("Computing get build")
    return requester.perform_request(Uri.build)

@timed_cache_data(10 * 60)
def get_character_items(char_name, collasped=True):
    result = requester.perform_request(Uri.character_items, char_name)
    #pprint(result)
    results = []
    if result:
        for bag in result['bags']:
            if bag:
                for item in bag['inventory']:
                    if item:
                        if ('binding' in item.keys() and item['binding'] not in ['Account', 'AcountBound', 'NoSalvage', 'NoSell', 'AccountBindOnUse']):
                            results.append(item['id'])
                        else:
                            results.append(item['id'])
    return results

@timed_cache_data(10 * 60)
def get_account_materials():
    result = requester.perform_request(Uri.account_materials)
    results = []
    print("Account materials")
    for i in result:
        if i['count'] > 0:
            results.append(i['id'])
    return results

def write_or_load(path, value, init_value=0):
    if os.path.isfile(path):
        with open(path, 'r') as reader:
            return reader.read()
    else:
        with open(path, 'w') as writer:
            writer.write(str(value))
        return init_value

if __name__ == '__main__':
    # pprint(tester(12))
    # pprint(get_recipe_info(20))

    pprint(get_account_materials())
    
