import hashlib
import os
import json
import time

cached_folder = 'requests_cache'

def cache_data(condi_funct=None, *condi_args, **condi_kwargs):
    def wrapper(func):
        def inner(*args, **kwargs):
            full_path = get_hash_folder(func, args, kwargs)
            if os.path.isfile(full_path):
                if condi_funct and condi_funct(*condi_args, **condi_kwargs):
                    print("Recomputing: {}({})".format(func.__name__, args))
                    val = func(*args, **kwargs)
                else:
                    with open(full_path, 'r') as reader:
                        val = json.loads(reader.read())
            else:
                print("First Computing: {}({})".format(func.__name__, args))
                val = func(*args, **kwargs)
                with open(full_path, 'w') as writer:
                    writer.write(json.dumps(val))
            return val
        return inner
    return wrapper

#todo: figure out if the cache_data function can be used in this function
#        or see if there is some common code that could be grouped 
def timed_cache_data(timeout):
    def wrapper(func):
        def inner(*args, **kwargs):
            inter_folder = func.__name__
            m = hashlib.sha256()
            for i in args:
                m.update(str(i).encode('utf-8'))
            full_path = os.path.join(cached_folder, inter_folder, m.hexdigest())

            if not os.path.isdir(os.path.dirname(full_path)):
                os.makedirs(os.path.dirname(full_path))

            #print("filename: {}".format(full_path))
            #print("Current time: {}".format(time.time()))
            # TODO: just lazy, but do a function for writing so it shared, 
            if os.path.isfile(full_path):
                if os.path.getmtime(full_path) + timeout <= time.time():
                    print("Recomputing: {}({})".format(func.__name__, args))
                    val = func(*args, **kwargs)
                    with open(full_path, 'w') as writer:
                        writer.write(json.dumps(val))
                else:
                    with open(full_path, 'r') as reader:
                        val = json.loads(reader.read())
            else:
                print("First Computing: {}({})".format(func.__name__, args))
                val = func(*args, **kwargs)
                with open(full_path, 'w') as writer:
                    writer.write(json.dumps(val))
            return val
        return inner
    return wrapper

def get_hash_folder(func, args=None, kwargs=None):
    inter_folder = func.__name__
    if args is None:
        args = []
    if kwargs is None:
        kwargs = []

    m = hashlib.sha256()
    for i in args:
        m.update(str(i).encode('utf-8'))
    full_path = os.path.join(cached_folder, inter_folder, m.hexdigest())

    if not os.path.isdir(os.path.dirname(full_path)):
        os.makedirs(os.path.dirname(full_path))
    return full_path

