from data_gathering import get_recipe_info, get_item_max_buy_price, get_item_min_sell_price, get_item_info

from pprint import pprint
import os
import json

class Item():
    def __init__(self, id):
        self.item_id = id
        self.name = None
        self.recipe_id = 0
        self._load()

    def save(self):
        with open('items/{}'.format(self.item_id), 'w') as writer:
            writer.write(json.dumps({'id' : self.item_id,
                                     'name' : self.name,
                                     'recipe_id' : self.recipe_id}))

    def _load(self):
        if not os.path.isdir('items'):
            os.makedirs('items')

        if os.path.isfile('items/{}'.format(self.item_id)):
            with open('items/{}'.format(self.item_id), 'r') as reader:
               item_info = json.loads(reader.read())
        else:
            item_info = get_item_info(self.item_id)
            item_info['recipe_id'] = 0

            with open('items/{}'.format(self.item_id), 'w') as writer:
                writer.write(json.dumps(item_info))

        if item_info:
            self.item_id = item_info['id']
            self.name = item_info['name']
            self.recipe_id = item_info['recipe_id']

        #pprint(item_info)
    def __str__(self):
        return self.name


class Recipe():
    def __init__(self, id):
        self.recipe_id = id
        self.output_id = 0
        self.input_info = []
        self.mhload()

    def mhload(self):
        if not os.path.isdir('recipes'):
            os.makedirs('recipes')
        
        if os.path.isfile('recipes/{}'.format(self.recipe_id)):
            with open('recipes/{}'.format(self.recipe_id), 'r') as reader:
                recipe_info = json.loads(reader.read())
        else:
            recipe_info = get_recipe_info(self.recipe_id)
            
            with open('recipes/{}'.format(self.recipe_id), 'w') as writer:
                writer.write(json.dumps(recipe_info))

        if recipe_info:
            self.output_id = recipe_info['output_item_id']
            self.input_info = recipe_info['ingredients']

    def __str__(self):
        val = "RECIPE\n"
        val += "\tOutput Id: {}\n".format(self.output_id)
        return val


