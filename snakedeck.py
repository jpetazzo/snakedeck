#!/usr/bin/env python

import json
import logging
import os
import requests
import socket
import struct
import subprocess
import time
import threading
import unicodedata
import yaml

from PIL import Image, ImageDraw, ImageFont, ImageOps
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from StreamDeck.Transport.Transport import TransportError


logging.basicConfig(level=logging.DEBUG)


# Set a couple of directory paths for later use.
# This follows the spec at the following address:
# https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
if not xdg_config_home:
  xdg_config_home = os.path.join(os.environ.get("HOME"), ".config")
config_dir = os.path.join(xdg_config_home, "snakedeck")

xdg_state_home = os.environ.get("XDG_STATE_HOME")
if not xdg_state_home:
  xdg_state_home = os.path.join(os.environ.get("HOME"), ".local", "state")
state_dir = os.path.join(xdg_state_home, "snakedeck")

import plugins.countdowns
countdowns = plugins.countdowns.snakedeck_plugin(state_dir)

import plugins.obs
obs = plugins.obs.snakedeck_plugin()

import plugins.lights
lights = plugins.lights.snakedeck_plugin()

import plugins.pulse
pulse = plugins.pulse.snakedeck_plugin()

import plugins.alsa
alsa = plugins.alsa.snakedeck_plugin()

# Associates deck id to deck
decks = {}


# FIXME: detect if these fonts are missing?
text_font = ImageFont.truetype("DroidSans", 20)
emoji_font = ImageFont.truetype("NotoColorEmoji", 109, layout_engine=ImageFont.Layout.RAQM)
interline = 8


sync_address = "224.0.19.4"
sync_port = 19004
sync_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sync_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sync_socket.bind(("0.0.0.0", sync_port))
sync_address_as_bytes = socket.inet_aton(sync_address)
sync_sockopt = struct.pack('4sL', sync_address_as_bytes, socket.INADDR_ANY)
sync_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, sync_sockopt)


deviceManager = DeviceManager()


def detect_decks():
  # First, let's check if any deck was disconnected.
  # Get a list of serials so that we don't change the dict while we iterate on it.
  deck_ids = list(decks)
  for deck_id in deck_ids:
    if not decks[deck_id].deck.connected():
      logging.warning(f"Deck {deck_id} ({decks[deck_id].serial_number}) was disconnected.")
      del decks[deck_id]
  # OK, now let's check if new decks are detected.
  for deck in deviceManager.enumerate():
    # Skip non-visual devices.
    if not deck.is_visual():
      continue
    deck_id = deck.id()
    if deck_id not in decks:
      logging.info(f"Deck {deck_id} was detected.")
      decks[deck_id] = Deck(deck)


def update_decks():
  for deck_id, deck in decks.items():
    for key_number in deck.keys:
      try:
        key = deck.keys[key_number]
        if "timer" in key:
          timer = key["timer"]
          interval = timer.get("interval", 1)
          deadline = timer.get("deadline", 0)
          if deadline > time.time():
            continue
          timer["deadline"] = time.time() + interval
          if "label" in timer:
            key["label"] = eval(timer["label"])
          if "emoji" in timer:
            key["emoji"] = eval(timer["emoji"])
          try:
            deck.update_key(key_number, key)
          except TransportError:
            logging.warning(f"Deck {deck_id} ({decks[deck_id].serial_number}) might have been disconnected.")
            del decks[deck_id]
            return
        if "sync" in key:
          actor = key.get("actor")
          if actor == deck.serial_number:
            data_as_bytes = bytes(json.dumps(key), "utf-8")
            sync_socket.sendto(data_as_bytes, (sync_address, sync_port))
      except:
        logging.exception(f"Exception while updating key {key_number} on deck {deck_id}:")


def sync_receiver():
  while True:
    try:
      data_as_bytes = sync_socket.recv(1024)
      if len(data_as_bytes) > 1023:
        logging.warning("Packet too long, discarding.")
        continue
      data = json.loads(data_as_bytes.decode("utf-8"))
      sync = data["sync"]
      for deck in decks.values():
        for key_number, key in deck.keys.items():
          if key.get("sync") == sync and data.get("serial", 1) > key.get("serial", 0):
            key.update(data)
            deck.update_key(key_number, key)
    except:
      logging.exception("Error while receiving sync packet.")


def loop_decks():
  while True:
    try:
      detect_decks()
      update_decks()
    except:
      logging.exception("Error in main loop.")
    time.sleep(1)


