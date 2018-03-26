
from data_gathering import get_known_recipes, get_item_info, get_recipe_info, get_item_max_buy_price
from data_models import LoadedRecipe

from pprint import pprint

item_max_buy_table = {}

def create_table(recipe_id, table):
    recipe_info = get_recipe_info(recipe_id)
    recipe_item_info = get_item_info(recipe_info['output_item_id'])
    l = LoadedRecipe(recipe_id)
    max_ingre = find_max(l, item_max_buy_table)
    for sub_ing in max_ingre[1]:
        print(sub_ing)
        if type(sub_ing['value']) == LoadedRecipe:
            pass
        else:
            item_info = get_item_info(sub_ing['value'])
            if item_info['name'] in table.keys():
                pass
            else:
                table[item_info['name']] = {'action' : 'sell',
                                            'parent' : recipe_item_info['name'],
                                            'count' : sub_ing['count']}

def find_max(recipe, item_buy_table):
    recipe_buy_price = get_item_max_buy_price(recipe.output_id)
    tmp = 0
    ing = []
    for j in recipe.input_info:
        if type(j['value']) == LoadedRecipe:
            ing_price, tmp_ing = find_sub_max(j['value'], item_buy_table)
            ing.extend(tmp_ing)
            tmp += j['count'] * ing_price
        else:
            ing.append(j)
            tmp += j['count'] * get_item_max_buy_price(j['value'])
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
        return False

if __name__ == "__main__":
    table = {}

    checked_recipes = []
    for charac, recipe_num in get_known_recipes():
        if recipe_num not in checked_recipes and uses_mat(recipe_num, [19719]):
            checked_recipes.append(recipe_num)
            recipe = LoadedRecipe(recipe_num)
            item_info = get_item_info(recipe.output_id)
            print("Checking recipe: {}".format(item_info['name']))
            create_table(recipe_num, table)
    pprint(table)

