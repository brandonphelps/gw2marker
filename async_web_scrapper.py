from tester_idea import gw2_endpoints, bundle_apis, EndPoint, RequestHandler, Uri, gw2_base

import itertools
import random
import asyncio
import logging
import re
import sys
from typing import IO
import urllib.error
import urllib.parse

import aiofiles
import aiohttp
import time

from aiohttp import ClientSession


logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr)

logger = logging.getLogger("areq")
logging.getLogger("chardet.charsetprober").disabled = True

HREF_RE = re.compile(r'href="(.*?)"')



async def fetch_html(url, session, **kwargs):
    logger.info(f"fetch html {url}")
    time.sleep(1)
    resp = await session.request(method="GET", url=url, **kwargs)
    resp.raise_for_status()
    logger.info(f"got response {resp.status} for url: {url}")
    html = await resp.text()
    return html



    


async def main():
    async with ClientSession() as session:
        tasks = []
        for url in map(lambda x: x.uri, gw2_endpoints):
            print(f"adding task for url: {url}")
            tasks.append(fetch_html(url, session))
        await asyncio.gather(*tasks)


async def queue_manager(name, q):
    while True:
        queue_group = random.randint(0, 10)
        print(f"Queue group of size {queue_group}")
        items_to_handle = []
        for _ in range(queue_group):
            r = await q.get()
            items_to_handle.append(r)
            q.task_done()
        summation_value = sum(items_to_handle)
        print(f"New summation over {queue_group} elements is {summation_value}")

async def makeitem(max_v=10):
    return random.randint(0, max_v)

async def randsleep(a=0, b=10,caller=None):
    i = random.randint(a, b)
    if caller:
        print(f"{caller} sleeping for {i} seconds.")
    await asyncio.sleep(i)

async def producers(name, q):
    n = random.randint(0, 10)
    for _ in itertools.repeat(None, n):
        await randsleep()
        i = await makeitem()
        r = await q.put(i)
        print(f"Producer {name} added <{i}> to queue.")
        print(f"producer {r}")

async def q_main():
    inbox = asyncio.Queue()
    
    p = [asyncio.create_task(producers(f"bob_{i}", inbox)) for i in range(10)]
    que_man = asyncio.create_task(queue_manager('Queueman', inbox))

    await asyncio.gather(*p)
    await inbox.join()
    que_man.cancel()

def mark_done(future):
    future.set_result(f'all done {random.randint(0, 10)}')
    

async def f_main():
    all_done = asyncio.Future()
    
    r = await mark_done(all_done)


if __name__ == "__main__":

    #import pathlib
    

