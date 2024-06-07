import leglight
import logging

class Lights(object):

  def __init__(self):
    self.discover()

  def discover(self):
    logging.debug("Discovering lights...")
    self.lights = leglight.discover(3)
    logging.debug(f"Found {len(self.lights)} lights.")

  def add(self, address):
    for light in self.lights:
      if address == light.address:
        logging.info(f"Light {address} already exists; not adding it.")
        return
    logging.info(f"Light {address} didn't exist yet; adding it.")
    try:
        self.lights.append(leglight.LegLight(address, 9123))
    except:
        logging.exception(f"Error while adding light {address}.")

  def set(self, light_name, power=None, brightness=None, temperature=None):
    light_found = False
    for light in self.lights:
      if light.display == light_name:
        light_found = True
        if temperature is not None:
          light.color(temperature)
        if brightness is not None:
          light.brightness(brightness)
        if power is True:
          light.on()
        if power is False:
          light.off()
    if not light_found:
      logging.warning(f"Light {light_name} not found. Trying to rediscover lights.")
      self.discover()

  def set_all(self, all_lights):
    for light in self.lights:
      if light.display in all_lights:
        light.color(all_lights[light.display][1])
        light.brightness(all_lights[light.display][0])
        light.on()
      else:
        light.off()


def snakedeck_plugin():
  return Lights()
