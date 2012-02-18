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

class VideoDelays(object):

  def __init__(self, fileName=None):
    self.__fileName = fileName
    self._delays = []
    self._subFiles = []
    self.__length = None

  @property
  def fileName(self):
    return self.__fileName

  @fileName.setter
  def fileName(self, f):
    self.__fileName = f

  @property
  def delays(self):
    return copy.copy(self._delays)

  @property
  def subFiles(self):
    return copy.copy(self._subFiles)

  @property
  def length(self):
    return self.__length

  @length.setter
  def length(self, l):
    self.__length = l


class ResyncPlayer(object):
  NO_BIND = re.compile(".*No bind found for key '(.+)'\.")
  SUB_FILE = re.compile("SUB: Added subtitle file \([0-9]+\): (.+)$")
  POLLING_RESOLUTION = 0.1

  def __init__(self, args=[]):
    # Player instanciation
    self.__player = AsyncPlayer(autospawn=False, stderr=subprocess.PIPE)   
    self.__player.stdout.connect(self.__stdoutHandler)
    self.__player.stderr.connect(self.__stderrHandler)
    self.__player._base_args = ('-slave', '-really-quiet', '-msglevel', 'global=4')
    self.__player.args = ['-msglevel', 'input=5:cplayer=5'] + list(args)

    # Key binding
    self.__keys = {}
    self.__keys["F11"] = self.__pushDelay
    self.__keys["'"] = self.__pushDelay
    self.__keys["MOUSE_BTN1"] = self.__pushDelay
    
    self.__videos = []
    
    self.__lastDelay = (0, 0)
    self.__pollLock = threading.RLock()
    self.__running = False

  @property
  def videos(self):
    return tuple(self.__videos)

  def __poll(self):
    # Get current fileName from mplayer
    fileName = self.__player.filename

    if fileName is not None:
      with self.__pollLock:
        if len(self.__videos) == 0:
          # We have a new video
          print("[ResyncPlayer] New video: %s" %fileName, file=sys.stderr)
          self.__videos.append(VideoDelays(fileName))
        elif fileName != self.__videos[-1].fileName:
          # We changed video
          self.__videos[-1]._delays.append((self.__lastDelay[0], self.__videos[-1].length))
          s = "%+.3f --> %s" %(self.__lastDelay[0], secToHMS(self.__videos[-1].length))
          print(s)
          print("[ResyncPlayer] New video: %s" %fileName, file=sys.stderr)
          self.__videos.append(VideoDelays(fileName))
          self.__lastDelay = (0, 0)
    
        # Get sub_delay and time_pos from mplayer
        delay = (self.__player.sub_delay, self.__player.time_pos)
        # Check if we have all the right values and update lastDelay
        if delay[0] is not None and delay[1] is not None:
          self.__lastDelay = (-delay[0], delay[1])
        # Retreive the length of the video if we haven't done it yet
        if len(self.__videos) > 0 and self.__videos[-1].length is None:
          self.__videos[-1].length = self.__player.length

    # Rearm timer
    if self.__running:
      self.__pollTimer = threading.Timer(self.POLLING_RESOLUTION, self.__poll)
      self.__pollTimer.start()

  def __keyHandler(self, key, default=None):
    self.__keys.get(key, self.dummy if default is None else default)()

  def dummy(self):
    pass

  def __pushDelay(self):
    if len(self.__videos) > 0:
      with self.__pollLock:
        # Filter out later delays
        self.__videos[-1]._delays = filter(lambda x: x[1] < self.__lastDelay[1], self.__videos[-1]._delays)
        # Append lastDelay
        self.__videos[-1]._delays.append(self.__lastDelay)
      s = "%+.3f --> %s" %(self.__videos[-1]._delays[-1][0], secToHMS(self.__videos[-1]._delays[-1][1]))
      print(s)
      self.__player.osd_show_text(s)

  def __stdoutHandler(self, data):
    if data.startswith('EOF code'):
      self.__player.quit()
    else:
      matches = self.SUB_FILE.match(data)
      if matches is not None and len(self.__videos) > 0:
        self.__videos[-1]._subFiles.append(matches.groups()[0])
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
    # Main loop
    asyncore.loop()
    #print("asyncore loop stopped", file=sys.stderr)
    self.__running = False
    self.__pollTimer.cancel()
    # Fixup the last video delays
    if len(self.__videos) > 0:
      self.__videos[-1]._delays.append((self.__lastDelay[0], self.__videos[-1].length))
      s = "%+.3f --> %s" %(self.__lastDelay[0], secToHMS(self.__videos[-1].length))
      print(s)