class Deck(object):

  def __init__(self, deck):
    self.deck = deck
    self.keys = {}
    self.config_timestamp = None
    logging.debug(f"Opening deck {deck.id()}.")
    self.deck.open()
    self.serial_number = self.deck.get_serial_number()
    logging.debug(f"Deck {deck.id()} is a {self.deck.DECK_TYPE}, serial number {self.serial_number}.")
    self.clear()
    self.image_size = self.deck.key_image_format()['size']
    logging.debug(f"Deck {self.serial_number} image size is {self.image_size}.")
    self.config_file_path = os.path.join(config_dir, self.serial_number + ".yaml")
    self.load_config()
    threading.Thread(target=self.watch_config).start()
    self.deck.set_key_callback(self.callback)

  def callback(self, deck, key_number, state):
    pressed_or_released = "pressed" if state else "released"
    logging.debug(f"Deck {self.serial_number} key {key_number} is now {pressed_or_released}.")
    try:
      key = self.keys[key_number]
      logging.debug(f"key={key}")
      if state and "shell" in key:
        command = key["shell"]
        kwargs = {"shell": True}
        if "cd" in key:
          kwargs["cwd"] = key["cd"]
        ret = subprocess.call(command, **kwargs)
        if ret != 0:
          logging.warning(f"Command {command!r} exited with non-zero status code.")
      if state and "eval" in key:
        retval = eval(key["eval"])
        if retval is not None:
          key.update(retval)
          self.update_key(key_number, key)
      if state and "cycle" in key:
        key["cycle"].append(key["cycle"].pop(0))
        key["actor"] = self.serial_number
        key["serial"] = key.get("serial", 0) + 1
        self.update_key(key_number, key)
    except Exception as e:
      logging.exception(f"Deck {self.serial_number} key {key_number} caused exception {e}:")

  def clear(self):
    # Clear all keys
    self.deck.reset()
    for key in range(self.deck.KEY_COUNT):
      self.deck.set_key_image(key, self.deck.BLANK_KEY_IMAGE)
    self.deck.set_brightness(80)
    self.keys.clear()

  def load_config(self):
    if not os.path.isfile(self.config_file_path):
      logging.warning(f"Deck {self.serial_number} has no configuration file ({self.config_file_path}).")
      return
    self.config_timestamp = os.stat(self.config_file_path).st_mtime
    config = yaml.safe_load(open(self.config_file_path))
    for key in config:
      if "line" in key and "column" in key:
        # FIXME validate line/column
        key_number = (key["line"] - 1) * self.deck.KEY_COLS + key["column"] - 1
        self.update_key(key_number, key)
      else:
        if "PATH" in key:
          os.environ["PATH"] = key["PATH"] + ":" + os.environ["PATH"]
        if "eval" in key:
          eval(key["eval"])


  def update_key(self, key_number, key):
    self.keys[key_number] = key
    if "cycle" in key:
      key.update(key["cycle"][0])
    if "label" in key:
      lines = key["label"].split("\n")
      images = []
      for line in lines:
        if not line:
          continue
        # Figure out if that line is text or emoji
        if unicodedata.category(line[0])=="So":
          font = emoji_font
          kwargs = dict(embedded_color=True, fill="white")
        else:
          font = text_font
          kwargs = dict()
        line_size = font.getbbox(line)[2:4]
        image = Image.new("RGB", line_size)
        draw = ImageDraw.Draw(image)
        draw.text((0,0), line, font=font, **kwargs)
        # If the resulting image is too wide, scale it down
        if image.width > self.image_size[0]:
          image = ImageOps.scale(image, self.image_size[0]/image.width)
        images.append(image)
      image_width = max(i.width for i in images)
      image_heigth = sum(i.height for i in images) + interline*(len(images)-1)
      image = Image.new("RGB", (image_width, image_heigth))
      y = 0
      for i in images:
        x = (image_width - i.width) // 2
        image.paste(i, (x, y))
        y += i.height + interline
      scaled_image = PILHelper.create_scaled_image(self.deck, image, margins=[4, 4, 4, 4])
      deck_image = PILHelper.to_native_format(self.deck, scaled_image)
      self.deck.set_key_image(key_number, deck_image)

  def watch_config(self):
    while True:
      time.sleep(1)
      if os.path.isfile(self.config_file_path):
        if os.stat(self.config_file_path).st_mtime > self.config_timestamp:
          logging.info(f"Configuration file for deck {self.serial_number} changed, reloading it.")
          self.clear()
          self.load_config()


threading.Thread(target=loop_decks).start()
#threading.Thread(target=sync_receiver).start()


for t in threading.enumerate():
  if t is threading.currentThread():
    continue

  if t.is_alive():
    try:
      t.join()
    except KeyboardInterrupt:
      os._exit(0)
