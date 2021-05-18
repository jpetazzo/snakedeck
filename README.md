# SnakeDeck 🐍🎛️

SnakeDeck (or snakedeck, as you like) is a program written in Python
to manage devices like the [Elgato Stream Deck].

The code quality is barely alpha level; treat it like a prototype or
MVP. That being sai, I use it "in production" (to control my
lights, cameras, and a few more things necessary when I run my
[Docker and Kubernetes training courses]).


## Why?

I wrote SnakeDeck because [streamdeck-ui] didn't have the features
that I needed. SnakeDeck is, however, using the same underlying Python
library to interface the Stream Deck.


## What can I do with it?

The most interesting feature of SnakeDeck is probably the fact that
you can associate Python code to the Stream Deck keys, and that
Python code can return the new state of the keys (for instance,
to reflect some "on/off" state). It is also (relatively) easy to
update key status remotely.


## Getting started

Clone that repo, `pip install --user requirements.txt`; and you
might have to do some setup specific to the Stream Deck library
(FIXME add link to that).

Then run `snakedeck.py`. If it detects a Stream Deck, it will
display a message like the following one:

```
WARNING:root:Deck AL012345678 has no configuration file (/home/jp/.config/snakedeck/AL012345678.yaml).
```

We need to create that configuration file. SnakeDeck monitors that
location, so we don't need to restart SnakeDeck after creating the file.
Furthermore, after loading the file, SnakeDeck keeps monitoring the
file, and automatically reloads it when it changes.

(We still need to restart SnakeDeck when changing its code or its
plugins, though. For now, at least.)

The configuration file should be a list of key bindings.


## Key bindings

A key binding will look like this:

```yaml
- line: 1
  column: 1
  label: Hello, world!
  emoji: 😎
  shell: curl http://localhost:5000
  eval: print(42)
```

The `line` and `column` is the position of the key on the Stream Deck.
(Line 1 is on top, column 1 is on the left.)

You probably want to specify `label` or `emoji`, not both. The text of the label
will be shrunk if it doesn't fit on the key (so if you put a super long label it
will be in tiny text). The emoji will be zoomed to take the whole key. Emojis
require to have the Noto Color Emoji font installed.

If the key as a `shell` section, that command will be executed in a shell.

If the key has an `eval` section, it will be evaluated as Python code. It
can be anything you like (including dangerous stuff that would totally mess up
with SnakeDeck's internal state, because why not).

If the code in the `eval` section returns something (that is not `None`), that
something should be a `dict` and will be used to update the state of the key.
This lets us change the `label`, the `emoji`, or even the action associated with
the key.


## Cycles

A key binding can also be a cycle, like this:

```yaml
- line: 1
  column: 1
  cycle:
  - emoji: 🙂
  - emoji: 🤣
  - emoji: 😭
  - emoji: 🤬
```

Each time it is pressed, the key will change to the next state in the cycle,
and will loop back to the beginning at the end. In the example above, the keys
don't do anything (other than changing what's shown on them) but the keys can
of course have actions associated with them, like in the example below.

```yaml
- line: 1
  column: 1
  cycle:
  - emoji: 🔇
    shell: pactl set-sink-mute @DEFAULT_SINK@ off
  - emoji: 🔊
    shell: pactl set-sink-mute @DEFAULT_SINK@ on
```


## Sync

A key can be synchronized with other Stream Decks, like this:

```yaml
- line: 1
  column: 1
  cycle:
  - emoji: ✅
  - emoji: ⛔️
  sync: stopgo
```

When a synchronized key is pressed, SnakeDeck starts sending multicast
packets every second with the state of the key. The packet contains the
synchronization tag (in that case `stopgo`).

When SnakeDeck receives one of these packets, and has a key with the same
synchornization tag, it updates the state of the key. Note that it completely
overwrite the state of the key.

Packets also contain a serial number that gets incremented automatically
when the state of the key changes.

The synchronization mechanism is currently bidirectional, but might change
in the future to allow send-only and receive-only operation.


## Future developments

Feel free to open issues if you have great ideas of new features!


[Elgato Stream Deck]: https://www.elgato.com/en/stream-deck
[Docker and Kubernetes training courses]: https://container.training/
[streamdeck-ui]: https://timothycrosley.github.io/streamdeck-ui/
