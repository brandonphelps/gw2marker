
from data_gathering import get_known_recipes, get_item_info, get_recipe_info, get_item_max_buy_price, get_item_min_sell_price, get_all_items, get_account_materials
from data_models import LoadedRecipe, get_item_recipe

from pprint import pprint

from tqdm import tqdm

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
        # ing_item_info = get_item_info(ingredient_item['value'])

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
    used_mats = [19697]

    for charac, recipe_num in tqdm(get_known_recipes(), desc="Recipes"):
        if recipe_num not in checked_recipes:
            l = LoadedRecipe(recipe_num)
            if True or l.uses_mat(used_mats):
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

if __name__ == "__main__":
    parent_table = {}
    max_recipes = {}

    # table = {}
    # main()
    test_main()
