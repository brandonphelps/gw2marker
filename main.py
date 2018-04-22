
from data_gathering import get_known_recipes, get_item_info, get_recipe_info, get_item_max_buy_price, get_item_min_sell_price, get_all_items, get_account_materials
from data_models import LoadedRecipe, get_item_recipe

from pprint import pprint

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

def update_table_sub_recip(recip, parent_recipe, table):
    recipe_item_info = get_item_info(recip.output_id)
    if recipe_item_info['name'] in item_max_buy_table.keys():
        current_parent_buy_price = item_max_buy_table[recipe_item_info['name']]['buy_price']
    else:
        current_parent_buy_price = 0
        

def update_sell(recipe, parent_recipe_info, table):
    recipe_output_info = get_item_info(recipe.output_id)
    for sub_ing in recipe.input_info:
        if type(sub_ing['value']) == LoadedRecipe:
            item_info = get_item_info(sub_ing['value'].output_id)
            if item_info['name'] in table.keys():
                item_entry = table[item_info['name']]
                if recipe_output_info['name'] not in item_entry['parent']:
                    item_entry['parent'].append(recipe_output_info['name'])
            else:
                table[item_info['name']] = {'action' : 'material/buy',
                                            'parent' : [recipe_output_info['name']],
                                            'count' : sub_ing['count']}
            update_sell(sub_ing['value'], parent_recipe_info, table)
        else:
            item_info = get_item_info(sub_ing['value'])
            if item_info['name'] in table.keys():
                item_entry = table[item_info['name']]
                if recipe_output_info['name'] not in item_entry['parent']:
                    item_entry['parent'].append(recipe_output_info['name'])
            else:
                table[item_info['name']] = {'action' : 'material/buy',
                                            'parent' : [recipe_output_info['name']],
                                            'count' : sub_ing['count']}

def create_table(recipe_id, table, max_table):
    recipe_info = get_recipe_info(recipe_id)
    recipe_item_info = get_item_info(recipe_info['output_item_id'])
    l = LoadedRecipe(recipe_id)
    max_ingre = find_max(l, item_max_buy_table)
    max_table[recipe_item_info['name']] = max_ingre
    for sub_ing in max_ingre[1]:
        if type(sub_ing['value']) == LoadedRecipe:
            sub_item_info = get_item_info(sub_ing['value'].output_id)
            if sub_ing['value'].recipe_id == recipe_id:
                table[sub_item_info['name']] = {'action': 'sell',
                                                'parent': [],
                                                'count': 1}
            else:
                if sub_item_info['name'] not in table.keys():
                    table[sub_item_info['name']] = {'action' : 'sell',
                                                    'parent' : [recipe_item_info['name']],
                                                    'count' : 1}
            update_sell(sub_ing['value'], recipe_item_info, table)
        else:
            item_info = get_item_info(sub_ing['value'])
            # todo, do we need to check if the item is already been marked for material/buy for another item? 
            if item_info['name'] not in table.keys():
                table[item_info['name']] = {'action' : 'sell',
                                            'parent' : [recipe_item_info['name']],
                                            'count' : sub_ing['count']}

def find_max(recipe, item_buy_table):
    recipe_buy_price = get_item_max_buy_price(recipe.output_id)
    if recipe_buy_price not in item_buy_table.keys():
        recipe_item_info_name = get_item_info(recipe.output_id)['name']
        item_buy_table[recipe_item_info_name] = {'buy_price' : recipe_buy_price,
                                                 'count' : 1,
                                                 'id' : recipe.output_id}
    else:
        print("Have already evaluated this recipe: {}".format(recipe.output_id))
    tmp = 0
    ing = []
    for j in recipe.input_info:
        if type(j['value']) == LoadedRecipe:
            ing_price, tmp_ing = find_max(j['value'], item_buy_table)
            ing.extend(tmp_ing)
            tmp += j['count'] * ing_price
        else:
            ing.append(j)
            tmp += j['count'] * get_item_max_buy_price(j['value'])
            item_info = get_item_info(j['value'])
            item_buy_table[item_info['name']] = {'buy_price' : get_item_max_buy_price(j['value']),
                                                 'count': j['count'],
                                                 'id' : j['value']}
    if tmp > recipe_buy_price:
        return tmp, ing
    else:
        return recipe_buy_price, [{'value' : recipe, 'count' : 1}]

