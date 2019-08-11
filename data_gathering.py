
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
from collections import defaultdict
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
    account_inventory = ('account/inventory', True)
    items = ('items/{}', False, 1)
    item_stats = ('itemstats/{}', False, 1)
    item_stats_all = ('itemstats', False, 0)
    recipes = ('recipes/{}', False, 1)
    commerce_listings = ('commerce/listings/{}', False, 1)
    commerce_prices = ('commerce/prices/{}', False, 1)
    characters = ('characters/{}', True, 1)
    character_crafting = ('characters/{}/crafting', True, 1)
    character_recipes = ('characters/{}/recipes', True, 1)
    character_items = ('characters/{}/inventory', True, 1)
    character_equipment = ('characters/{}/equipment', True, 1)
    build = ('build', False)

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

        time.sleep(2.0)
        if option.optional_param_count != 0:
            if len(args) > 0:
                uri = uri.format(*args)
            else:
                uri = uri.replace('{', '').replace('}', '')
        if option.requires_auth:
            uri += "?access_token={}".format(key)
        print(uri)
        return self._perform_request(uri)

    def _perform_request(self, uri):
        r = requests.get(uri)
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
def get_items():
    """
    returns a list of item ids
    """
    return requester.perform_request(Uri.items)

@cache_data(None)
def get_item_info(item_id):
    item_info = requester.perform_request(Uri.items, item_id)
    return item_info

@cache_data(None)
def get_item_stat_ids():
	item_info = requester.perform_request(Uri.item_stats_all)
	return item_info

@cache_data(None)
def get_item_stats(stat_id):
	item_info = requester.perform_request(Uri.item_stats, stat_id)
	return item_info

def is_item_account_bound(item_id):
    item_info = get_item_info(item_id)
    return 'AccountBound' in item_info['flags']

@cache_data(None)
def get_item_id_by_name(item_name):
    for item_id in get_items():
        item_info = get_item_info(item_id)
        if item_info['name'] == item_name:
            return item_id
    return None


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
    return get_item_max_buy_price(recipe_info['output_item_id'])

time_cache_interval = 3 * 60 

@timed_cache_data(time_cache_interval)
def tp_buy_stock(item_id):
    r = requester.perform_request(Uri.commerce_listings, item_id)
    if r:
        return r['buys']
    else:
        return []

@timed_cache_data(time_cache_interval)
def tp_sell_stock(item_id):
    r = requester.perform_request(Uri.commerce_listings, item_id)
    if r:
        return r['sells']
    else:
        return []

@timed_cache_data(time_cache_interval)
def tp_instant_stock_info(item_id):
    item_info = requester.perform_request(Uri.commerce_listings, item_id)

    if item_info and item_info['buys']:
        return sorted(item_info['buys'], key=lambda x: x['unit_price'], reverse=True)
    else:
        return []

@timed_cache_data(time_cache_interval) 
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

@timed_cache_data(time_cache_interval)
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
        t = requester.perform_request(Uri.characters)
        print(t)
        return t

@timed_cache_data(time_cache_interval)
def get_character_crafting(char_name):
    return requester.perform_request(Uri.character_crafting, char_name)


@timed_cache_data(time_cache_interval)
def get_character_recipes(char_name):
    value = requester.perform_request(Uri.character_recipes, char_name) 
    if not value:
        value = {'recipes': []}    
    return value

def get_mystic_forge_recipes():
    return []

@timed_cache_data(time_cache_interval)
def get_known_recipes():
    recipes = []
    for j in get_characters():
        print(j)
        recipes.extend(get_character_recipes(j)['recipes'])
    return recipes

@timed_cache_data(time_cache_interval * 50)
def get_all_items(binding_filter):
	return [(j, i) for j in get_characters()
	        for i in get_character_items(j, binding_filter=binding_filter)]

def get_all_account_items(binding_filter=None):
	return get_all_items(binding_filter)

@timed_cache_data(time_cache_interval)
def get_build():
    return requester.perform_request(Uri.build)

