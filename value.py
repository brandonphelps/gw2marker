from data_gathering import get_known_recipes, get_item_info, get_recipe_info, get_item_max_buy_price, get_item_min_sell_price, get_all_items, get_account_materials, get_items, get_item_id_by_name, get_recipe_ids, get_account_item_count, get_recipes, tp_instant_stock_info, tp_sell_stock, tp_buy_stock
from data_models import LoadedRecipe, get_item_recipe, get_recipe_min_make_price, test_function, TPItemStock
from graph_visitor import ItemTreeVisitor, LoadedRecipeVisitor, MinCostVisitor
from cache_funcs import timed_cache_data
from collections import defaultdict, namedtuple
from pprint import pprint
import subprocess
import math
from tqdm import tqdm
import time
import math

from copy import deepcopy
from pycallgraph import PyCallGraph, Config, GlobbingFilter
from pycallgraph.output import GraphvizOutput


SellEntry = namedtuple('SellEntry', ['count', 'item_id'])

# key is item_id of item to sell
# count is number of items to sell
# sell_dict = {}

class key_dependent_dict(defaultdict):
    def __init__(self, f_of_x):
        super().__init__(None)
        self.f_of_x = f_of_x
    def __missing__(self, key):
        ret = self.f_of_x(key)
        self[key] = ret
        return ret

def after_taxes(gain):
    return math.floor(gain - (gain * .15))

def build_tp_dict(mat_ids):
    tp_dict = {'buy' : {}, 'sell' : {}}
    tp_dict = {'buy' : key_dependent_dict(lambda x: TPItemStock(x, 'buy')), 'sell' : key_dependent_dict(lambda x: TPItemStock(x, 'sell'))}
    for i in mat_ids:
        tp_dict['buy'][i] = TPItemStock(i, 'buy')
        tp_dict['sell'][i] = TPItemStock(i, 'sell')
    return tp_dict

def build_account_mat_count(mat_ids):
    blah = key_dependent_dict(lambda x: get_account_item_count(x))
    for i in mat_ids:
        blah[i] = get_account_item_count(i)

        #    blah[i] = 0
        #    print(f"FAiled to get item count for : {i} {get_item_info(i)['name']}")
        #    exit(1)
    return blah

def blakfj(jfdk):
    if type(jfdk['value']) == LoadedRecipe:
        wejr = jfdk['value'].output_id
    else:
        wejr = jfdk['value']
    return wejr

def recipe_output_value(l, tp_dict, account_mats):
    output_id = l.output_id
    t = 0
    for i in range(l.output_item_count):
        t += tp_dict['buy'][output_id].current_price(i)
    return t







def cheapest_crafting(l, tp_dict, account_mats, opts=None):

    temp_acc_mats = key_dependent_dict(lambda x: get_account_item_count(x))
    temp_acc_mats.update(account_mats)

    if opts is None:
        opts = {'buy' : defaultdict(int), 'use' : defaultdict(int), 'craft' : defaultdict(int)}

    min_cost = 0



    for info in l.input_info:
        item_id = blakfj(info)
        for c in range(info['count']):
            buy_cost = tp_dict['sell'][item_id].current_price(opts['buy'][item_id])

            sub_item_recipe, id_type = get_item_recipe(item_id)
            if id_type == 'recipe':
                print(f"Crafted Item {get_item_info(item_id)['name']}")
                sub_opts = {'buy' : defaultdict(int), 'use' : defaultdict(int), 'craft' : defaultdict(int)}
                for i in opts['buy']:
                    sub_opts['buy'][i] = opts['buy'][i]
                    print(sub_opts['buy'][i])
                for i in sub_opts['use']:
                    sub_opts['use'][i] = opts['use'][i]
                for i in sub_opts['craft']:
                    sub_opts['craft'][i] = opts['craft'][i]
                craft_cost = cheapest_crafting(LoadedRecipe(sub_item_recipe), tp_dict, account_mats, sub_opts)
            else:
                print(f"Item {get_item_info(item_id)['name']}")
                craft_cost = 1000000000
                
            if buy_cost < have_cost:
                min_cost += buy_cost
                opts['buy'][item_id] += 1
                

            if have_cost < buy_cost:
                if have_cost < craft_cost:
                    min_cost += have_cost
                    opts['use'][item_id] += 1
                else:
                    min_cost += craft_cost
                    opts['craft'][item_id] += 1
                    for i in sub_opts['buy']:
                        opts['buy'][i] = sub_opts['buy'][i]
                    for i in sub_opts['use']:
                        opts['use'][i] = sub_opts['use'][i]
                    for i in sub_opts['craft']:
                        opts['craft'][i] = sub_opts['craft'][i]
            else:
                if buy_cost < craft_cost:
                    min_cost += buy_cost
                    opts['buy'][item_id] += 1
                else:
                    min_cost += craft_cost
                    opts['craft'][item_id] += 1
                    for i in sub_opts['buy']:
                        opts['buy'][i] = sub_opts['buy'][i]
                    for i in sub_opts['use']:
                        opts['use'][i] = sub_opts['use'][i]
                    for i in sub_opts['craft']:
                        opts['craft'][i] = sub_opts['craft'][i]
    return min_cost
























