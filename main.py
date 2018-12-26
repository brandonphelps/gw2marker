
from data_gathering import get_known_recipes, get_item_info, get_recipe_info, get_item_max_buy_price, get_item_min_sell_price, get_all_items, get_account_materials, get_items, get_item_id_by_name, get_recipe_ids, get_account_item_count, get_recipes, tp_instant_stock_info, tp_sell_stock, tp_buy_stock
from data_models import LoadedRecipe, get_item_recipe, get_recipe_min_make_price, test_function, TPItemStock
from graph_visitor import ItemTreeVisitor, LoadedRecipeVisitor, MinCostVisitor
from cache_funcs import timed_cache_data
from collections import defaultdict
from pprint import pprint
import subprocess
import math
from tqdm import tqdm
import pyprind

from pycallgraph import PyCallGraph, Config, GlobbingFilter
from pycallgraph.output import GraphvizOutput

item_max_buy_table = {}

item_name_max_buy_table = {}


def exchange_fee(gain):
    return math.floor(gain * 0.10)
    
def list_fee(gain):
    return math.floor(gain * 0.05)

def after_taxes(value):
    return value - (exchange_fee(value) + list_fee(value))

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
    finished = recipe_maker("Yassith's Visor")
    k.gendot(recipe_maker("Yassith's Pauldrons"))
    
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



def print_instant_instr_item(recipe_id, mat_ids, cut_off, buy_sell=True):
    l = LoadedRecipe(recipe_id)
    if not l.uses_mat(mat_ids):
        return 
    print("Checking: {}".format(l))

    sell_amount = 0
    min_sell_for = 0
    max_sell_for = 0
    tp_dictionary = {}
    tp_other_dic = {}
    buy_dictionary = defaultdict(int)
    account_item_holds = {}
    buy_rep = TPItemStock(l.output_id, 'buy')

    for i in l.all_item_ids():
        tp_dictionary[i] = TPItemStock(i, 'sell')
        tp_other_dic[i] = TPItemStock(i, 'buy')
        account_item_holds[i] = get_account_item_count(i)

    def current_mat_cost(tp_mat_consumption=True):
        t = 0
        mats = []
        for i in l.input_info:
            item_id = 0
            if type(i['value']) == LoadedRecipe:
                item_id = i['value'].output_id
            else:
                item_id = i['value']
            mats.append((i['count'], item_id))
            for c in range(i['count']):
                if not tp_mat_consumption and account_item_holds[item_id] > 0:
                    t += tp_other_dic[item_id].current_price(c)
                else:
                    t += tp_dictionary[item_id].current_price(c)
        return mats, t

    def purchase_and_sell(mats, tp_mat_consumption=True):
        """
        tp mat consumption can be turn off, so that the price is static, useful for when liquidating inventory
        use inventory consumption, but then go to tp if we are out. 
        """
        for i in mats:
            item_id = i[1]
            count = i[0]
            for c in range(count):
                if tp_mat_consumption:
                    tp_dictionary[item_id].consume(1)
                buy_dictionary[item_id] += 1

    buy_reasons = {'rep' : l}

    pro_perf = 0
    sell_amount = 0
    total_gain = 0
    total_supply_cost = 0
    while True:
        mats, cost = current_mat_cost(buy_sell)
        # mats, cost = get_best_mat_costs(l)
        gain = buy_rep.current_price()
        pro_perf = gain / cost

        if buy_sell:
            cost += exchange_fee(gain) + list_fee(gain)

        pro_perf = gain / cost

        if pro_perf >= cut_off:
            purchase_and_sell(mats, buy_sell)
            buy_rep.consume(1)
            total_gain += gain
            total_supply_cost += cost
            # print("Buy supply: {} {} {}".format(buy_rep.supply(), gain, pro_perf))        
            sell_amount += 1
        else:
            break

    buy_reasons['sell_amount'] = sell_amount
    if sell_amount > 0:
        print(buy_reasons)
        print("Total gain: {} Total cost: {} Prof: {}".format(total_gain, total_supply_cost, total_gain  - total_supply_cost))
        for i in buy_dictionary:
            print("{}: {}".format(get_item_info(i)['name'], buy_dictionary[i]))

    return 

