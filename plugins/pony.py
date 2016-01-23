import requests

from cloudbot import hook

## deref implementation
SENTRY = object()

def deref(delay):
    print(delay)
    f, value = delay
    if value is not SENTRY:
        return value
    else:
        delay[1] = f()
        return delay[1]

def new_delay(f):
    return [f, SENTRY]

def retry(delay):
    delay[1] = delay[0]()

## fetching
FAILED = object()

def fetch(url, *args):
    def f():
        try:
            json = requests.get(url, *args).json()
        except Exception:
            return FAILED
        if json is None:
            return FAILED
        else:
            return json
    return f

## as a FSM

RETRIES = 3
HOST = "http://derpiboo.ru/"
URL = "{0}images.json".format(HOST)

global_state = (0, RETRIES, new_delay(fetch(URL)), 1)

def user_request(state):
    res = state[2]
    json = deref(res)
    if json is FAILED:
        return on_failure(state)
    else:
        return on_success(state, json)

def on_success(state, json):
    index, retries, res, page = state
    images = json["images"]
    try:
        image = images[state[0]]
    except IndexError:
        params = {}
        params["page"] = page
        return user_request((0, retries, fetch(URL, params), page + 1))
    return (done(image["id"]), (index + 1, min(retries + 1, RETRIES), res, page))

def on_failure(state):
    index, retries, res, page = state
    if retries == 0:
        return ("Failed to fetch image", state)
    else:
        return user_request((index, retries - 1, res))

def done(iid):
    return "{0}{1}".format(HOST, iid)

@hook.command("pony", "cute", autohelp=False)
def pony2():
    '''Gets a random image from derpiboo.ru'''
    res, new_state = user_request(global_state)
    global global_state
    global_state = new_state
    return res
