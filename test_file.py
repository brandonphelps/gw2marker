import asyncio
import random
import itertools
import time


async def count():
    r = random.randint(0, 10)
    c = 0 
    print(f"one: {r}")
    c += r
    await asyncio.sleep(r)
    print("two")
    return c




async def makerandom(idx, threshold = 6):
    print(f'initial random: {idx}, threshold of {threshold}')
    i = random.randint(0, 10)
    while i <= threshold:
        print(f"makerandom({idx}) == {i}, retrying")
        await asyncio.sleep(idx + 1)
        i = random.randint(0, 10)
    
    print(f"Finishing with randomness({idx}) == {i}")
    return i

async def makeitem(max_v=10):
    return random.randint(0, max_v)


async def randsleep(a=1, b=5, caller=None):
    i = random.randint(0, 10)
    if caller:
        print(f"{caller} sleeping for {i} seconds.")
    await asyncio.sleep(i)

async def produce(name, q):
    n = random.randint(0, 10)
    for _ in itertools.repeat(None, n):
        await randsleep(caller=f"Producer {name}")
        i = await makeitem()
        t = time.perf_counter()
        await q.put((i, t))
        print(f"Producer {name} added <{i}> to queue.")


async def consume(name, q):
    while True:

        await randsleep(caller=f"Consumer {name}")
        i, t = await q.get()
        now = time.pref_counter()
        print(f"Consumer {name} got element <{i}>"
              f" in {now-t:0.5f} seconds.")
        q.task_done()

async def main():
    rest = await asyncio.gather(*(makerandom(i, 10 - i - 1) for i in range(3, 10)))
    return rest


async def main_q(nprod, ncon):
    q = asyncio.Queue()
    producers = [asyncio.create_task(produce(n, q)) for n in range(nprod)]
    consumers = [asyncio.create_task(consume(n, q)) for n in range(ncon)]
    
    await asyncio.gather(*producers)
    await q.join()
    for c in consumers:
        c.cancel()

def my_cool_func(x):
    t = (x + 4, x*4 + 4)
    print(t)
    time.sleep(random.randint(*t))
    return x*2 + x-3 + x*x


async def get_value(x):
    return my_cool_func(x)

async def main_func():
    inbox = asyncio.Queue()
    outbox = asyncio.Queue()

    te = await asyncio.gather(get_value(1),
                              get_value(2),
                              get_value(3),
                              get_value(4))
    return te
                         

if __name__ == "__main__":
    # asyncio.run(main_q(3, 4))
    #for i in range(1, 30):
    #    print(get_value(i))
    print(asyncio.run(main_func()))
    