def get_obj_id(value):
    if type(value) == LoadedRecipe:
        return value.output_id
    elif type(value) == dict:
        return value['value']
    elif type(value) == int:
        return value
    else:
        print("iunno what i got: {}".format(value))
        return None

def uses_mat(recipe, material_list, depth=1):
    if type(recipe) == int:
        recipe = LoadedRecipe(recipe)

    recipe_item_info = get_item_info(recipe.output_id)
    a = 1 #debuging
    return_val = True
    for i in recipe.input_info:
        if get_obj_id(i) in material_list:
            return True
        else:
            if type(i['value']) == LoadedRecipe:
                if uses_mat(i['value'], material_list, depth + 1):
                    return True
    else:
        return False


def item_in_vault(item_id):
    acc_mats = get_account_materials()
    if item_id in acc_mats:
        return True
    else:
        return False

def get_item_make_price(item_id, recipe_listing):
    recipe_id = get_item_recipe(item_id)
    if item_in_vault(item_id):
        return 0
    elif recipe_id[0] == item_id:
        return get_item_min_sell_price(item_id)
    else:
        recipe = LoadedRecipe(recipe_id[0])
        return recipe_min_cost(recipe, recipe_listing)

def have_parent_item(item_id, current_recipe_list):
    for i in current_recipe_list.keys():
        if uses_mat(get_item_recipe(i)[0], [item_id]):
            break # already have a recipe which contains this item
    else:
        # didn't find a recipe using this item
        return False
    return True

def recipe_min_cost(recipe, recipe_listing):
    cost = 0
    for j in recipe.input_info:
        recipe_list = []
        min_sell_price = get_item_min_sell_price(get_obj_id(j['value']))
        make_price = get_item_make_price(get_obj_id(j['value']), recipe_list)
        cost += j['count'] * min(min_sell_price, make_price)
        sub_item_info = get_item_info(get_obj_id(j['value']))
        if min_sell_price <= make_price:
            recipe_listing.append({'buy' : sub_item_info['name'], 'cost' : j['count'] * min_sell_price})
        else:
            recipe_listing.append({'make' : sub_item_info['name'], 'cost' : 0})
            recipe_listing.extend(recipe_list)
    return cost

def account_has_item(item_id):
    character_items = get_all_items()
    for char_name, item in character_items:
        if item == item_id:
            return True
    return False

def have_sell_item(name, list):
    for j in list:
        for k in j[1]:
            if 'make' in k.keys() and name == k['make']:
                return True
            elif 'buy' in k.keys() and name == k['buy']:
                return True
    return False

