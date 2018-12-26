from data_gathering import get_recipe_info, get_item_max_buy_price, get_item_min_sell_price, get_item_info, get_recipe_ids, timed_cache_data, get_recipe_max_buy_price
from data_gathering import cache_data, build_conditional, tp_buy_stock, tp_sell_stock
from graphviz import Digraph

from pprint import pprint
import os
import json
from collections import defaultdict
from itertools import permutations
from enum import Enum

# @timed_cache_data(10  * 60 * 60)
@cache_data(build_conditional)
def get_item_recipe(item_id, use_known=False):
    item_info = get_item_info(item_id)
    for i in get_recipe_ids():
        recipe_info = get_recipe_info(i)
        if recipe_info['output_item_id'] == item_id:
            # found recipe thus return it
            return (i, 'recipe')
    else:
        # no recipe to make the item, thus return the item
        return (item_id, 'item')

def get_recipe_from_item_id(item_id, use_known=False):
    s = get_item_recipe(item_id, use_known)
    if s[1] == 'recipe':
        return s[0]
    else:
        return None

class Item():
    def __init__(self, item_id):
        self._item_id = item_id
        self.name = None
        self.vendor_value = None
        self._load_data()

    def get_id(self):
        return self._item_id

    def _load_data(self):
        """
        uses item id to requery server for item info 
        """
        t = get_item_info(self._item_id)
        self.name = t['name']
        self.vendor_value = t['vendor_value']
        
    def __repr__(self):
        return "Item({})".format(self._item_id)

    def __str__(self):
        return "Item({})\n\t{}".format(self._item_id, self.name)

class LoadedRecipe():
    def __init__(self, id):
        self.recipe_id = id
        recipe_info = get_recipe_info(self.recipe_id)
        self.output_id = recipe_info['output_item_id']
        self.input_info = []
        self.output_item_count = recipe_info['output_item_count']

        for ing in recipe_info['ingredients']:
            id_value, id_type = get_item_recipe(ing['item_id'])
            if id_type == "recipe":
                self.input_info.append({'count' : ing['count'],
                                        'value' : LoadedRecipe(id_value)})
            elif id_type == "item":
                self.input_info.append({'count' : ing['count'],
                                        'value' : id_value})
            else:
                print("What did you give me?")

    def __str__(self):
        output_item_info = get_item_info(self.output_id)
        return "LoadedRecipe: {}".format(str(output_item_info['name']))

    def __repr__(self):
        return str(self)

    def immediate_use_mat(self, item_ids):
        for i in self.input_info:
            if type(i['value']) == LoadedRecipe:
                if i['value'].output_id in item_ids:
                    return True
            else:
                if i['value'] in item_ids:
                    return True
        else:
            return False



    def uses_mat(self, item_ids):
        for i in self.input_info:
            if type(i['value']) == LoadedRecipe:
                if i['value'].output_id in item_ids:
                    return True
                if i['value'].uses_mat(item_ids):
                    return True
            else:
                if i['value'] in item_ids:
                    return True
        else:
            return False

    def immediate_mat_list(self):
        for i in self.input_info:
            if type(i['value']) == LoadedRecipe:
                yield i['value'].output_id
            else:
                yield i['value']

    def all_item_ids(self):
        yield self.output_id
        for i in self.input_info:
            if type(i['value']) == LoadedRecipe:
                for j in i['value'].all_item_ids():
                    yield j
            else:
                yield i['value']

    def all_ids(self):
        yield self.recipe_id
        for i in self.input_info:
            if type(i['value']) == LoadedRecipe:
                for j in i['value'].all_ids():
                    yield j
            else:
                yield i['value']