def recipe_input_value(l, tp_dict, account_mats):
    cost = 0
    gain = 0
    mats = {'buy' : defaultdict(int), 'use' : defaultdict(int), 'craft' : defaultdict(int)}
    for info in l.input_info:
        item_id = blakfj(info)
        # TODO MAKE RECURSIVE FOR MINIMUM ITEM CRAFT COST
        for c in range(info['count']):
            have_cost = 0
            have_gain = 0

            buy_cost = 0
            buy_gain = 0

            craft_cost = 0
            craft_gain = 0

            if account_mats[item_id] > c:
                # mats['use'][item_id] += 1
                have_cost = tp_dict['buy'][item_id].current_price()
                have_gain = tp_dict['buy'][item_id].current_price()
            else:
                have_cost = 100000000
                have_gain = 0

            # mats['buy'][item_id] += 1
            buy_cost = tp_dict['sell'][item_id].current_price()
            buy_gain = tp_dict['buy'][item_id].current_price()
            opt = None
            if have_cost < buy_cost:
                opt = 'have'
                #if not (have_cost < craft_cost):
                #    opt = 'craft'
            else: # craft cost <= have_cost
                opt = 'buy'
                #if craft_cost < buy_cost:
                #    opt = 'craft'

            assert opt != None

            if opt == 'have':
                cost += have_cost
                gain += have_gain
                mats['use'][item_id] += 1
            elif opt == 'buy':
                cost += buy_cost
                gain += buy_gain
                mats['buy'][item_id] += 1
            elif opt == 'craft':
                cost += craft_cost
                gain += craft_gain
                for i in craft_mats['use']:
                    mats['use'][i] += craft_mats['use'][i]
                for i in craft_mats['buy']:
                    mats['buy'][i] += craft_mats['buy'][i]
                mats['craft'][item_id] += 1
            #print(get_item_info(item_id)['name'], gain, cost)
    return cost, gain, mats

def value(sell_list, tp_dict=None):
    mat_ids = [item_id for item_id, count in sell_list.items()]
    if tp_dict is None:
        tp_dict = build_tp_dict(mat_ids)

    sell_count = defaultdict(int)

    s = 0 
    for item_id, count in sell_list.items():
        for c in range(count):
            s += tp_dict['buy'][item_id].current_price(c)
    return s

def recipe_mat_filter(recipe_id_list, mat_list):
    mat_id_set = set(mat_list)
    for i in recipe_id_list:
        l = LoadedRecipe(i)
        used_mats = set(l.immediate_mat_list())
        if mat_id_set.issuperset(used_mats):
            yield i

def subtract_mats(recipe, account_mats):
    new_account_mats = {}
    return new_account_mats