# naive approach? 
    rep_input = get_recipe_input_sell_value(recipe_id)
    rep_input_cost = get_recipe_input_buy_value(recipe_id)
    for stock_item in tp_instant_stock_info(l.output_id):
        if rep_input != 0 and stock_item['unit_price'] / rep_input_cost > cut_off:
            sell_amount += stock_item['quantity']
            if max_sell_for == 0:
                max_sell_for = stock_item['unit_price']
            min_sell_for = stock_item['unit_price']
        else:
            if sell_amount != 0:
                print("{}".format(l))
                cost = get_recipe_input_buy_value(recipe_id, True)
                print("Cost: {}".format(cost))
                print("{} Min sell for {} Max sell for {} ".format(sell_amount, min_sell_for, max_sell_for))
            break


def mat_usage(recipe_id):
    l = LoadedRecipe(recipe_id)

    # print(f"Checking {l}")

    sell_amount = 0
    tp_dictionary = {'buy' : {}, 'sell' : {}}

    account_item_counts = {}
    item_usage_counts = defaultdict(int)
    buy_counts = defaultdict(int)

    tp_dictionary['buy'][l.output_id] = TPItemStock(l.output_id, 'buy')
    for i in l.all_item_ids():
        tp_dictionary['sell'][i] = TPItemStock(i, 'sell')
        tp_dictionary['buy'][i] = TPItemStock(i, 'buy')
        account_item_counts[i] = get_account_item_count(i)

    def current_mat_cost():
        buy_cost = 0
        sell_cost = 0
        mats_sell_value = 0
        mats_buy_value = 0
        my_mat_value = 0
        mats = []
        for i in l.input_info:
            item_id = 0
            if type(i['value']) == LoadedRecipe:
                item_id = i['value'].output_id
            else:
                item_id = i['value']
            mats.append((i['count'], item_id))
            items_used_count = 0

            for c in range(i['count']):
                indi_sel = tp_dictionary['buy'][item_id].current_price(c)
                indi_buy = tp_dictionary['sell'][item_id].current_price(c)
                # print(f"{get_item_info(item_id)['name']}: {indi_sel} {indi_buy}")
                mats_sell_value += indi_sel
                mats_buy_value += indi_buy

                if account_item_counts[item_id] > c:
                    my_mat_value += tp_dictionary['buy'][item_id].current_price(c) # how much are people buying the mats for
                    # print(f"I own a {get_item_info(item_id)['name']}")
                else:
                    my_mat_value += tp_dictionary['sell'][item_id].current_price(c)

                #if (account_item_counts[item_id] - items_used_count) > 0:
                #    buy_cost += tp_dictionary['buy'][item_id].current_price(c)
                #    sell_cost += tp_dictionary['sell'][item_id].current_price(c)
                #    items_used_count += 1
                #else:
                #    s = tp_dictionary['sell'][item_id].current_price(c - items_used_count)
                #    # print(f'Using tp stores: {s} {c - items_used_count}')
                #    buy_cost += s
                #print(buy_cost)
        return mats, mats_buy_value, mats_sell_value, my_mat_value # buy_cost, sell_cost

    def process_mats(mats):
        for count, item_id in mats:
            for c in range(count):
                if account_item_counts[item_id] > 0:
                    account_item_counts[item_id] -= 1
                    
                    item_usage_counts[item_id] += 1
                else:
                    buy_counts[item_id] += 1
                    tp_dictionary['sell'][item_id].consume(1)
                    
    total_gain = 0
    prof = 0
    sell_gradient = defaultdict(int)
    cost_gradient = defaultdict(int)


    while True:
        mats, mat_buy_value, mat_sell_value, my_mat_value = current_mat_cost()
        result_sell = 0
        for j in range(l.output_item_count):
            result_sell += tp_dictionary['buy'][l.output_id].current_price(j)

        # mat_buy_value # this this is how much it would be to sell all the materials 
        # mat_sell_value # this is how much it would cost to buy all the materials

        # result_sell -= exchange_fee(result_sell) + list_fee(result_sell) # this will check to see if buying the mats is more than what we could sell it for. 

        if after_taxes(my_mat_value) >= after_taxes(result_sell):
            # print(f"{my_mat_value} > {result_sell}")
            #if mat_buy_value > result_sell:
            #    # print("Mats are too expensive to buy")
            #    pass 
            #else:
            #print("Sell all the mats")
            #print("Total Buy Mat value: {}".format(mat_buy_value)) # 
            #print("Total Sell Mat Value: {}".format(mat_sell_value)) # 
            #print("My Mat value: {}".format(my_mat_value))
            #print("Output Sell value: {}".format(result_sell))
            break
        else:
            #print("Sell the result")
            #print("Total Buy Mat value: {}".format(mat_buy_value)) # this is how much it would cost to buy all the materials
            #print("Total Sell Mat Value: {}".format(mat_sell_value)) # this is how much it would be to sell all the materials 
            #print("My Mat value: {}".format(my_mat_value))
            #print("Output Sell value: {}".format(result_sell))
            # print(f"Buy Supply: {tp_dictionary['buy'][l.output_id].supply()} {result_sell} / {my_mat_value} {result_sell / my_mat_value}%")
            prof += after_taxes(result_sell) - after_taxes(my_mat_value)
            sell_gradient[result_sell] += 1
            process_mats(mats)
            tp_dictionary['buy'][l.output_id].consume(1)
            sell_amount += 1

    if sell_amount > 0:
        #for i in buy_counts:
        #    print(f"Buy: {get_item_info(i)['name']} {buy_counts[i]}")
        #for i in item_usage_counts:
        #    print(f"Use: {get_item_info(i)['name']} {item_usage_counts[i]}")
        #print(f"Sell {sell_amount} of {l} for total gain of {prof}")
        #print(f"Average Per Unit gain {math.floor(prof/sell_amount)}")
        #print("Sell Gradiant for output")
        #for i in sorted(sell_gradient.keys(), reverse=True):
        #    print(f"{i} ({after_taxes(i)}) {sell_gradient[i]} ")
        #print("Sell gradieant for mats")
        #for i in sorted(cost_gradient.keys()):
        #    print(f"{i} ({after_taxes(i)}) {cost_gradient[i]}")
        return prof, sell_amount, item_usage_counts, buy_counts, sell_gradient
    else:
        # print(f"Sell Mats for {get_item_info(l.output_id)['name']}")
        return 0

