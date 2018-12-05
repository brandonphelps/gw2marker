
from data_gathering import get_known_recipes, get_item_info, get_recipe_info, get_item_max_buy_price, get_item_min_sell_price, get_all_items, get_account_materials, get_items, get_item_id_by_name, get_recipe_ids, get_account_item_count, get_recipes
from data_models import LoadedRecipe, get_item_recipe, ItemTree, get_recipe_min_make_price, test_function
from graph_visitor import ItemTreeVisitor, LoadedRecipeVisitor, MinCostVisitor

from pprint import pprint
import subprocess

item_max_buy_table = {}

item_name_max_buy_table = {}

class MaxBuySubRep:
    def __init__(self, recipe_id):
        self.recipe_id = recipe_id
        self.info = {}
        self.sell_price = 0

    def add_to_max_table(self, item_id):
        if name not in item_name_max_buy_table.keys():
            item_price = get_item_max_buy_price(item_id)
            item_name_max_buy_table[name] = {'buy_price' : item_price,
                                             'count' : 1,
                                             'id' : item_id}
        else:
            print("Already have: {}".format(name))

    def output_item_name(self):
        s = LoadedRecipe(self.recipe_id)
        item_info = get_item_info(s.output_id)
        return item_info['name']

    def __repr__(self):
        return self.output_item_name()

    def find_max(self, recipe):
        # global max table of item names to prices
        recipe_item_info_name = get_item_info(recipe.output_id)['name']
        recipe_buy_price = get_item_max_buy_price(recipe.output_id)
        tmp = 0
        ing = []
        for j in recipe.input_info:
            if type(j['value']) == LoadedRecipe:
                ing_price, tmp_ing = self.find_max(j['value'])
                ing.extend(tmp_ing)
                tmp += j['count'] * ing_price
            else:
                ing.append(j)
                tmp += j['count'] * get_item_max_buy_price(j['value'])
        if tmp > recipe_buy_price:
            return tmp, ing
        else:
            return recipe_buy_price, [{'value' : recipe, 'count' : 1}]

    def update_info(self):
        recipe = LoadedRecipe(self.recipe_id)
        self.sell_price, self.info = self.find_max(recipe)


class WhatDoResult:
    def __init__(self, what_do, with_item):
        self.what_do = what_do
        self.result_item = with_item
        self.owner = ""

    def __str__(self):
        return "{}".format(self.what_do)

    def __repr__(self):
        return str(self)

def update_what_do_table(max_rep, ingredient_item, what_do_table, what_do='Sell'):
    if type(ingredient_item['value']) == LoadedRecipe:
        output_item_info = get_item_info(ingredient_item['value'].output_id)

        if output_item_info['name'] not in what_do_table.keys():
            wdr = WhatDoResult(what_do, max_rep.output_item_name())
            what_do_table[output_item_info['name']] = wdr
            parent_table[output_item_info['name']] = max_rep.output_item_name()
            for sub_ing in ingredient_item['value'].input_info:
                update_what_do_table(max_rep, sub_ing, what_do_table, 'Make {}'.format(output_item_info['name']))
        else:
            if max_recipes[parent_table[output_item_info['name']]].sell_price < max_rep.sell_price: # the parent of
                parent_table[output_item_info['name']] = max_rep.output_item_name()
                what_do_table[output_item_info['name']].what_do = 'Make {}'.format(max_rep.output_item_name())

    else:
        item_info = get_item_info(ingredient_item['value'])
        if item_info['name'] not in what_do_table.keys():
            wdr = WhatDoResult(what_do, item_info['name'])
            what_do_table[item_info['name']] = wdr
            parent_table[item_info['name']] = max_rep.output_item_name()

def test_main():
    checked_recipes = []
    used_mats = [get_item_id_by_name("Damask Patch"), get_item_id_by_name("Pile of Crystalline Dust"), get_item_id_by_name("Bag of Starch")
    ]

    for charac, recipe_num in get_known_recipes():
        if recipe_num not in checked_recipes:
            l = LoadedRecipe(recipe_num)
            if not l.uses_mat(used_mats):
                m = MaxBuySubRep(recipe_num)
                m.owner = charac
                m.update_info()
                if m.output_item_name in max_recipes.keys():
                    print("Found a duplicate")
                else:
                    max_recipes[m.output_item_name()] = m

    what_do_table = {}

    for max_rep_name in max_recipes.keys():
        max_rep = max_recipes[max_rep_name]
        for i in max_rep.info:
            update_what_do_table(max_rep, i, what_do_table)

    pprint(what_do_table)

