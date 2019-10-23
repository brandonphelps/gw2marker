



from tester_idea import Uri, EndPoint, RequestHandler, gw2_endpoints


from queue import Queue


import threading
import time
import random

queue_process_keep_running = True
request_handler = RequestHandler()

def queue_get(queue, num_items, block=True, timeout=None):
    """
    attempts to return num_items from the queue, allow for non blocking, which if the timeout is specified will return as many as items were available from the queue
    """
    if timeout is None:
        timeout = 0
    if num_items < 1:
        raise Exception("num items must be positive and greater than 0")
        
    results = []
    while len(results) < num_items:
        results.append(queue.get(block=block, timeout=timeout))
    return results

def queue_batcher_processor(queue):
    

def queue_processor(queue):
    while queue_process_keep_running:
        cur_job, future = queue.get()
        res = request_handler.get(cur_job)
        print(f"Setting result for job: {cur_job.uri}")
        future.set_results(res)
        r = random.randint(0, 10)
        time.sleep(r)

def random_api_getter(queue):
    results = []
    for i in range(10):
        job_to_do = random.choice(gw2_endpoints)
        print(f"URI put onto queue: {job_to_do.uri}")
        k = queue_up_api_call(job_to_do, queue)
        print(k.get_results())
        results.append(k)

    r = results.pop(0)
    while results:
        if r.get_results() is None:
            print(f"Waiting for updated results {len(results)}")
            time.sleep(1)
        else:
            print(f"Result!: {r.get_results()}")
            r = results.pop(0)

    print("finished")

class JobResults:
    def __init__(self):
        self._results = None
    def set_results(self, results):
        self._results = results
    def get_results(self):
        return self._results
    
def queue_up_api_call(EndPoint, queue):
    j = JobResults()
    queue.put((EndPoint, j), block=False)
    return j

if __name__ == "__main__":
    job_queue = Queue()
    
    threads = []
    for i in range(1):
        t = threading.Thread(target=queue_processor, args=(job_queue,))
        threads.append(t)
        t.start()
    for k in range(2):
        t = threading.Thread(target=random_api_getter, args=(job_queue,))
        threads.append(t)
        t.start()

    continue_waiting = True

    while continue_waiting:
        for j in threads:
            if j.is_alive():
               break
        else:
            continue_waiting = False
    queue_process_keep_running = False        
        


