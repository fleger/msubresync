#! /usr/bin/env python2
# coding=utf-8

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

from __future__ import print_function

import sys
import threading
import asyncore
import re
import subprocess
import copy

from mplayer.async import AsyncPlayer

from .tools import secToHMS

class ResyncPlayer(object):
  NO_BIND = re.compile(".*No bind found for key '(.+)'\.")
  SUB_FILE = re.compile("SUB: Added subtitle file \(1\): (.+)$")
  POLLING_RESOLUTION = 0.1

  def __init__(self, args=[]):
    self.__player = AsyncPlayer(autospawn=False, stderr=subprocess.PIPE)   
    self.__player.stdout.connect(self.__stdoutHandler)
    self.__player.stderr.connect(self.__stderrHandler)
    self.__player._base_args = ('-slave', '-really-quiet', '-msglevel', 'global=4')
    self.__player.args = ['-msglevel', 'input=5:cplayer=5'] + list(args)
    self.__keys = {}
    self.__keys["F11"] = self.__pushDelay
    self.__keys["MOUSE_BTN1"] = self.__pushDelay
    self.__delays = []
    self.__lastDelay = (0, 0)
    self.__pollLock = threading.RLock()
    self.__length = None
    self.__subFile = None
    self.__running = False

  @property
  def _lastDelay(self):
    with self.__pollLock:
      return self.__lastDelay

  @property
  def length(self):
    with self.__pollLock:
      return self.__length

  @property
  def delays(self):
    return copy.copy(self.__delays)

  @property
  def subFile(self):
    return self.__subFile

  def __poll(self):
    delay = (self.__player.sub_delay, self.__player.time_pos)
    with self.__pollLock:
      if delay[0] is not None and delay[1] is not None:
        self.__lastDelay = (-delay[0], delay[1])
      if self.length is None:
        self.__length = self.__player.length
    if self.__running:
      self.__pollTimer = threading.Timer(self.POLLING_RESOLUTION, self.__poll)
      self.__pollTimer.start()
    else:
      print("polling not reconducted", file=sys.stderr)

  def __keyHandler(self, key, default=None):
    self.__keys.get(key, self.dummy if default is None else default)()

  def dummy(self):
    pass

  def __pushDelay(self):
    self.__delays.append(self._lastDelay)
    s = "%+.3f --> %s" %(self.__delays[-1][0], secToHMS(self.__delays[-1][1]))
    print(s)
    self.__player.osd_show_text(s)

  def __stdoutHandler(self, data):
    if data.startswith('EOF code'):
      self.__player.quit()
    else:
      matches = self.SUB_FILE.match(data)
      if matches is not None:
        self.__subFile = matches.groups()[0]
      print("%s" %data)

  def __stderrHandler(self, data):
    matches = self.NO_BIND.match(data)
    if matches:
      self.__keyHandler(matches.groups()[0])
    else:
      print("%s" %data, file=sys.stderr)

  def run(self):
    self.__player.spawn()
    # FIXME: workaround uncaught exceptions closing the channels
    self.__player.stdout._dispatcher.handle_error = self.dummy
    self.__player.stderr._dispatcher.handle_error = self.dummy
    self.__running = True
    self.__poll()
    asyncore.loop()
    print("asyncore loop stopped", file=sys.stderr)
    self.__running = False
    self.__pollTimer.cancel()
    self.__delays.append((self._lastDelay[0], self.length))
    s = "%+.3f --> %s" %(self._lastDelay[0], secToHMS(self.length))
    print(s)