def generate_sell_list(base_mat_ids, dont_sell_list=None, process_count_limit=1000, cut_off=1.0):
    available_recipes = []
    seen_recipes = []
    available_output_items = {}
    for i in base_mat_ids:
        available_output_items[i] = None

    print("Filtering recipe based on materials")
    for i in recipe_mat_filter(get_known_recipes(), base_mat_ids):
        l = LoadedRecipe(i)
        if l.recipe_id in seen_recipes:
            continue
        else:
            seen_recipes.append(l.recipe_id)
        available_output_items[l.output_id] = l
        print(get_item_info(l.output_id)['name'])
        available_recipes.append(l)

    print("Building material counts")
    mat_account_counts = build_account_mat_count(available_output_items.keys())

    if dont_sell_list:
        for mat_id, count in dont_sell_list.items():
            if mat_id in mat_account_counts.keys():
                if count > mat_account_counts[mat_id]:
                    mat_account_counts[mat_id] = 0
                else:
                    mat_account_counts[mat_id] -= count

    print("Building TP Dictionary")
    tp_dict = build_tp_dict(available_output_items.keys())
    total_resource_usage = {'use' : defaultdict(int), 'buy' : defaultdict(int), 'sell' : defaultdict(int)}
    total_buy_flag = False
    def helper():
        max_sell = 0
        max_value = 0
        max_id = 0
        tmp_value = 0
        max_pro = 0
        mats_to_consume = {'buy' : defaultdict(int),
                           'use' : defaultdict(int)}
        
        for item_id in available_output_items.keys():
            if available_output_items[item_id]:
                input_cost, input_gain, consume_mats = recipe_input_value(available_output_items[item_id], tp_dict, mat_account_counts)
                output_gain = recipe_output_value(available_output_items[item_id], tp_dict, mat_account_counts)

                if mat_account_counts[item_id] > 0: # todo thoughts?
                    consume_mats = {'use' : defaultdict(int), 'buy' : defaultdict(int)} # dont' consume any mats since we have the item
                    input_cost = 0
                    for i in range(available_output_items[item_id].output_item_count):
                        input_cost += tp_dict['sell'][item_id].current_price(i)
            else:
                if mat_account_counts[item_id] > 0:
                    consume_mats = {'use' : defaultdict(int), 'buy' : defaultdict(int)} # use is not indicated since we always pull out the sold item if
                    # we have the account mat
                    input_cost = tp_dict['buy'][item_id].current_price()
                else:
                    consume_mats = {'use' : defaultdict(int), 'buy' : {item_id : 1}}
                    input_cost = tp_dict['sell'][item_id].current_price() # used to be buy testing it 
                output_gain = tp_dict['buy'][item_id].current_price()

            if input_cost == 0:
                input_cost = 0.000001
            tmp_value = after_taxes(output_gain) / input_cost

            
            if tmp_value > max_value and ((consume_mats['use'] or mat_account_counts[item_id] > 0) or tmp_value > 1.0):
                #print(f"{get_item_info(item_id)['name']}: ({output_gain}) {after_taxes(output_gain)} / {input_cost} = {after_taxes(output_gain) / input_cost}")
                        
                max_id = item_id
                max_value = tmp_value
                max_pro = output_gain
                max_cost = input_cost
                mats_to_consume = consume_mats
            else:
                pass
                #print("Could make recipe, but not mats used")
                #print(get_item_info(item_id)['name'], tmp_value)
        
        purchase_cost = 0
            
        for j in mats_to_consume['buy']:
            for i in range(mats_to_consume['buy'][j]):
                purchase_cost += tp_dict['sell'][j].current_price()
                tp_dict['sell'][j].consume(1)
                total_resource_usage['buy'][j] += 1

        for j in mats_to_consume['use']:
            mat_account_counts[j] -= mats_to_consume['use'][j]
            assert mat_account_counts[j] >= 0
            total_resource_usage['use'][j] += mats_to_consume['use'][j]


        if max_id != 0:
            tp_dict['buy'][max_id].consume(1)
            total_resource_usage['sell'][max_id] += 1
            if mat_account_counts[max_id] > 0:
                mat_account_counts[max_id] -= 1
            return max_value, max_id, after_taxes(max_pro) - purchase_cost
        else:
            return 0, 0, 0

    for i in mat_account_counts:
        print(f"{get_item_info(i)['name']}: {mat_account_counts[i]}")

    t = 1
    cont = True
    process_count = 0
    total_pro = 0
    while t >= cut_off and cont and process_count < process_count_limit:
        t, crafted_item, tmp_pro = helper()
        total_pro += tmp_pro
        process_count += 1
        cont = False
        for i in mat_account_counts:
            if mat_account_counts[i] > 0:
                cont = True
                break
        if crafted_item != 0:
            print(f"Created: {get_item_info(crafted_item)['name']}: {total_resource_usage['sell'][crafted_item]}")
        else:
            cont = False

    for i in total_resource_usage['sell']:
        print(f"Sell: {get_item_info(i)['name']} {total_resource_usage['sell'][i]}")
    for i in total_resource_usage['buy']:
        print(f"Buy: {get_item_info(i)['name']} {total_resource_usage['buy'][i]}")
    for i in total_resource_usage['use']:
        print(f"Use: {get_item_info(i)['name']} {total_resource_usage['use'][i]}")
    print(f"Total prof: {total_pro}")

