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
