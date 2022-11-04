import pulsectl

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
    return "🎧️\n" + sink.description.split()[0]

  def next_default_sink(self):
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

