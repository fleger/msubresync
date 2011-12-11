#! /usr/bin/env python2
# coding=utf-8

from __future__ import print_function

import threading
import asyncore
import re
import subprocess
import copy

from mplayer.async import AsyncPlayer

class ResyncPlayer(object):
  NO_BIND = re.compile(".*No bind found for key '(.+)'\.")
  SUB_FILE = re.compile("SUB: Added subtitle file \(1\): (.+)$")

  def __init__(self, args=[]):
    self.__player = AsyncPlayer(autospawn=False, stderr=subprocess.PIPE)
    self.__player._base_args = ('-slave', '-idle', '-really-quiet', '-msglevel', 'global=4', '-input', 'nodefault-bindings')
    self.__player.args = ['-msglevel', 'input=5:cplayer=5'] + list(args)
    self.__player.stdout.connect(self.__stdoutHandler)
    self.__player.stderr.connect(self.__stderrHandler)
    self.__keys = {}
    self.__keys["KP9"] = self.__pushDelay
    self.__delays = []
    self.__lastDelay = (0, 0)
    self.__pollLock = threading.RLock()
    self.__length = None
    self.__subFile= None

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
    if self.__player.is_alive():
      self.__pollTimer = threading.Timer(.1, self.__poll)
      self.__pollTimer.start()

  def __keyHandler(self, key, default=None):
    self.__keys.get(key, self.dummy if default is None else default)()

  def dummy(self):
    pass

  def __pushDelay(self):
    print(self._lastDelay)
    self.__delays.append(self._lastDelay)

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
    self.__poll()
    asyncore.loop()
    self.__pollTimer.cancel()
    self.__delays.append((self._lastDelay[0], self.length))

  def getDelays(self):
    return self.__delays
