import textwrap
import subprocess
from data_models import LoadedRecipe
from data_gathering import get_item_info, get_account_item_count, is_item_account_bound, get_item_min_sell_price, get_item_max_buy_price, get_known_recipes
from collections import defaultdict

import os

GRAPH_FOLDER = 'graphs'

class GraphVisitor:
    def __init__(self):
        self.dot_header = [textwrap.dedent("""digraph astgraph {
        node [shape=circle, fontsize=12, fontname=\"Courier\", height=.1]
        ranksep=.3;
        edge [arrowsize=.5]
        \n""")]
        self.dot_body = []
        self.dot_footer = ["}"]
        self.count = 0

    def _create_graph(self, graph_name='graph'):
        if not os.path.isdir(GRAPH_FOLDER):
            os.makedirs(GRAPH_FOLDER)
        with open(os.path.join(GRAPH_FOLDER, f'{graph_name}.dot'), 'w') as writer:
            writer.write(''.join(self.dot_header + self.dot_body + self.dot_footer))
        subprocess.run(['dot', '-Tpng', '-o', os.path.join(GRAPH_FOLDER, f'{graph_name}.png'), os.path.join(GRAPH_FOLDER, f'{graph_name}.dot')])

    def gendot(self, recipe, graph_name='graph'):
        self.visit(recipe)
        self._create_graph(graph_name)

    def add_node(self, node_label, color=None):
        node_line = f"node{self.count}"
        properties = []

        if node_label:
            properties.append(f"label=\"{node_label}\"")

        if color:
            properties.append(f"color={color}")

        if properties:
            node_line += "["
        for prop in properties[:-1]:
            node_line += f"{prop},"
        if properties:
            node_line += "{}]".format(properties[-1])

        node_line += "\n"

        self.dot_body.append(node_line)
        my_id = self.count
        self.count += 1
        return my_id

    def add_edge(self, parent_id, child_id, label=None):
        blah = "node{} -> node{}".format(parent_id, child_id)
        if label:
            blah += " [label=\"{}\"]".format(label)
        blah += "\n"
        self.dot_body.append(blah)


class ItemTreeVisitor(GraphVisitor):
    def visit(self, item_tree):
        my_id = self.add_node(item_tree.output_item.name)
        for i in item_tree.input_trees():
            child_id = self.add_node(i.output_item.name)
            self.add_edge(my_id, child_id, " {}".format(i.output_count))

class LoadedRecipeVisitor(GraphVisitor):
    sub_mat_count=True
    display_cost=True

    def visit(self, loaded_recipe):
        self.used_items = defaultdict(int)
        self.costs = defaultdict(int) # key is item id, value is total cost of item.
        if isinstance(loaded_recipe, list):
            for i in loaded_recipe:
                self.loaded_recipe_visit(i, 1, self.sub_mat_count)
        else:
            self.loaded_recipe_visit(loaded_recipe, 1, self.sub_mat_count)

        self.add_legend()

    def add_legend(self):
        pass

    def get_mat_count_left(self, item_id):
        k = get_account_item_count(item_id) # how many items the account has
        used_count = self.used_items[item_id] # total used so far
        return max(k - used_count, 0)
            
    def loaded_recipe_visit(self, loaded_recipe, count, sub_mat_count=False, only_needed=True):
        # tmp = get_item_info(loaded_recipe.output_id)
        parent_id = self.item_visit(loaded_recipe.output_id)
        for i in loaded_recipe.input_info:
            if isinstance(i['value'], LoadedRecipe):
                item_id = i['value'].output_id
            else:
                item_id = i['value']
            item_name = get_item_info(item_id)['name']

            total_item_count = i['count'] * count
            
            if sub_mat_count:
                have_item_count = self.get_mat_count_left(item_id)
                print("I have {} of {} and need to use {}".format(have_item_count, item_name, total_item_count))
                if have_item_count >= total_item_count:
                    self.used_items[item_id] += total_item_count
                else:
                    self.used_items[item_id] += have_item_count
                
                total_item_count = total_item_count - have_item_count
                left_over_count = 0
                if total_item_count < 0:
                    left_over_count = -1 * total_item_count
                    total_item_count = 0
                if only_needed and total_item_count == 0:
                    continue

            if isinstance(i['value'], LoadedRecipe):
                if sub_mat_count:
                    node_id = self.loaded_recipe_visit(i['value'], total_item_count, sub_mat_count)
                else:
                    node_id = self.loaded_recipe_visit(i['value'], i['count'], sub_mat_count)
            else:
                node_id = self.item_visit(i['value'])

            if sub_mat_count:
                print("{}, require amount: {}".format(item_name, total_item_count))
                label_info = " Require: " + str(total_item_count) + " left over: " + str(left_over_count)
            else:
                label_info = " " + str(i['count']) + "per" + " (" + str(total_item_count) + " total)"

            self.add_edge(node_id, parent_id, label_info)
        return parent_id

    def item_visit(self, item, count=1):
        tmp = get_item_info(item)
        if is_item_account_bound(item):
            color = "red"
        else:
            color = "blue"
        return self.add_node(tmp['name'], color=color)

