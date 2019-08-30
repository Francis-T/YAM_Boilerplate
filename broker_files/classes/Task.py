from utils.Utils import *
import numpy as np
import uuid

class Task(object):
    status_arr = ['None', 'Sent', 'Done', 'Error']
    # Generate id automatically
    def __init__(self, task_type, socket):
        self.payload = []
        self._id = str(uuid.uuid4())
        self._task_type = task_type
        self._socket = socket
        self._payload_count = 0
        self._status = Task.status_arr[0]
        return

    # TODO: This send method should probably in a different place
    # Payload:
    '''
    [0] = Address
    # This is consumed by the Handlers
    [1] = Task type
    [2] = Task ID
    [3] = Payload Count
    # Determined by payload count
    [4] = Payload type
    [5] = Payload
    [6] = Payload type
    [7] = Payload ....
    '''
    def send(self, address):
        payload_to_send = []

        # Get the address, but check if we have to encode it first
        encoded_address = None
        if isinstance(address, bytes):
            encoded_address = address
        else:
            encoded_address = encode(address)

        payload_to_send.append(encoded_address)

        print("Task.send: ", self._task_type)
        payload_to_send.append(encode(self._task_type))
        payload_to_send.append(encode(self._id))
        payload_to_send.append(encode(str(self._payload_count)))
        # Extend because payload is also a list. (i dont know why, probably shouldnt be one)
        payload_to_send.extend(self.payload)
        self._socket.send_multipart(payload_to_send)

        return

    def add_payload(self, data):
        self._payload_count += 1
        if __debug__ == 0:
            print("Add_payload of type:{}".format(type(data)))

        if isinstance(data, np.ndarray):
            self.payload.append(b"ZippedPickleNdArray")
            self.payload.append(zip_and_pickle(data))

        elif isinstance(data, bytes):
            self.payload.append(b"Bytes")
            self.payload.append(data)

        elif isinstance(data, str):
            self.payload.append(b"String")
            self.payload.append(encode(data))

        else:
            self._payload_count -= 1

        return

    def update_status(self, new_status):
        self._status = Task.status_arr[new_status]
        return

    def deconstruct_payload(self):
        # TODO?
        return

    def add_query_id(self, query_id):
        self._query_id = query_id
        return

