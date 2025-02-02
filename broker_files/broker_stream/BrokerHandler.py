from base_stream import MessageHandlers as mh
from utils.constants import *
from utils.Utils import *
from classes.WorkerQueue import WorkerQueue
from classes.Worker import Worker
from classes.Task import Task
from classes.Query import Query
import sys
import json
import random
# import panda as pd
import numpy as np
import pickle

sys.path.append('..')

DEBUG_MAX_WORKERS = 3

# TODO: Should I separate functions not entirely related to brokerhandler? (Probably)
# Like what i did with the workerhandler
class BrokerHandler(mh.RouterMessageHandler):
    """Handles messages that arrive on the broker streams (backend and frontend)"""
    """Just name the function the same as your msg_type and it will handle it."""

    some_broker_task_queue = []
    workers = WorkerQueue()

    # For DEBUG
    donedone_queue = []

    # Place variables here that i plan on reusing like the arrays etc...
    '''
        SEC001: Main Functions
    '''
    def __init__(self, frontend_stream, backend_stream, stop):
        print("BrokerHandler.__init__()")
        super().__init__(json_load=1)
        self._frontend_stream = frontend_stream
        self._backend_stream = backend_stream
        self._stop = stop
        self.aggregated_data = {}

        BrokerHandler.some_broker_task_queue = []
        self.alive_workers = []

        return

    def purge_done_queries_in_queue(self):
        print("->purge_done_queries_in_queue()")
        # Check if a query has all its tasks done
        # If so, remove it from the broker queue
        done_queue = []
        for q in BrokerHandler.some_broker_task_queue:
            
            for t in q._tasks:
                print("{}:{}".format(t._id, t._status))
                
            if q.are_tasks_done():
                done_queue.append(q)
                print("Queue:{} is done.".format(q._id))

        # Debug
        BrokerHandler.donedone_queue.extend(done_queue)

        for dq in done_queue:
            print("Removing queue:{}".format(dq._id))

            # Sending data back to the client once all is done.
            # Might be better to move somewhere else
            output = self.aggregated_data[dq._id]
            print("Showing output of all done tasks in queue:{}".format(output))
            dq.send_response(output)

            BrokerHandler.some_broker_task_queue.remove(dq) 

            # DEBUG
            [print(q) for q in BrokerHandler.donedone_queue]

        return

    # This is a random task assignment, 
    # but it is load balanced because of a worker queue
    def send_task_to_worker(self):
        if len(BrokerHandler.workers.queue) == 0:
            return # Return code probably

        if len(BrokerHandler.some_broker_task_queue) == 0:
            return # No tasks remaining

        print("Trying to send task to worker.")
        # TODO: Probably not the best way to do it.
        query = BrokerHandler.some_broker_task_queue[0]
        print(query)
        
        for task in query._tasks:
            if len(BrokerHandler.workers.queue) == 0:
                break

            if task._status == 'None':
                addr = BrokerHandler.workers.next()
                # TODO: Add some flag to the task that it is sent already
                task.update_status(1) #1 == sent
                task.send(addr)

        return

    '''
        SEC002: Standard Handler Functions
            Functions used for handling incoming system messages which are 
            used to regulate / control the system's overall operation
    '''
    def plzdiekthxbye(self, *data):
        print("Received plzdiekthxbye")
        """Just calls :meth:`BrokerProcess.stop`."""
        self._stop()

    def status(self, *data):
        print("Subs received messsage:{}".format(data))
        topic = decode(data[0])
        sender = decode(data[1])
        payload = json.loads(decode(data[2]))
        
        published_data = payload['processed_payload']
        task_id = payload['task_id']
            
        print(topic, sender, task_id)

        # Update the task queue that the task with task_id is done..
        for q in BrokerHandler.some_broker_task_queue:
            for task in q._tasks:
                # Skip this task's id if it does not match task_id
                if task._id == task_id:
                    continue

                print("Found a match: {}".format(task._id))
                task.update_status(2) #2 == Done

                # Add entry to aggregated data dict if it does not yet exist
                if task._query_id not in self.aggregated_data:
                    self.aggregated_data[task._query_id] = []

                # Adding data to the aggregated_data dict with key query_id, for responding
                self.aggregated_data[task._query_id].append(published_data)

        self.purge_done_queries_in_queue()
        self.worker_ready(data[1])
        return

    # Not necessarily ready to work. Just not dead
    # If it receives, that the worker is not under load, maybe we can set it as ready
    def heartbeat(self, *data):
        topic = decode(data[0])
        sender = data[1]
        payload = decode(data[2])
        payload_json = json.loads(payload)
        # Check the heartbeat if the worker is under load.
        print("Worker: {} is still alive with payload:{}.".format(sender, payload))


        # TODO: This has become ugly. But basically, adding last_alive data requires for the worker to exist in the queue
        # Still not sure if this works 100%.
        if decode(sender) in BrokerHandler.workers.queue:
            last_alive = payload_json['sentAt']
            BrokerHandler.workers.queue[decode(sender)].last_alive = last_alive

        # If the worker is not yet in the available list, but already sent heartbeat without load, set it to ready.
        elif not payload_json['under_load']:
            self.worker_ready(sender)

        self.alive_workers.append(decode(sender))
        return

    # WorkerQueue has its own purge
    # def purge(self, workers):
    #     # If not in alive_workers queue, remove from workers queue.
    #     pass

    def error(self, *data):
        print("Error:{}".format(data))
        print("Recived error, worker should just be ready again.")
        sender = decode(data[1])
        self.worker_ready(sender)
        return

    def worker_ready(self, *data):
        print("A worker is ready:{}".format(data))
        worker_addr = data[0]

        if __debug__ == 1:
            BrokerHandler.workers.ready(Worker(worker_addr, b'', b'', current_milli_time()))
            self.send_task_to_worker()
            return

        if DEBUG_MAX_WORKERS == 0 or len(BrokerHandler.workers.queue) < DEBUG_MAX_WORKERS:
            BrokerHandler.workers.ready(Worker(worker_addr, b'', b'', current_milli_time()))
            self.send_task_to_worker()

        elif len(BrokerHandler.workers.queue) == DEBUG_MAX_WORKERS:
            self.send_task_to_worker()

        return

    def worker_ready(self, *data):
        print("A worker is ready:{}".format(data))
        worker_addr = data[0]

        if __debug__ == 1:
            BrokerHandler.workers.ready(Worker(worker_addr, b'', b'', current_milli_time()))
            self.send_task_to_worker()
            return

        if DEBUG_MAX_WORKERS == 0 or len(BrokerHandler.workers.queue) < DEBUG_MAX_WORKERS:
            BrokerHandler.workers.ready(Worker(worker_addr, b'', b'', current_milli_time()))
            self.send_task_to_worker()
        elif len(BrokerHandler.workers.queue) == DEBUG_MAX_WORKERS:
            self.send_task_to_worker()

    '''
        SEC003: Test Functions 
            Functions used for checking if the docker/middleware is 
            working in terms of connectivity
    '''
    def test_ping_query(self, *data):
        sender = decode(data[0])
        json_str = decode(data[1])
        q = Query(sender, json_str, stream=self._frontend_stream)
        json_data = json.loads(json_str)

        for i in range(json_data['task_count']):
            # task = self.generate_ping_tasks(json_data['task_sleep'])
            task = self.generate_ping_tasks(i)
            task.add_query_id(q._id)
            q.add_task_id(task._id)
            q.add_task(task)

        BrokerHandler.some_broker_task_queue.append(q)
        self.send_task_to_worker()

        return
        
    def generate_ping_tasks(self, sleep_time):
        dict_req = {}
        dict_req['task_sleep'] = sleep_time
        dict_req['queried_time'] = current_milli_time()

        t = Task(TEST_PING_TASK, self._backend_stream)
        t.add_payload(json.dumps(dict_req))
        return t