def profitable_craft_count(item_id, account_mat_count, tp_dict):
    prof_count = 0
    use_counts = 0
    buy_counts = 0

    return prof_count, use_counts, buy_counts

def another_attempt(recipe_ids, mat_ids):
    filtered_rep_ids = recipe_mat_filter(recipe_ids, mat_ids)
    """
    sell_mat_pool = []
    sell_mat_pool.extend(mat_ids)

    for i in filtered_rep_ids:
        l = LoadedRecipe(i)
        output_item_id = l.output_id
        sell_mat_pool.append(l.output_id)

    for i in sell_mat_pool:
        print(get_item_info(i)['name'])
    tp_dict = {'buy': {}, 'sell' : {}}
    account_item_counts = {}

    for i in sell_mat_pool:
        tp_dict['sell'][i] = TPItemStock(i, 'sell') 
        tp_dict['buy'][i] = TPItemStock(i, 'buy')
        account_item_counts[i] = get_account_item_count(i)

    profitable_craft_count(sell_mat_pool, account_item_counts, tp_dict)
    """
       
    for i in filtered_rep_ids:
        l = LoadedRecipe(i)
        blah = mat_usage(i)
        if blah == 0:
            # print(f"None mat usage for: {i}")
            continue
        else:
            profit_after_taxes = blah[0]
            print(f"{get_item_info(l.output_id)['name']} Average Sell Amount: {profit_after_taxes/blah[1]}")
            print(f"\tProf: {profit_after_taxes} Sell Amount: {blah[1]}")
            for i in blah[2]:
                print(f"\t\tUse: {get_item_info(i)['name']} {blah[2][i]}")
            for i in blah[3]:
                print(f"\t\tBuy: {get_item_info(i)['name']} {blah[3][i]}")
            print("Sell Gradient")
            for i in blah[4]:
                print(i)

