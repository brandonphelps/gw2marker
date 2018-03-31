
from data_gathering import get_known_recipes, get_item_info, get_recipe_info, get_item_max_buy_price
from data_models import LoadedRecipe

from pprint import pprint

item_max_buy_table = {}

def update_table_sub_recip(recip, parent_recipe, table):
    recipe_item_info = get_item_info(recip.output_id)
    if recipe_item_info['name'] in item_max_buy_table.keys():
        current_parent_buy_price = item_max_buy_table[recipe_item_info['name']]['buy_price']
    else:
        current_parent_buy_price = 0

def update_sell(recipe_info, parent_recipe_info, table):
    if parent_recipe_info['name'] in item_max_buy_table.keys():
        current_parent_buy_price = item_max_buy_table[parent_recipe_info['name']]['buy_price']
    else:
        current_parent_buy_price = 0

    for sub_ing in recipe.input_info:
        if type(sub_ing['value']) == LoadedRecipe:
            pass
        else:
            item_info = get_item_info(sub_ing['value'])
            if item_info['name'] in table.keys() and table[item_info['name']]['parent'] in item_max_buy_table.keys():
                prev_parent_buy_price = item_max_buy_table[table[item_info['name']]['parent']]['buy_price']
            else:
                prev_parent_buy_price = 0

            if item_info['name'] not in table.keys():
                table[item_info['name']] = {'action' : 'sell',
                                            'parent' : parent_recipe_info['name'],
                                            'count' : sub_ing['count']}


def create_table(recipe_id, table):
    recipe_info = get_recipe_info(recipe_id)
    recipe_item_info = get_item_info(recipe_info['output_item_id'])
    l = LoadedRecipe(recipe_id)
    max_ingre = find_max(l, item_max_buy_table)
    for sub_ing in max_ingre[1]:
        print(sub_ing)
        if type(sub_ing['value']) == LoadedRecipe:
            update_sell(sub_ing['value'], recipe_item_info, table)
            if recipe_item_info['name'] in item_max_buy_table.keys():
                current_parent_buy_price = item_max_buy_table[recipe_item_info['name']]['buy_price']
            else:
                current_parent_buy_price = 0

            for recipe_sub_ing in sub_ing['value'].input_info:
                if type(recipe_sub_ing['value']) == LoadedRecipe:
                    print("Skipping: {}")
                else:
                    item_info = get_item_info(recipe_sub_ing['value'])
                    #pprint(table)
                    if item_info['name'] in table.keys() and table[item_info['name']]['parent'] in item_max_buy_table.keys():
                        prev_parent_buy_price = item_max_buy_table[table[item_info['name']]['parent']]['buy_price']
                    else:
                        prev_parent_buy_price = 0

                    if current_parent_buy_price > prev_parent_buy_price:
                        table[item_info['name']] = {'action' : 'material/buy',
                                                    'parent' : recipe_item_info['name'],
                                                    'count' : 1}
        else:
            item_info = get_item_info(sub_ing['value'])
            if item_info['name'] not in table.keys():
                table[item_info['name']] = {'action' : 'sell',
                                            'parent' : recipe_item_info['name'],
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

def uses_mat(recipe_id, material_list, depth=1):
    recipe = LoadedRecipe(recipe_id)
    for i in recipe.input_info:
        if get_obj_id(i) in material_list:
            return True
        else:
            if type(i) == LoadedRecipe:
                return uses_mat(get_recipe_item(i.output_id), material_list, depth+1)
    else:
        return False

if __name__ == "__main__":
    table = {}

    checked_recipes = []
    for charac, recipe_num in get_known_recipes():
        if recipe_num not in checked_recipes and uses_mat(recipe_num, [19699]):
            checked_recipes.append(recipe_num)
            recipe = LoadedRecipe(recipe_num)
            item_info = get_item_info(recipe.output_id)
            print("Checking recipe: {}".format(item_info['name']))
            create_table(recipe_num, table)
    pprint(table)
    pprint(item_max_buy_table)