class TPItemStock:
    def __init__(self, item_id, dir='buy'):
        self._item_id = item_id
        self._item_info = get_item_info(self._item_id)
        self._dir = dir

        if dir == 'buy':
            self.items_holder = tp_buy_stock(self._item_id)
        else:
            self.items_holder = tp_sell_stock(self._item_id)
        self.items_holder.sort(key=lambda x: x['unit_price'], reverse = dir == 'buy')
        self._supply = 0
        for i in self.items_holder:
            self._supply += i['quantity']

    def consume(self, amount):
        consume_amount = min(self.supply(), amount)
        while consume_amount > 0 and self._supply > 0:
            self.items_holder[0]['quantity'] -= 1
            self._supply -= 1
            if self.items_holder[0]['quantity'] == 0:
                self.items_holder.pop(0)
            consume_amount -= 1

    def supply(self):
        return self._supply

    def current_price(self, peek=0):
        if self.items_holder:

            index = 0
            if peek < 0:
                peek = 0

            while peek >= 0 and index < len(self.items_holder):
                if peek > self.items_holder[index]['quantity']:
                    peek -= self.items_holder[index]['quantity']
                    index += 1
                else:
                    return self.items_holder[index]['unit_price']
            if self._dir == 'buy':
                return 0
            else:
                return 100000000
        else:
            if self._dir == 'buy':
                return 0
            else:
                return 1000000000

    def current_amount_left(self):
        return self.items_holder[0]['quantity']

    def __str__(self):
        return "{}: {} {}".format(self._item_info['name'], self._dir, self.items_holder[0]['unit_price'])



def build_dep_graph(parent, dep_id_graph, parent_ids, recipe_id_map):
    children = parent.input_info
    parent_ids.append(str(parent.recipe_id))
    recipe_id_map[str(parent.recipe_id)] = parent
    for i in children:
        if type(i['value']) == LoadedRecipe:
            dep_id_graph[str(parent.recipe_id)][str(i['value'].recipe_id)] = True
            build_dep_graph(i['value'], dep_id_graph, parent_ids, recipe_id_map)
        else:
            dep_id_graph[str(parent.recipe_id)][str(i['value'])] = True



def get_recipe_min_make_price(recipe, actions, material_counts=None):
    t = 0

    for i in recipe.input_info:
        if type(i['value']) == LoadedRecipe:
            item_id = i['value'].output_id
        else:
            item_id = i['value']

        item_info = get_item_info(item_id)
        if material_counts:
            have_amount = material_counts[item_id]
            if i['count'] <= have_amount:
                material_counts[item_id] -= i['count']
                need_amount = 0
            else:
                need_amount = i['count'] - have_amount
        else:
            need_amount = i['count']

        if type(i['value']) == LoadedRecipe:
            if need_amount == 0:
                actions[item_info['name']] = 'Craft'
            else:
                recipe_make_price = need_amount * get_recipe_min_make_price(i['value'], actions, material_counts)
                sell_price = need_amount * get_item_min_sell_price(item_id)
                if recipe_make_price < sell_price:
                    actions[item_info['name']] = 'Craft'
                else:
                    actions[item_info['name']] = 'Buy'
                    for sub_item in i['value'].input_info:
                        if type(sub_item['value']) == LoadedRecipe:
                            name = get_item_info(sub_item['value'].output_id)['name']
                        else:
                            name = get_item_info(sub_item['value'])['name']
                        del actions[name]

                t += min(recipe_make_price, sell_price)
        else:
            if need_amount != 0:
                actions[item_info['name']] = 'Buy'
                tmp = need_amount * get_item_min_sell_price(item_id)
            else:
                tmp = 0
            t += tmp
    return t


def test_function(recipe):
    t = 0
    for i in recipe.input_info:
        if type(i['value']) == LoadedRecipe:
            t += test_function(i['value'])
        else:
            t += get_item_min_sell_price(i['value'])
    return t

def find_max(recipe):
    parent_buy_price = get_item_max_buy_price(recipe.output_id)
    tmp = 0
    ing = []
    for j in recipe.input_info:
        if type(j['value']) == LoadedRecipe:
            ing_price, tmp_ing = find_max(j['value'])
            ing.extend(tmp_ing)
            j['coinage'] = j['count'] * ing_price
            tmp += j['count'] * ing_price
        else:
            ing.append(j)
            j['coinage'] = j['count'] * get_item_max_buy_price(j['value'])
            tmp += j['count'] * get_item_max_buy_price(j['value'])
    if tmp > parent_buy_price:
        return tmp, ing
    else:
        return parent_buy_price, [{'value' : recipe, 'count' : 1, 'coinage' : parent_buy_price}]