def get_recipe_input_buy_value(recipe_id, print_t=False):
    loaded_rep = LoadedRecipe(recipe_id)
    input_value = 0
    for i in loaded_rep.input_info:
        if type(i['value']) == LoadedRecipe:
            input_value_id = i['value'].output_id
        else:
            input_value_id = i['value']
        value = get_item_min_sell_price(input_value_id)
        if print_t:
            print("Input: {} {} {}".format(get_item_info(input_value_id)['name'], i['count'], value))
        input_value += i['count'] * value
    return input_value
        
def get_recipe_input_sell_value(recipe_id, print_t=False):
    loaded_rep = LoadedRecipe(recipe_id)
    input_value = 0
    for i in loaded_rep.input_info:
        if type(i['value']) == LoadedRecipe:
            input_value_id = i['value'].output_id
        else:
            input_value_id = i['value']
        if print_t:
            print("Input: {} {} {}".format(get_item_info(input_value_id)['name'], i['count'], get_item_max_buy_price(input_value_id)))
        input_value += i['count'] * get_item_max_buy_price(input_value_id)
    return input_value

@timed_cache_data(60 * 3 * 60)
def value_of_recipe_id(recipe_id, print_t=False):
    return value_of_recipe(LoadedRecipe(recipe_id), print_t)

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


def recipe_mat_filter(recipe_id_list, mat_list):
    mat_id_set = set(mat_list)
    for i in recipe_id_list:
        l = LoadedRecipe(i)
        used_mats = set(l.immediate_mat_list())
        if mat_id_set.issuperset(used_mats):
            yield i

class SellableItem:
    def __init__(self, item_id, recipe_id):
        self._item_id = item_id
        self._recipe_id = recipe_id





if __name__ == "__main__":
#    pass
#config = Config()
#config.trace_filter = GlobbingFilter(exclude=['pycallgraph.*', 'requests.*', 'urllib3.*', '_find_and_load', '_handle_fromlist', '__new__', '_find_and_load_unlocked', '_ModuleLockManager'])

#graphviz = GraphvizOutput(output_file='stuff.png')
#with PyCallGraph(output=graphviz, config=config):

    parent_table = {}
    max_recipes = {}
    max_diff = 0
    checked_rep_ids = []
    count = 0

    get_item_info(89140)

    mat_names = ["Copper Ore",
                 "Lump of Tin",
                 "Bronze Ingot",
                 "Bone Chip",
                 "Vial of Weak Blood",
                 "Tiny Scale",
                 "Tiny Claw",
                 "Pile of Glittering Dust",
                 "Tiny Fang",
                 "Tiny Totem",
                 "Tiny Venom Sac",
                 "Mithril Ore",
                 "Mithril Ingot",
                 "Pile of Bloodstone Dust",
                 "Silk Scrap",
                 "Bolt of Silk"
                 "Darksteel Ingot",
                 "Silver Ore",
                 "Large Fang",
                 "Silver Ingot",
    ]

    mat_ids =  [get_item_id_by_name(i) for i in mat_names] # get_item_id_by_name("Potent Venom Sac"), get_] #, get_item_id_by_name("Mithril Ingot"), get_item_id_by_name("Mithril Ore")]

    reps = get_recipes()

    removed_dups = []
    for char, rep_id in get_known_recipes():
        if rep_id in removed_dups:
            continue
        removed_dups.append(rep_id)

    another_attempt(removed_dups, mat_ids)
