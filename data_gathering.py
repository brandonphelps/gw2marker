
from secrets import key

from enum import Enum
import time
import requests
import re

from functools import lru_cache

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
        
    @RateLimited(10)
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

    def get_account(self):
        uri = "{}/{}/{}?access_token={}".format(self.base_url, self.version, 'account', key)
        return self._perform_request(uri)

    def _append_key(self, uri):
        return "{}?access_token={}".format(uri, key)

    def commerce(self, item_id=None):
        uri = "{}/{}/{}".format(self.base_url, self.version, 'commerce/listings')
        if item_id:
            uri = "{}/{}".format(uri, item_id)

        return self._perform_request(uri)

    def get_item_info(self, item_id):
        if type(item_id) == int:
            uri = "{}/{}/{}/{}".format(self.base_url, self.version, "items", item_id)
        else:
            return None
        return self._perform_request(uri)

    def get_recipe_info(self, item_id):
        uri = "{}/{}/{}/{}".format(self.base_url, self.version, "recipes", item_id)
        return self._perform_request(uri)

    def get_character_craftables(self):
        uri = "{}/{}/{}?access_token={}".format(self.base_url, self.version, 'account/recipes', key)
        return self._perform_request(uri)

    def get_character_craftable_info(self):
        craf_reipces = self.get_character_craftables()
        for i in craf_reipces:
            pprint(self.get_recipe_info(i))

requester = GW2Request('v2')


####### data caching

class NoSellsException(Exception):
    # No available sellers
    pass
    
class NoBuyException(Exception):
    # No available buyers
    pass


def get_item_info(item_id):
    item_info = requester.perform_request(Uri.items, item_id)
    return item_info

@lru_cache(maxsize=10)
def get_recipe_ids():
    recipe_ids = requester.perform_request(Uri.recipes)
    return recipe_ids

def get_recipe_info(recipe_id):
    recipe_info = requester.perform_request(Uri.recipes, recipe_id)
    return recipe_info

def get_recipe_max_buy_price(recipe_id):
    recipe_info = get_recipe_info(recipe_id)
    return get_item_max_buy_price(recipe_info['output_item_id'])

def get_item_max_buy_price(item_id):
    item_info = requester.perform_request(Uri.commerce_listings, item_id)
    if item_info is None:
        print("Failed to get item info for id: {}".format(item_id))

    if item_info and item_info['buys']:
        return max(item_info['buys'], key=lambda x: int(x['unit_price']))['unit_price']
    else:
        return 0

def get_item_min_sell_price(item_id):
    item_info = requester.perform_request(Uri.commerce_listings, item_id)
    if item_info is None:
        return 100000000
    if item_info and item_info['sells']:
        return min(item_info['sells'], key=lambda x: int(x['unit_price']))['unit_price']
    else:
        # todo add exception handling
        return 100000000

def get_characters(char=None):
    if char:
        return requester.perform_request(Uri.characters, char)
    else:
        return requester.perform_request(Uri.characters)

def get_character_crafting(char_name):
    return requester.perform_request(Uri.character_crafting, char_name)

def get_character_recipes(char_name):
    return requester.perform_request(Uri.character_recipes, char_name)

def get_known_recipes():
    return [(j, i) for j in get_characters() for i in get_character_recipes(j)['recipes']]