def main():
    checked_recipes = []
    max_table = {}
    for charac, recipe_num in get_known_recipes():
        if recipe_num not in checked_recipes:
            recipe = LoadedRecipe(recipe_num)
            #print("Checking recipe: {} {}".format(charac, recipe_num))
            if True or uses_mat(recipe, [19697]):
                checked_recipes.append(recipe_num)
                item_info = get_item_info(recipe.output_id)
                create_table(recipe_num, table, max_table)
    items_checked = []
    sell_items = []
    temp_sell_items = {} # a list of items to sell
    temp_sell_reciped_items = {} # a list of LoadedRecipes to sell
    mat_sells = []
    for i in max_table.keys():
        if len(max_table[i][1]) == 1:
            if type(max_table[i][1][0]['value']) == LoadedRecipe:
                item_info = get_item_info(max_table[i][1][0]['value'].output_id)
                if item_info['name'] == i:
                    ing_list = []
                    value = recipe_min_cost(max_table[i][1][0]['value'], ing_list)
                    if value < max_table[item_info['name']][0]:
                        sell_items.append((value, ing_list, max_table[item_info['name']][0], item_info['name']))
                        #print("Sell! {} : cost {} buy {}".format(item_info['name'], max_table[item_info['name']][0], value))
                        temp_sell_reciped_items[item_info['id']] = i
                        #print(value, ing_list)
        else:
            for item_ing in max_table[i][1]:
                if type(item_ing['value']) == LoadedRecipe:
                    item_info = get_item_info(item_ing['value'].output_id)
                    value = recipe_min_cost(item_ing['value'], ing_list)
                    if (not have_sell_item(item_info['name'], sell_items)) and item_info['name'] in max_table.keys() and value < max_table[item_info['name']][0]:
                        sell_items.append((value, ing_list, max_table[item_info['name']][0], item_info['name']))

                    temp_sell_reciped_items[item_info['id']] = i
                    for j in item_ing['value'].input_info:
                        if type(j['value']) == LoadedRecipe:
                            pass
                        else:
                            if j['value'] in temp_sell_items.keys():
                                mat_sells.append(temp_sell_items[j['value']])
                                del temp_sell_items[j['value']]
                else:
                    if not have_parent_item(item_ing['value'], temp_sell_reciped_items):
                        temp_sell_items[item_ing['value']] = i


    final_results = []

    for i in temp_sell_items:
        buy_price = 0
        item_info = get_item_info(i)
        if item_info['name'] in max_table.keys():
            buy_price = max_table[item_info['name']][0]
        else:
            buy_price = get_item_max_buy_price(i)
        final_results.append(('base', item_info['name'], buy_price))

    for i in temp_sell_reciped_items:
        buy_price = 0
        item_info = get_item_info(i)
        if item_info['name'] in max_table.keys():
            buy_price = max_table[item_info['name']][0]
        else:
            buy_price = get_item_max_buy_price(i)
        if item_info['name'] in max_table.keys():
            final_results.append(('craft', item_info['name'], max_table[item_info['name']][0]))
        else:
            print("Failed to find data on item: {}".format(item_info['name']))

    for i in sorted(final_results, key=lambda x: x[2]):
        if i[0] == 'base':
            print("Sell basic {} for {}".format(i[1], i[2]))
        else:
            print("Sell craft {} for {}".format(i[1], i[2]))
            print(max_table[i[1]])


    for i in mat_sells:
        print(i)



def update_what_do_table(max_rep, ingredient_item, what_do_table, what_do='Sell'):
    if type(ingredient_item['value']) == LoadedRecipe:
        output_item_info = get_item_info(ingredient_item['value'].output_id)

        if output_item_info['name'] not in what_do_table.keys():
            what_do_table[output_item_info['name']] = what_do
            parent_table[output_item_info['name']] = max_rep.output_item_name()
            for sub_ing in ingredient_item['value'].input_info:
                update_what_do_table(max_rep, sub_ing, what_do_table, 'Make {}'.format(output_item_info['name']))
        else:
            print("I've seen this recipe before what do i do? {}".format(output_item_info['name']))
            print("Current: {}".format(max_rep.output_item_name()))
            print("Parent: {}".format(parent_table[output_item_info['name']]))
            print("Buy Compare: {} {}".format(max_recipes[parent_table[output_item_info['name']]].sell_price, max_rep.sell_price))
            if max_recipes[parent_table[output_item_info['name']]].sell_price < max_rep.sell_price: # the parent of
                parent_table[output_item_info['name']] = max_rep.output_item_name()
                what_do_table[output_item_info['name']] = 'Make {}'.format(max_rep.output_item_name())

    else:
        item_info = get_item_info(ingredient_item['value'])
        if item_info['name'] not in what_do_table.keys():
            what_do_table[item_info['name']] = what_do
            parent_table[item_info['name']] = max_rep.output_item_name()

def test_main():
    checked_recipes = []
    used_mats = [19697]

    for charac, recipe_num in get_known_recipes():
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
