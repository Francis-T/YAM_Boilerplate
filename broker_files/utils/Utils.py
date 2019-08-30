import time
import pickle
import blosc
import numpy as np
import os
import json
import datetime
from dateutil import tz

decode = lambda x: x.decode('utf-8')
current_milli_time = lambda: int(round(time.time() * 1000))

def encode(raw):
    if isinstance(raw, list):
        return zip_and_pickle(raw, protocol=2)
    elif isinstance(raw, str):
        return raw.encode('ascii')
    elif isinstance(raw, np.ndarray):
        return zip_and_pickle(raw)
    return None

def zip_and_pickle(obj, flags=0, protocol=-1):
    """pickle an object, and zip the pickle before sending it"""
    p = pickle.dumps(obj, protocol)
    z = blosc.compress(p, typesize=8)
    return z

def unpickle_and_unzip(pickled):
    unzipped = blosc.decompress(pickled)
    unpickld = pickle.loads(unzipped)
    return unpickld
    
# TODO: For some reason, the shuffle is not working? I thought it was inplace.
# This might cause too much memory use though. (most probably)
def split(a, n):
    # np.random.shuffle(a)
    a_ = a[np.random.permutation(a.shape[0])]
    k, m = divmod(len(a_), n)
    return (a_[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))

# TODO: Im lazy.
def delete_json_data(dir, filename, *keys):
    return

def read_json_data(dir, filename, *keys):
    if not os.path.exists(os.path.join(os.getcwd(), dir)):
        return None, False

    logs_dir = os.path.join(os.getcwd(), dir)
    logs_path = os.path.join(logs_dir, filename)
    if not os.path.exists(logs_path):
        return None, False

    with open(logs_path, "r") as jsonFile:
        data = json.load(jsonFile)
        out = {}
        for key in keys[0]:
            if key in data:
                out[key] = data[key]
    return out, True

def write_json_data(dir, filename, dict):
    if not os.path.exists(os.path.join(os.getcwd(), dir)):
        os.mkdir(os.path.join(os.path.join(os.getcwd(), dir)))
    logs_dir = os.path.join(os.getcwd(), dir)
    logs_path = os.path.join(logs_dir, filename)
    try:
        open(logs_path, 'r')
    except IOError:
        open(logs_path, 'w')

    # If file is empty
    if os.stat(logs_path).st_size == 0:
        with open(logs_path, "w") as myfile:
            json.dump(dict, myfile)

        return True

    with open(logs_path, "r+") as jsonFile:
        data = json.load(jsonFile)

        for k, v in dict.items():
            if k in data:
                tmp = data[k]
                data[k] = v
                jsonFile.seek(0)  # rewind
                json.dump(data, jsonFile)
                jsonFile.truncate()
                continue

            # Or you could issue an error here...
            data[k] = v
            jsonFile.seek(0)  # rewind
            json.dump(data, jsonFile)
            jsonFile.truncate()

    return True

    def convert_millis_to_strdatetime(millis, local=True):
        if isinstance(millis, str):
            millis = int(millis)

        if local:
            from_zone = tz.gettz('UTC')
            to_zone = tz.gettz('Asia/Tokyo')
            date = datetime.datetime.fromtimestamp(millis/1000.0)
            central = date.astimezone(to_zone)
            central = central.strftime('%Y-%m-%d %H:%M:%S')
            return central

        date = datetime.datetime.fromtimestamp(millis/1000.0)
        central = date.strftime('%Y-%m-%d %H:%M:%S')

        return central