class MinCostVisitor(GraphVisitor):
    use_owned_mats = False

    def gendot(self, recipe, graph_name='graph'):
        itd, cost, gain, ratio = self.visit(recipe)
        self._create_graph(graph_name)
        resultant_sell = cost
        return cost, gain, ratio

    def visit(self, loaded_recipe):
        self.used_items = defaultdict(int)
        self.item_cost = defaultdict(int)
        self.craft_items = defaultdict(int)
        self.buy_items = defaultdict(int)
        self.contrain_known = True

        return self.loaded_recipe_visit(loaded_recipe, 1, top=True)

    def get_mat_count_left(self, item_id):
        k = get_account_item_count(item_id)
        used_count = self.used_items[item_id]
        return max(k - used_count, 0)

    def loaded_recipe_visit(self, loaded_recipe, count, top=False):
        parent_id, my_item_cost, buy_price, my_buy_sell_ratio = self.item_visit(loaded_recipe.output_id, count)
        sub_crafting_cost = 0
        for i in loaded_recipe.input_info:
            if isinstance(i['value'], LoadedRecipe):
                item_id = i['value'].output_id
            else:
                item_id = i['value']
            
            item_name = get_item_info(item_id)['name']
            
            total_item_count = i['count'] * count

            have_item_count = self.get_mat_count_left(item_id)
            if have_item_count >= total_item_count:
                self.used_items[item_id] += total_item_count
            else:
                self.used_items[item_id] += have_item_count

            total_item_count = total_item_count - have_item_count
            if total_item_count < 0:
                total_item_count = 0

            if isinstance(i['value'], LoadedRecipe):
                node_id, sub_tree_cost, sub_buy_cost, buy_sell_ratio = self.loaded_recipe_visit(i['value'], total_item_count)
            else:
                node_id, sub_tree_cost, sub_buy_cost, buy_sell_ratio = self.item_visit(i['value'], total_item_count)

            label_info = str(i['count'])
            label_info += f" total: {total_item_count}"
            sub_crafting_cost += sub_tree_cost
            self.add_edge(node_id, parent_id, label=label_info)

        return parent_id, my_item_cost + sub_crafting_cost, buy_price, my_buy_sell_ratio
        
    def item_visit(self, item, count):
        tmp = get_item_info(item)
        item_name = tmp['name']
        cut_percentage = .1
        do_cut = False
        buy_price = get_item_max_buy_price(tmp['id'], do_cut, cut_percentage)
        sell_price = get_item_min_sell_price(tmp['id'])
        self.item_cost[tmp['id']] = sell_price

        l = f"{item_name}: Gross: {buy_price}"
        if do_cut:
            l += f"({cut_percentage})"
        l += f" Cost: {sell_price} total cost: {count * sell_price}"
        
        buy_sell_ratio = buy_price / sell_price

        return self.add_node(l), count * sell_price, buy_price, buy_sell_ratio

if __name__ == "__main__":
    pass
