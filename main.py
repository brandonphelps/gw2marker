

from data_gathering import GW2Request, Uri, get_recipe_ids
from data_gathering import get_item_min_sell_price, get_recipe_max_buy_price
from data_gathering import get_characters, get_character_crafting, get_character_recipes
from data_gathering import get_known_recipes, get_all_items, get_item_max_buy_price
from data_models import Recipe, Item

from graphviz import Digraph

import pdb

from pprint import pprint
from functools import lru_cache

all_items_by_id = {}

def load_all_items():
    print("Loading Items")
    for i in range(1000):
        all_items_by_id[str(i)] = Item(i)

@lru_cache(maxsize=40000)
def get_item_recipe(item_id):
    i = Item(item_id)
    #print("Get item {} recipe: {}".format(i.name, i.recipe_id))
    if int(i.recipe_id) == -1: # thus we have no recipe for item
        return None
    elif int(i.recipe_id) == 0:
        for j in get_recipe_ids():
            recp = Recipe(j)
            if recp.output_id == item_id:
                i.recipe_id = j
                i.save()
                return recp
        # couldn't find recipe thus we'll mark down there isn't one
        if i.recipe_id == 0:
            i.recipe_id = -1
            i.save()
    else:
        return Recipe(i.recipe_id)

def get_item_make_price(item_id, recipe_listing, dot):
    recipe = get_item_recipe(item_id)
    #todo: check inventory for mats and reduce price etc
    if recipe is None:
        return get_item_min_sell_price(item_id)
    else:
        return calculate_cost_profit(recipe.recipe_id, recipe_listing, dot)

def calculate_cost_profit(recipe_id, recipe_listing, dot):
    recipe = Recipe(recipe_id)
    cost = 0
    item_t = Item(recipe.output_id)
    for j in recipe.input_info:
        recipe_list = []
        graph_details = []
        itm = Item(j['item_id'])
        min_sell_price = get_item_min_sell_price(j['item_id'])
        make_price = get_item_make_price(j['item_id'], recipe_list, graph_details)
        cost += j['count']  * min(min_sell_price, make_price)
        edge_info = {'edge' : [itm.name, item_t.name]}
        if min_sell_price <= make_price:
            recipe_listing.append({'buy' : itm.name, 'cost' : min_sell_price})
            # dot.node(itm.name, color='red')
            edge_info['color'] = 'red'
            edge_info['cost'] = str(min_sell_price)
        else:
            # dot.node(itm.name, color='green')
            edge_info['color'] = 'green'
            recipe_listing.append({'make':  itm.name, 'cost' : make_price})
            recipe_listing.extend(recipe_list)
            dot.extend(graph_details)
        dot.append(edge_info)
        #dot.edge(itm.name, item_t.name, label=str(j['count']))

        #print("Item {} {} has min sell price {}".format(itm.item_id, itm.name, cost))
    return cost

def main():
    count = 0

    for character_name, item_id in get_all_items():
        graph_details = []
        recipe_listing = []
        #print("Checking item num {} {}".format(character_name, item_id))
        #count += 1
        #if count > 10:
        #    break
        buy_price = get_item_max_buy_price(item_id)
        cost_price = 0
        fees = int(buy_price * .15)
        item = Item(item_id)
        #if item:
        #    print("{} Sell Value {} Cost {}".format(item.name, buy_price, cost_price + fees))
        #else:
        #    print("Failed to get item info for: {}".format(rep.output_id))
        if buy_price > (cost_price + fees):
            print("Sell that {} {} for {}".format(character_name, item.name, buy_price - fees))

    for character_name, recipe_num in get_known_recipes():
        graph_details = []
        recipe_listing = []
        #print("Checking recipe num: {}".format(recipe_num))
        #count += 1
        #if count > 10:
        #    break

        buy_price = get_recipe_max_buy_price(recipe_num)
        cost_price = calculate_cost_profit(recipe_num, recipe_listing, graph_details)
        fees = int(buy_price * .15)
        rep = Recipe(recipe_num)
        item = Item(rep.output_id)
        #if item:
        #    print("{} Sell Value {} Cost {}".format(item.name, buy_price, cost_price + fees))
        #else:
        #    print("Failed to get item info for: {}".format(rep.output_id))

        if buy_price > (cost_price + fees):
            if item:
                print(item.name)
            print("{} can make {}".format(character_name, recipe_num))
            print("Buy Price {} Total cost {} fee {}".format(buy_price, cost_price, fees))
            pprint(recipe_listing)
            dot = Digraph(comment=recipe_num)
            for edge in graph_details:
                dot.edge(*edge['edge'])
                for i in edge['edge']:
                    if i != item.name:
                        label = "{}".format(i)
                        if edge['color'] == 'red':
                            label += " : {}".format(edge['cost'])
                        dot.node(i, color = edge['color'], label=label)

            dot.render(view=True)


if __name__ == "__main__":
    main()
    
