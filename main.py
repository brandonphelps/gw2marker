

from data_gathering import GW2Request, Uri, get_recipe_ids
from data_gathering import get_item_min_sell_price, get_recipe_max_buy_price
from data_gathering import get_characters, get_character_crafting, get_character_recipes
from data_gathering import get_known_recipes
from d_models import Recipe, Item

from graphviz import Digraph

import pdb

from pprint import pprint

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


    for character_name, recipe_num in get_known_recipes():
        graph_details = []
        recipe_listing = []
        print("Checking recipe num: {}".format(recipe_num))

        dot = Digraph(comment=recipe_num)
        buy_price = get_recipe_max_buy_price(recipe_num)
        cost_price = calculate_cost_profit(recipe_num, recipe_listing, graph_details)
        fees = int(cost_price * .15)
        if buy_price > (cost_price + fees):
            rep = Recipe(recipe_num)
            item = Item(rep.output_id)
            if item:
                print(item.name)
            print("{} can make {}".format(character_name, recipe_num))
            print("Buy Price {} Total cost {} fee {}".format(buy_price, cost_price, fees))
            pprint(recipe_listing)
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
    
