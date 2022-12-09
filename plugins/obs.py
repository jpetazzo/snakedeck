#!/usr/bin/env python

import json
import sys

import obsws_python.reqs

host = "localhost"
port = 4455
password = "sesame"
ws = None


def obs_connect():
  return obsws_python.reqs.ReqClient(host=host, port=port, password=password)


def call(func, *args, **kwargs):
  global ws
  if ws is None:
    ws = obs_connect()
  if ws is not None:
    try:
      response = getattr(ws, func)(*args, **kwargs)
      if hasattr(response, "attrs"):
        retval = dict([(k, getattr(response, k)) for k in response.attrs()])
        return retval
      else:
        return
    except:
      ws = None
      raise


def noretcall(func, *args, **kwargs):
  call(func, *args, **kwargs)


# Snakedeck uses the return value to update the key.
# We don't want to update OBS shortcut keys when they are pressed.
# So we force an empty return value.
def snakedeck_plugin():
  return noretcall


if __name__ == "__main__":
  if len(sys.argv) == 1:
    print("""
You can invoke this plugin from the command line to explore the OBS
WebSocket API. You can pass a function call to invoke as a parameter,
like this:

    GetSceneList
    SetCurrentScene <name>

You can also specify '?' to show available functions, or ?Scene to show
all functions containing Scene.

If an argument contains = it will be passed as a kwarg, and the right
hand side should be JSON.
""")
    exit()

  if sys.argv[1].startswith('?'):
    search = sys.argv[1][1:]
    for func in dir(obsws_python.reqs.ReqClient):
      if func[0] == '_':
        continue
      if search in func:
        print(func)
    exit()

  args = []
  kwargs = {}

  for a in sys.argv[2:]:
    if '=' in a:
      k, v = a.split('=', 1)
      v = json.loads(v)
      kwargs[k] = v
    else:
      args.append(a)

  ret = call(sys.argv[1], *args, **kwargs)
  print(json.dumps(ret))
