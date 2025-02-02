# Yet another boiler plate for a middleware  
This was born out of spite from my stupid code that took me 3 hours just to add another 'service' to it.  

**Steps for the middleware testbed:** 
1. docker-compose up --build  
 
**In a separate terminal:**  
1. Git clone  
2. cd YAM_Boilerplate  
3. python3 -m venv venv    
4. pip install -r requirements.txt  
5. python main_prog.py  

Sample application:  

**Client**  
1. 'task_count' determines the number of tasks you want to generate.  
2. main_prog.py sends a query to the broker with the msg_type = 'test_ping_query'    

**Broker**  
3. The broker receives the message and executes the test_ping_query function  
4. Here the broker *generates the query object and task objects*  
5. Set **DEBUG_MAX_WORKERS** to 0, to be able to use all available workers (in this case 3)  
6. Broker sends the tasks to the available workers  

**Workers**  
7. Workers receive the tasks with the msg_type = 'test_ping_task'  
8. They perform some processing in the function: **test_ping_task** which is to just perform some wait  
9. They publish a message to the topic: **topic**, with the msg_type: **status**  

**Broker**  
10. Broker is subscribed to the topic and receives the payload  
11. It checks the task_id of the received payload and tries to find the corresponding task it has in the queue  
12. Updates the status of the task from *sent* to *done*  
13. It does this for all received messages  
14. At the same time, broker listens for heartbeats from the worker to see if they are still alive and purges if not  **(not yet implemented)**  

# Adding new services  
* For simple services, you only need to modify 3 main files.  
    1. WorkerHandler.py  
    2. BrokerHandler.py  
    3. main_prog.py  
* main_prog.py is the client, so you need to setup the query to send to the broker here, similar to the ping() process.  
* The **TEST_PING_QUERY** is the msg_type, so you need a corresponding function name in *BrokerHandler.py*  
* In BrokerHandler.py, you need to add the function name with the msg_type and then handle the payload being passed by the client.  
* Here you perform the **Query** and **Task** generations and you distribute it to the *Workers* depeding on the task scheduling algorithm you desire (not included)  
* In *WorkerHandler.py* again you must create the function with the same name as your msg_type you used in **generate_ping_tasks()**  
* This function performs necessary processing and publishes a message when done.  
* This is received by the *BrokerHandler.py* for aggregation.  

# References:  
Basic architecture of the boilerplate is based on this zmq tutorial:  
[Designing and testing pyzmq applications](https://stefan.sofa-rockers.org/2012/02/01/designing-and-testing-pyzmq-applications-part-1/)