def basic_tier_one():
    return ["Jute Scrap", "Bolt of Jute", "Spool of Jute Thread", "Rawhide Leather Section",
            "Stretched Rawhide Leather Square", "Copper Ore", "Lump of Tin",
            "Copper Ingot", "Bronze Ingot", "Green Wood Log", "Green Wood Plank"]

def basic_tier_two():
    return ["Wool Scrap", "Bolt of Wool", "Spool of Wool Thread", "Iron Ore", "Iron Ingot", "Thin Leather Section", "Cured Thin Leather Square", "Soft Wood Log", "Soft Wood Plank"]

def basic_tier_three():
    return ["Cotton Scrap", "Bolt of Cotton", "Spool of Cotton Thread", "Gold Ore", "Lump of Coal", "Gold Ingot", "Steel Ingot", "Coarse Leather Section", "Cured Coarse Leather Square", "Seasoned Wood Log", "Seasoned Wood Plank"]

def basic_tier_four():
    return ["Linen Scrap", "Bolt of Linen", "Spool of Linen Thread", "Platinum Ore", "Lump of Primordium", "Platinum Ingot", "Darksteel Ingot", "Rugged Leather Section", "Cured Rugged Leather Square", "Hard Wood Log", "Hard Wood Plank"]

def basic_tier_five():
    return ["Silk Scrap", "Bolt of Silk", "Spool of Silk Thread", "Mithril Ore", "Mithril Ingot", "Thick Leather Section", "Cured Thick Leather Square", "Elder Wood Log", "Elder Wood Plank"]

def basic_tier_six():
    return ["Gossamer Scrap", "Bolt of Gossamer", "Spool of Gossamer Thread", "Orichalcum Ore", "Orichalcum Ingot", "Hardened Leather Section", "Cured Hardened Leather Square", "Ancient Wood Log", "Ancient Wood Plank"]

def basic_pigments():
    return ["Pouch of {} Pigment".format(color) for color in ["Brown", "Red", "Orange", "Yellow", "Green", "Blue", "Purple", "White", "Black"]]

def basic_misc():
    return ["Crafter's Backpack Frame", "Lump of Glass", "Pile of Flax Seeds", "Flax Fiber", "Milling Stone", "Milling Basin"]

def inter_tier_one():
    return ["Bone Chip", "Tiny Claw", "Pile of Glittering Dust", "Tiny Fang", "Tiny Scale", "Tiny Totem", "Tiny Venom Sac", "Vial of Weak Blood"]

def inter_tier_two():
    return ["Bone Shard", "Small Claw", "Pile of Shimmering Dust", "Small Fang", "Small Scale", "Small Totem", "Small Venom Sac", "Vial of Thin Blood"]

def inter_tier_three():
    return ["Bone", "Claw", "Pile of Radiant Dust", "Fang", "Scale", "Totem", "Venom Sac", "Vial of Blood"]

def inter_tier_four():
    return ["Heavy Bone", "Sharp Claw", "Pile of Luminous Dust", "Sharp Fang", "Smooth Scale", "Engraved Totem", "Full Venom Sac", "Vial of Thick Blood"]

