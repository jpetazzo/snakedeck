#!/usr/bin/env python

import json
import logging
import websocket
import sys

from obswebsocket import obsws, requests  # noqa: E402
from obswebsocket.exceptions import ConnectionFailure

host = "localhost"
port = 4444

def obs_connect():
  # Manual connection
  # (there seems to be an issue with password auth;
  # this might be specific to OBS 24 since it worked
  # fine on OBS 25 on Arch)
  try:
    ws = obsws(host, port)
    ws.ws = websocket.WebSocket()
    ws.ws.connect("ws://{}:{}".format(host, port))
    ws._run_threads()
    return ws
  except ConnectionRefusedError:
    logging.warning("Could not connect to OBS. Is it running and accepting WebSocket connections?")
  except:
    logging.exception("Could not connect to OBS.")

ws = obs_connect()

def call(func, *args, **kwargs):
  global ws
  if ws is None:
    ws = obs_connect()
  if ws is not None:
    try:
      req = ws.call(getattr(requests, func)(*args, **kwargs))
      return req.datain
    except:
      ws = None
      raise

def noretcall(func, *args, **kwargs):
  call(func, *args, **kwargs)

def snakedeck_plugin():
  # Snakedeck uses the return value to update the key.
  # We don't want to update OBS shortcut keys when they are pressed.
  # So we force an empty return value.
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
    for func in dir(requests):
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

