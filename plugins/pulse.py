import pulsectl
import re


class Pulse(object):

  def __init__(self):
    self.pulse = pulsectl.Pulse('snakedeck')

  def get_mic_muted(self, mic_name):
    mic_states = [m.mute for m in self.pulse.source_list() if mic_name in m.name]
    if len(mic_states)==0:
      return f"{mic_name}\n🎤🚫"
    if all(mic_states):
      return f"{mic_name}\n🎤🔴"
    elif any(mic_states):
      return f"{mic_name}\n🎤🟠"
    else:
      return f"{mic_name}\n🎤🟢"

  def set_mic_muted(self, mic_name, muted):
    for source in self.pulse.source_list():
      if mic_name in source.name:
        self.pulse.source_mute(source.index, mute=muted)

  def get_default_sink(self):
    sink = self.pulse.get_sink_by_name(self.pulse.server_info().default_sink_name)
    card = [ card for card in self.pulse.card_list() if card.index==sink.card ][0]
    hdmi_ports = re.findall(".* Stereo \((.*)\) Output", card.profile_active.description)
    if hdmi_ports:
      extra_port_info = hdmi_ports[0]
      if extra_port_info == "HDMI":
        extra_port_info = "HDMI 1"
      extra_port_info = "\n" + extra_port_info
    else:
      extra_port_info = ""
    return "🎧️\n" + sink.description.split()[0] + extra_port_info

  def next_default_sink(self):
    sink = self.pulse.get_sink_by_name(self.pulse.server_info().default_sink_name)
    card = [ card for card in self.pulse.card_list() if card.index==sink.card ][0]
    hdmi_profiles = [ p for p in card.profile_list if p.available and p.name.startswith("output:hdmi-stereo") ]
    if hdmi_profiles:
      active_profile_index = [ p.name for p in hdmi_profiles].index(card.profile_active.name)
      active_profile_index += 1
      if active_profile_index < len(hdmi_profiles):
        self.pulse.card_profile_set(card, hdmi_profiles[active_profile_index])
        return
      self.pulse.card_profile_set(card, card.profile_list[0])
    current_sink_name = self.pulse.server_info().default_sink_name
    sink_list = self.pulse.sink_list()
    next_sink = sink_list[-1]
    for sink in sink_list:
      if sink.name==current_sink_name:
        break
      next_sink = sink
    self.pulse.sink_default_set(next_sink)


def snakedeck_plugin():
  return Pulse()

