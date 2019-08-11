"""
Main for outfitting ones characters, 
made for looking at the list of equipment an account has and determine what is missing or best fit for a specific character.
"""
import math
import itertools
import sys
from pprint import pprint

from data_gathering import get_all_account_items, get_item_info
from data_gathering import get_item_stats, get_item_stat_ids
from data_gathering import get_account_equipable_items

def equipment_score(item_info: dict, weights):
	"""
	item_info, dict: should be obtained from get_item_info function
	"""
	if 'infix_upgrade' in item_info['details']:
		item_attributes = item_info['details']['infix_upgrade']['attributes']

	else:
		item_attributes = {}

	score = 0
	for attrib in item_attributes:
		weight = 0
		if attrib['attribute'] in weights:
			weight = weights[attrib['attribute']]
		else:
			weight = 0
		score += attrib['modifier'] * weight
	return score
	
def get_account_trinket_filter(slot_type, toon_name=None):
	"""
	slot_type, str: 
	Accessory – Accessory
    Amulet – Amulet
    Ring – Ring
	"""
	for toon_name, item_info in get_account_equipable_items(toon_name):
		if (item_info['type'] == 'Trinket' and
		    item_info['details']['type'] == slot_type):
			yield (toon_name, item_info)

def get_account_armor_filter(slot_type, weight_class, toon_name=None):
	"""
	slot_type, str: type to filter on for armor. 
	slot_type values are: 
	Boots – Feet slot
    Coat – Chest slot
    Gloves – Hands slot
    Helm – Helm slot
    HelmAquatic – Breathing apparatus slot
    Leggings – Legs slot
    Shoulders – Shoulders slot

	weight_class, str: type to filter on for armor. 
	Heavy – Heavy armor
    Medium – Medium armor
    Light – Light armor
    Clothing – Town clothing
	"""

	# binding_filter, don't exclude anything
	for toon_name, item_info in get_account_equipable_items(toon_name):
		if (item_info['type'] == 'Armor' and
		    item_info['details']['type'] == slot_type and
		    item_info['details']['weight_class'] == weight_class):
			yield (toon_name, item_info)

def get_account_weapon_filter(type, toon_name=None):
	"""
	type, str:
	One-handed main hand: Axe, Dagger, Mace, Pistol, Scepter, Sword
    One-handed off hand: Focus, Shield, Torch, Warhorn
    Two-handed: Greatsword, Hammer, LongBow, Rifle, ShortBow, Staff
    Aquatic: Harpoon, Speargun, Trident
    Other: LargeBundle, SmallBundle, Toy, ToyTwoHanded
	"""
	for toon_name, item_info in get_account_equipable_items(soulbound=toon_name):
		if (item_info['type'] == 'Weapon' and
		    item_info['details']['type'] == type):
			yield (toon_name, item_info)

light_helm_armors = lambda toon_name: get_account_armor_filter('Helm', 'Light', toon_name)
light_coat_armors = lambda toon_name: get_account_armor_filter('Coat', 'Light', toon_name)
light_shoulders_armors = lambda toon_name: get_account_armor_filter('Shoulders', 'Light', toon_name)
light_gloves_armors = lambda toon_name: get_account_armor_filter('Gloves', 'Light', toon_name)
light_leggings_armors = lambda toon_name: get_account_armor_filter('Leggings', 'Light', toon_name)
light_boots_armors = lambda toon_name: get_account_armor_filter('Boots', 'Light', toon_name)
ring_armors = lambda toon_name: get_account_trinket_filter('Ring', toon_name)
amulet_armors = lambda toon_name: get_account_trinket_filter('Amulet', toon_name)
accessory_armors = lambda toon_name: get_account_trinket_filter('Accessory', toon_name)
axe_weapons = lambda toon_name: get_account_weapon_filter('Axe', toon_name)
sword_weapons = lambda toon_name: get_account_weapon_filter('Sword', toon_name)
dagger_weapons = lambda toon_name: get_account_weapon_filter('Dagger', toon_name)

def get_best_equipment_for(char_name, filter_func, attribute_weights, count):

	item_list_with_score = [(toon_name, item_info, equipment_score(item_info, attribute_weights)) for toon_name, item_info in filter_func(char_name)]
	
	for count, toon_item_info_score in zip(range(count), sorted(item_list_with_score, key=lambda x: x[2], reverse=True)):
		yield toon_item_info_score

def get_best_equipment():
	attribute_weights = {'Power': 0.3,
	                     'Precision': 0.165,
	                     'Healing': 0.3,
	                     'ConditionDamage': 0.165}
	char_name = 'Hydra Of Stone'


	for category, filter, count in [('Helm', light_helm_armors, 1),
	                                ('Shoulders', light_shoulders_armors, 1),
	                                ('Coat', light_coat_armors, 1),
	                                ('Gloves', light_gloves_armors, 1),
	                                ('Leggings', light_leggings_armors, 1),
	                                ('Boots', light_boots_armors, 1),
	                                ('Ring', ring_armors, 2),
	                                ('Accessory', accessory_armors, 2),
	                                ('Amulet', amulet_armors, 1),
	                                ('Sword', sword_weapons, 1),
	                                ('Dagger', dagger_weapons, 2)]:

		for toon_name, item_info, score in get_best_equipment_for(char_name, filter, attribute_weights, count):
			if item_info:
				print(f"{category}: {item_info['name']} {score}")
			else:
				print(f"{category}: {item_info}")

def main():
	get_best_equipment()


if __name__ == "__main__":
	main()