def inter_tier_five():
    return ["Large Bone", "Large Claw", "Pile of Incandescent Dust", "Large Fang", "Large Scale", "Intricate Totem", "Potent Venom Sac", "Vial of Potent Blood"]

def inter_tier_six():
    return ["Ancient Bone", "Vicious Claw", "Pile of Crystalline Dust", "Vicious Fang", "Armored Scale", "Elaborate Totem", "Powerful Venom Sac", "Vial of Powerful Blood"]

def inter_tier_misc():
    return ["Karka Shell", "Watchwork Sprocket", "Blade Shard", "Vial of Linseed Oil", "Piece of Mother-of-Pearl", "Leaf Fossil", "Barbed Thorn", "Pile of Coarse Sand", "Shimmering Crystal", "Tenebrous Crystal"]

def advance_tier_one():
    return ["Pile of Soiled Essence",
            "Onyx Sliver",
            "Molten Sliver",
            "Glacial Sliver",
            "Destroyer Sliver",
            "Crystal Sliver",
            "Corrupted Sliver",
            "Charged Sliver",
            "Mordrem Sliver",
            "Evergreen Sliver",
            "Resonating Sliver",
            "Vial of Condensed Mists Essence"]

def advance_tier_two():
    return ["Pile of Foul Essence",
            "Onyx Fragment",
            "Molten Fragment",
            "Glacial Fragment",
            "Destroyer Fragment",
            "Crystal Fragment",
            "Corrupted Fragment",
            "Charged Fragment",
            "Mordrem Fragment",
            "Evergreen Fragment",
            "Resonating Fragment",
            "Glob of Coagulated Mists Essence"]

def main():
    mat_names = []
    mat_names.extend(basic_tier_one())
    mat_names.extend(basic_tier_two())
    #mat_names.extend(basic_tier_three())
    #mat_names.extend(basic_tier_four())
    #mat_names.extend(basic_tier_five())
    #mat_names.extend(basic_tier_six())
    mat_names.extend(basic_pigments())
    mat_names.extend(basic_misc())
    mat_names.extend(inter_tier_one())
    mat_names.extend(inter_tier_two())
    #mat_names.extend(inter_tier_four())
    #mat_names.extend(inter_tier_five())
    #mat_names.extend(inter_tier_six())
    mat_names.extend(inter_tier_misc())
    mat_names.extend(advance_tier_one())
    mat_names.extend(advance_tier_two())

    mat_ids =  [get_item_id_by_name(i) for i in mat_names]

    mats = {'buy' : defaultdict(int), 'use' : defaultdict(int), 'craft' : defaultdict(int)}
    #value = cheapest_crafting(LoadedRecipe(get_item_recipe(get_item_id_by_name("Malign Bronze Axe"))[0]), build_tp_dict(mat_ids), build_account_mat_count(mat_ids), mats)
    #print(value)
    #for i in mats:
    #    print(f'Opt: {i}')
    #    for opt in mats[i]:
    #        print(f"Item: {get_item_info(opt)['name']}: {mats[i][opt]}")
    #exit(1)
    for index, id in enumerate(mat_ids):
        if id is None:
            print(f"Unable to find id for {mat_names[index]}")
            exit(1)
    account_mats = build_account_mat_count(mat_ids)
    dont_sell_amounts = [('Bolt of Jute', 100), ("Jute Scrap", 170), ("Stretched Rawhide Leather Square", 100), ("Rawhide Leather Section", 100)]
    ids_dont_sells = {get_item_id_by_name(mat_name) : count for mat_name, count in dont_sell_amounts}
    mat_ids = [get_item_id_by_name(item_name) for item_name in mat_names]
    generate_sell_list(mat_ids, ids_dont_sells, 4000, .5)
    

if __name__ == "__main__":
#config = Config()
#
#config.trace_filter = GlobbingFilter(exclude=['pycallgraph.*', 'requests.*', 'urllib3.*', '_find_and_load', '_handle_fromlist', '__new__', '_find_and_load_unlocked', '_ModuleLockManager'])

#graphviz = GraphvizOutput(output_file='stuff.png')
#with PyCallGraph(output=graphviz, config=config):

    main()

    
