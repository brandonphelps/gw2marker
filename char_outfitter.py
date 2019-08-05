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
	print(item_info['name'], item_info)
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

def attribute_manhat_dist(attribute1, attribute2, weights=None):
	attribute_one_data = {}
	attribute_two_data = {}
	if weights is None:
		weights = {}

	for attr in attribute1:
		assert attr['attribute'] not in attribute_one_data
		attribute_one_data[attr['attribute']] = attr

	for attr in attribute2:
		assert attr['attribute'] not in attribute_two_data
		attribute_two_data[attr['attribute']] = attr

	value = 0
	for key in set(list(attribute_one_data.keys()) + list(attribute_two_data.keys())):
		l_m_value, l_v_value = 0, 0
		r_m_value, r_v_value = 0, 0

		if key in attribute_one_data:
			l_m_value, l_v_value = attribute_one_data[key]['multiplier'], attribute_one_data[key]['value']
		if key in attribute_two_data:
			r_m_value, r_v_value = attribute_two_data[key]['multiplier'], attribute_two_data[key]['value']

		value += math.fabs(l_m_value - r_m_value) + math.fabs(l_v_value - r_v_value)

	return value
	
def get_account_armor_filter(slot_type, weight_class):
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
	for toon_name, item_info in get_account_equipable_items(binding_filter=[]):
		if (item_info['type'] == 'Armor' and
		    item_info['details']['type'] == slot_type and
		    item_info['details']['weight_class'] == weight_class):
			yield (toon_name, item_info)

light_helm_armors = get_account_armor_filter('Helm', 'Light')
light_coat_armors = get_account_armor_filter('Coat', 'Light')
light_shoulders_armors = get_account_armor_filter('Shoulders', 'Light')
light_gloves_armors = get_account_armor_filter('Gloves', 'Light')
light_leggings_armors = get_account_armor_filter('Leggins', 'Light')
light_boots_armors = get_account_armor_filter('Boots', 'Light')

light_armors = itertools.chain(light_helm_armors, light_coat_armors, light_shoulders_armors, light_gloves_armors, light_leggings_armors, light_boots_armors)

def get_best_equipment_for(slot, attribute_weights, filter_func):
	best_item = None
	best_score = 0
	print(slot)
	for toon_name, item_info in filter_func:
		item_score = equipment_score(item_info, attribute_weights)
		print("\t", item_info['name'], item_score)
		if item_score > best_score:
			best_item = item_info
			best_score = item_score
	return best_item, best_score

def get_best_equipment():
	attribute_weights = {'Power': 0.3,
	                     'Precision': 0.165,
	                     'Healing': 0.3,
	                     'ConditionDamage': 0.165}

	for category, filter in [('Helm', light_helm_armors),
	                         ('Shoulders', light_shoulders_armors),
	                         ('Coat', light_coat_armors),
	                         ('Gloves', light_gloves_armors),
	                         ('Leggins', light_leggings_armors),
	                         ('Boots', light_boots_armors)]:
		item_info, best_equipement = get_best_equipment_for(category, attribute_weights, filter)
		if item_info:
			print(f"{category}: {item_info['name']} {best_equipement}")
		else:
			print(f"{category}: {item_info} {best_equipement}")

def main():
	get_best_equipment()


if __name__ == "__main__":
	main()