@timed_cache_data(time_cache_interval)
def get_account_bank():
    return requester.perform_request(Uri.account_bank)

@timed_cache_data(time_cache_interval)
def get_raw_character_items(character_name):
    return requester.perform_request(Uri.character_items, character_name)

@timed_cache_data(time_cache_interval)
def get_raw_account_materials():
    return requester.perform_request(Uri.account_materials)

@timed_cache_data(time_cache_interval)
def get_recipes():
    return [(None, recipe_id) for recipe_id in requester.perform_request(Uri.recipes)]

def get_account_item_count(item_id):
    item_counts = defaultdict(int)
    for character in get_characters():
        inventory = get_raw_character_items(character)
        if inventory:
            for bag in inventory['bags']:
                if bag:
                    for item in bag['inventory']:
                        if item:
                            item_counts[item['id']] += item['count']

    for item in get_raw_account_materials():
        if item:
            item_counts[item['id']] += item['count']

    for item in get_account_bank():
        if item:
            item_counts[item['id']] += item['count']

    if item_id:
        return item_counts[item_id]
    else:
        return item_counts

@timed_cache_data(time_cache_interval)
def get_character_items(char_name, collasped=True, binding_filter=None):
	if binding_filter is None:
		binding_filter = ['Account', 'AccountBound', 'NoSalavage', 'NoSell', 'AccountBindOnUse']
	result = requester.perform_request(Uri.character_items, char_name)
	results = []
	if result:
		for bag in result['bags']:
			if bag:
				for item in bag['inventory']:
					if item:
						if ('binding' in item.keys() and item['binding'] not in binding_filter):
							results.append(item['id'])
						else:
							results.append(item['id'])

	result = requester.perform_request(Uri.character_equipment, char_name)
	if result:
		for item in result['equipment']:
			print(char_name, get_item_info(item['id'])['name'])
			results.append(item['id'])

	return results


def get_account_equipable_items(soulbound=None):
	return [(j, i) for j in get_characters()
	        for i in get_equipable_items_with_stats(j, soulbound=soulbound)]

@timed_cache_data(time_cache_interval * 30)
def get_equipable_items_with_stats(char_name, soulbound=None):
	results = []

	def is_item_equipable(item_id):
		item_info = get_item_info(item_id)
		return item_info and (item_info['type'] == 'Armor' or
		                      item_info['type'] == 'Back' or
		                      item_info['type'] == 'Weapon' or
		                      item_info['type'] == 'Trinket')
	
	def get_result_from_item_info(item_info):
		new_item_info = get_item_info(item_info['id'])
		if 'stats' in item_info:
			print("Adding user selected stats")
			# making it look like the get_item_info data
			attribs = []
			for attrib in item_info['stats']['attributes']:
				attribs.append({'attribute': attrib,
				                'modifier' : item_info['stats']['attributes'][attrib]})
			new_item_info['details']['infix_upgrade'] = {'attributes': attribs}
		return new_item_info

	result = requester.perform_request(Uri.character_items, char_name)
	results = []
	if result:
		for bag in result['bags']:
			if bag:
				for item in bag['inventory']:
					if item and is_item_equipable(item['id']):
						if 'binding' in item and item['binding'] == 'Character':
							if item['bound_to'] == soulbound:
								results.append(get_result_from_item_info(item))
							else:
								# don't add item since its soulbound to another character
								pass
						else:
							results.append(get_result_from_item_info(item))

	result = requester.perform_request(Uri.character_equipment, char_name)
	if result:
		for item in result['equipment']:
			if is_item_equipable(item['id']):
				if 'binding' in item and item['binding'] == 'Character':
					if item['bound_to'] == soulbound:
						print(repr(char_name))
						results.append(get_result_from_item_info(item))
					else:
						# don't add item since its soulbaound to another character
						pass
				else:
					results.append(get_result_from_item_info(item))

	return results

@timed_cache_data(time_cache_interval)
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

	# pprint(get_account_materials())
	pprint(get_equipable_items_with_stats('Hydra Of Stone'))
    