def find_sub_max(recipe):
    parent_buy_price = get_item_max_buy_price(recipe.output_id)
    tmp = 0
    ing = []
    for j in recipe.input_info:
        if type(j['value']) == LoadedRecipe:
            ing_price, tmp_ing = find_sub_max(j['value'])
            ing.extend(tmp_ing)
            tmp += j['count'] * ing_price
        else:
            ing.append(j)
            j['value'] = j['count'] * get_item_max_buy_price(j['value'])
            tmp += j['count'] * get_item_max_buy_price(j['value'])
    if tmp > parent_buy_price:
        return tmp, ing
    else:
        return parent_buy_price, [recipe]

def find_min(recipe):
    parent_sell_price = get_item_min_sell_price(recipe.output_id)
    tmp = 0
    ing = []
    for j in recipe.input_info:
        if type(j['value']) == LoadedRecipe:
            ing_price, tmp_ing = find_min(j['value'])
            ing.extend(tmp_ing)
            tmp += j['count'] * ing_price
        else:
            ing.append(j)
            tmp += j['count'] * get_item_min_sell_price(j['value'])

    if tmp < parent_sell_price:
        return tmp, ing
    else:
        return parent_sell_price, [recipe]

def graph_recipe(recipe, dot, values=None):
    item_info = get_item_info(recipe.output_id)
    for j in recipe.input_info:
        if type(j['value']) == LoadedRecipe:
            j_i_info = get_item_info(j['value'].output_id)
            dot.edge(item_info['name'], j_i_info['name'], label=str(j['count']))
            if values:
                if values == Dir.Buy:
                    buy_price = get_item_max_buy_price(j['value'].output_id)
                elif values == Dir.Sell:
                    buy_price = get_item_min_sell_price(j['value'].output_id)
                dot.node(item_info['name'], label="{}: {}".format(item_info['name'], buy_price))
            graph_recipe(j['value'], dot)
        else:
            j_i_info = get_item_info(j['value'])
            dot.edge(item_info['name'], j_i_info['name'], label=str(j['count']))
            if values:
                if values == Dir.Buy:
                    buy_price = get_item_max_buy_price(item_info['id'])
                    j_i_buy_price = get_item_max_buy_price(j_i_info['id'])
                elif values == Dir.Sell:
                    buy_price = get_item_min_sell_price(item_info['id'])
                    j_i_buy_price = get_item_min_sell_price(j_i_info['id'])

                dot.node(item_info['name'], label="{}: {}".format(item_info['name'], buy_price))
                dot.node(j_i_info['name'], label="{}: ({}x) {}".format(j_i_info['name'], j['count'], j['count'] * j_i_buy_price))
                    

class Dir(Enum):
    Buy = 1
    Sell = 2

def create_table(recipe_id, table):
    recipe_info = get_recipe_info(recipe_id)
    recipe_item_info = get_item_info(recipe_info['output_item_id'])
    l = LoadedRecipe(recipe_id)
    k = find_max(l)
    for i in k[1]:
        if type(i['value']) == LoadedRecipe:
            meta_i = i
            i = i['value']
            item_info = get_item_info(i.output_id)
            if item_info['name'] in table.keys():
                pass
            else:
                table[item_info['name']] = {'action' : 'Sell',
                                            'count' : meta_i['count'],
                                            'value' : meta_i['coinage']}
                for j in i.input_info:
                    if type(j['value']) == LoadedRecipe:
                        item_info_id = j['value'].output_id
                    else:
                        item_info_id = j['value']
                    ing_item_info = get_item_info(item_info_id)
                    if ing_item_info['name'] in table.keys():
                        prev_vablue = table[ing_item_info['name']]
                        if prev_vablue['action'] == 'Sell':
                            table[ing_item_info['name']] = {'action': 'Material/Buy',
                                                            'parent': recipe_item_info['name'],
                                                            'value': j['coinage'],
                                                            'count': j['count']}
                        else:
                            pass
                    else:
                        table[ing_item_info['name']] = {'action': 'Material/Buy',
                                                        'parent': recipe_item_info['name'],
                                                        'value': j['coinage'],
                                                        'count': j['count']}
        else:
            item_info = get_item_info(i['value'])
            if item_info['name'] in table.keys():
                pass
            else:
                table[item_info['name']] = {'action': 'Sell',
                                            'parent' : recipe_item_info['name'],
                                            'value' : i['coinage'],
                                            'count' : i['count']}