def recipe_maker(item_name, count=1):
    return [LoadedRecipe(get_item_recipe(get_item_id_by_name(item_name))[0]) for i in range(count)]

def build_display():
    k = LoadedRecipeVisitor()
    # k.gendot(recipe_maker("Yassith's Pauldrons") + recipe_maker("Forgemaster's Visor") + recipe_maker("Forgemaster's Warfists"))
    # k.gendot(recipe_maker("20 Slot Craftsman's Bag") + recipe_maker("Zintl Visor")+recipe_maker("Zintl Pauldrons") + recipe_maker("Zintl Greaves"))
    k.gendot(recipe_maker("Yassith's Visor") + recipe_maker("Yassith's Pauldrons"))
    
def price_display(recipe):
    if isinstance(recipe, LoadedRecipe):
        print("Name: {}".format(get_item_info(recipe.output_id)['name']))
        print("Sell Price: {}".format(get_item_max_buy_price(recipe.output_id)))
        print("Buy Price: {}".format(get_item_min_sell_price(recipe.output_id)))
        for input in recipe.input_info:
            price_display(input['value'])
    else:
        print("Name: {}".format(get_item_info(recipe)['name']))
        print("Sell Price: {}".format(get_item_max_buy_price(recipe)))
        print("Buy Price: {}".format(get_item_min_sell_price(recipe)))

def new_main():
    used_item_ids = [get_item_id_by_name("Barbed Thorn")]
    
    excluded_items = [get_item_id_by_name("Iron Ore")]

    print("Id: ", used_item_ids)
    print("Buy: ", get_item_max_buy_price(used_item_ids[0]))

    seen_recipe_id = []

    max_profit = 0

    for i in get_known_recipes():
        l = LoadedRecipe(i[1])
        if i[1] not in seen_recipe_id and l.uses_mat(used_item_ids):
            print("RECIPE: {}".format(l))
            seen_recipe_id.append(i[1])
            output_item_name = get_item_info(l.output_id)['name']
            # v = MinCostVisitor()
            # v.gendot(l, output_item_name)
            actions = {}
            cost = get_recipe_min_make_price(l, actions, get_account_item_count(None))
            gain = get_item_max_buy_price(l.output_id)
            list_fee = .05 * cost
            transaction_fee = .10 * cost
            profit = gain - (cost + list_fee + transaction_fee)
            if profit > 0:
                # price_display(l)
                # item_counts = get_account_item_count(None)
                print("Cost: {}".format(cost))
                print("Gain: {}".format(gain))
                print("Listing fee: {}".format(list_fee))
                print("Transation fee: {}".format(transaction_fee))
                print("Profit: {}".format(profit))
                new_actions = {} 
                ratio_s = get_recipe_min_make_price(l, new_actions, get_account_item_count(None))
                if ratio_s == 0:
                    ratio_s = 1
                print("Profit: Ratio {}".format(profit / ratio_s))
                pprint(actions)

def leather_working():
    pass

def value_of_recipe(loaded_rep, print_t=False):
    rep_output_value = get_item_max_buy_price(loaded_rep.output_id)
    input_items_output_value = 0
    for i in loaded_rep.input_info:
        if type(i['value']) == LoadedRecipe:
            input_value_id = i['value'].output_id
        else:
            input_value_id = i['value']
        if print_t:
            print("Input: {} {} {}".format(get_item_info(input_value_id)['name'], i['count'], get_item_max_buy_price(input_value_id)))
        input_items_output_value += i['count'] * get_item_max_buy_price(input_value_id)
    return rep_output_value, input_items_output_value

def max_rep(recipe_id):
    pass


if __name__ == "__main__":
    parent_table = {}
    max_recipes = {}

    # table = {}
    # main()
    # test_main()
    # new_main()
    # build_display()

    max_diff = 0

    for rep_id in get_recipes():# get_known_recipes():
        l = LoadedRecipe(rep_id)
        output_v, input_v = value_of_recipe(l, False)
        #
        if output_v > input_v and max_diff < (output_v - input_v):
            print("{} {}: {} {}".format(l, '', output_v, input_v))
            max_diff = (output_v - input_v)
            value_of_recipe(l, True)


    
    
