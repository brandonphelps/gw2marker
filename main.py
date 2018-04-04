
from data_gathering import get_known_recipes, get_item_info, get_recipe_info, get_item_max_buy_price, get_item_min_sell_price, get_all_items, get_account_materials
from data_models import LoadedRecipe, get_item_recipe

from pprint import pprint

item_max_buy_table = {}

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
            table[item_info['name']] = {'action' : 'material/buy',
                                        'parent' : recipe_output_info['name'],
                                        'count' : sub_ing['count']}
            update_sell(sub_ing['value'], parent_recipe_info, table)
        else:
            item_info = get_item_info(sub_ing['value'])

            table[item_info['name']] = {'action' : 'material/buy',
                                        'parent' : recipe_output_info['name'],
                                        'count' : sub_ing['count']}

#            if recipe_item_info['name'] in item_max_buy_table.keys():
#                current_parent_buy_price = item_max_buy_table[recipe_item_info['name']]['buy_price']
#            else:
#                current_parent_buy_price = 0
#
#            for recipe_sub_ing in sub_ing['value'].input_info:
#                if type(recipe_sub_ing['value']) == LoadedRecipe:
#                    print("Skipping: {}")
#                else:
#                    item_info = get_item_info(recipe_sub_ing['value'])
#                    #pprint(table)
#                    if item_info['name'] in table.keys() and table[item_info['name']]['parent'] in item_max_buy_table.keys():
#                        prev_parent_buy_price = item_max_buy_table[table[item_info['name']]['parent']]['buy_price']
#                    else:
#                        prev_parent_buy_price = 0
#
#                    if current_parent_buy_price > prev_parent_buy_price:
#                        table[item_info['name']] = {'action' : 'material/buy',
#                                                    'parent' : recipe_item_info['name'],
#                                                    'count' : 1}


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
                                                'count': 1}
            else:
                if sub_item_info['name'] not in table.keys():
                    table[sub_item_info['name']] = {'action' : 'sell',
                                                    'parent' : recipe_item_info['name'],
                                                    'count' : 1}
            update_sell(sub_ing['value'], recipe_item_info, table)
        else:
            item_info = get_item_info(sub_ing['value'])
            # todo, do we need to check if the item is already been marked for material/buy for another item? 
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
    elif type(value) == int:
        return value
    else:
        print("iunno what i got: {}".format(value))
        return None

def uses_mat(recipe, material_list, depth=1):
    recipe_item_info = get_item_info(recipe.output_id)
    a = 1 #debuging
    for i in recipe.input_info:
        if get_obj_id(i) in material_list:
            return True
        else:
            if type(i['value']) == LoadedRecipe:
                return uses_mat(i['value'], material_list, depth+1)
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
                print("Recipe {} contains {}".format(item_info['name'], 19699))
                create_table(recipe_num, table, max_table)
    pprint(max_table)
    print("\n\n")
    items_checked = []
    print("HERLJERKEJQLRKEJRLWEJR")
    sell_items = []
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
                        #print(value, ing_list)

    for i in sorted(sell_items, key=lambda x: x[2]):
        print("Sell! {}: cost {} buy {}".format(i[3], i[2], i[0]))
        print("{}\n".format(i[1]))


if __name__ == "__main__":
    table = {}
    main()
