

import peewee

from secrets import SQLITE_DB_PATH

db = peewee.SqliteDatabase(SQLITE_DB_PATH)



class BaseModel(peewee.Model):
    class Meta:
        database = db


# both of these are mapping between ids and names
# will be used to go from item id to recipe id, via name
class Item(BaseModel):
    output_id = peewee.CharField()
    recipe_id = peewee.CharField(default=0)

class Recipe(BaseModel):
    output_id = peewee.CharField(default=0)

class PossibleCraftable(BaseModel):
    # the existence of id in this table indicates that this is
    # craftable by the player
    # each id corresponds to the recipe's id
    # we'll be computing the profit when creating the recipe, thus
    # the sale price of the output - (the cost of its inputs + listing fee)
    id = peewee.IntegerField()

def init_tables():
    try:
        db.create_tables([Item, PossibleCraftable])
    except peewee.OperationalError as e:
        print(e)



if __name__ == "__main__":
    init_tables()
