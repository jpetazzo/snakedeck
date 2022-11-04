import alsaaudio

class Alsa(object):

  def get_mixer_by_name(self, name):
    for card_index in alsaaudio.card_indexes():
      short_name, long_name = alsaaudio.card_name(card_index)
      if name in short_name or name in long_name:
        return alsaaudio.Mixer("Mic", cardindex=card_index)

  def get_mic_muted(self, mic_name):
    mixer = self.get_mixer_by_name(mic_name)
    if mixer is None:
      return f"{mic_name}\n🎤🚫"
    rec = mixer.getrec()[0]
    mixer.close()
    if rec:
      return f"{mic_name}\n🎤🟢"
    else:
      return f"{mic_name}\n🎤🔴"

  def set_mic_muted(self, mic_name, muted):
    mixer = self.get_mixer_by_name(mic_name)
    if mixer is None:
      return
    mixer.setrec(0 if muted else 1)
    mixer.close()

  def get_mic_volume(self, mic_name):
    mixer = self.get_mixer_by_name(mic_name)
    if mixer is None:
      return f"{mic_name}\n🎤🚫"
    vol = mixer.getvolume()[0]
    mixer.close()
    if vol==100:
      return f"{mic_name}\n🎤🟢"
    elif vol==0:
      return f"{mic_name}\n🎤🔴"
    else:
      return f"{mic_name}\n🎤🟠"

  def set_mic_volume(self, mic_name, volume):
    mixer = self.get_mixer_by_name(mic_name)
    if mixer is None:
      return
    mixer.setvolume(volume)
    mixer.close()


def snakedeck_plugin():
  return Alsa()

