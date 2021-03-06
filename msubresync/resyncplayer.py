#! /usr/bin/env python2
# coding=utf-8

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.



import sys
import threading
import asyncore
import re
import subprocess
import copy
import os

from mplayer.async import AsyncPlayer

from .tools import secToHMS
from .configuration import Configuration

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
  FILE_NAME = re.compile("Playing (.+)\.$")

  def __init__(self, args=[]):
    # Player instanciation
    self.__player = AsyncPlayer(autospawn=False, stderr=subprocess.PIPE)   
    self.__player.stdout.connect(self.__stdoutHandler)
    self.__player.stderr.connect(self.__stderrHandler)
    self.__player._base_args = ('-slave', '-really-quiet', '-msglevel', 'global=4')
    self.__player.args = ['-msglevel', 'input=5:cplayer=5'] + list(args)

    conf = Configuration()
    self.__pollingResolution = conf.values["ResyncPlayer"]["Polling Resolution"]
    self.__autoResync = conf.values["ResyncPlayer"]["Auto-resync"]

    # Action mapping
    self.__actions = {
      "Push Delay": self.__pushDelay,
      "Dummy": self.__dummy,
    }

    # Key binding
    self.__keys =  conf.values["ResyncPlayer"]["Bindings"]

    self.__videos = []
    
    self.__lastDelay = (0, 0)
    self.__currentDelayPosition = float("inf")
    self.__pollLock = threading.RLock()
    self.__running = False

  @property
  def videos(self):
    return tuple(self.__videos)

  def __poll(self):
    with self.__pollLock:
      # Get sub_delay and time_pos from mplayer
      delay = (self.__player.sub_delay, self.__player.time_pos)
      # Check if we have all the right values
      if delay[0] is not None and delay[1] is not None:
        # Auto-resync on seek before the last pushed delay
        if self.__autoResync and len(self.__videos) > 0 and len(self.__videos[-1]._delays) > 0 and delay[1] < self.__videos[-1]._delays[-1][1]:
          for d in self.__videos[-1]._delays:
            if delay[1] < d[1]:
              # Auto resync only once per delay position
              if d[1] != self.__currentDelayPosition:
                self.__player.sub_delay = -d[0]
                print("[ResyncPlayer] Auto-resync to %.3f" %(d[0]), file=sys.stderr)
                self.__player.osd_show_text("Sub delay: %s ms" %(int(-d[0] * 1000)))
                self.__currentDelayPosition = d[1]
                # sub_delay has changed
                delay = (d[0], delay[1])
              break
        # Update lastDelay
        # msubresync delays follow aeidon's convention, which is the opposite of mplayer
        self.__lastDelay = (-delay[0], delay[1])

      # Retreive the length of the video if we haven't done it yet
      if len(self.__videos) > 0 and self.__videos[-1].length is None:
        self.__videos[-1].length = self.__player.length

    # Rearm timer
    if self.__running:
      self.__pollTimer = threading.Timer(self.__pollingResolution, self.__poll)
      self.__pollTimer.start()

  def __keyHandler(self, key, default=None):
    self.__actions.get(self.__keys.get(key, "Dummy" if default is None else default), self.__dummy)()

  def __dummy(self):
    pass

  def __pushDelay(self):
    if len(self.__videos) > 0:
      with self.__pollLock:
        # Filter out later delays
        self.__videos[-1]._delays = [x for x in self.__videos[-1]._delays if x[1] < self.__lastDelay[1]]
        # Append lastDelay
        self.__videos[-1]._delays.append(self.__lastDelay)
      s = "%+.3f --> %s" %(self.__videos[-1]._delays[-1][0], secToHMS(self.__videos[-1]._delays[-1][1]))
      print(s)
      self.__player.osd_show_text(s)

  def __stdoutHandler(self, data):
    if data.startswith('EOF code'):
      self.__player.quit()
      return

    matches = self.FILE_NAME.match(data)
    if matches is not None:
      with self.__pollLock:
        if len(self.__videos) > 0:
          # Changed video - fixup last delay
          self.__videos[-1]._delays.append((self.__lastDelay[0], self.__videos[-1].length))
          s = "%+.3f --> %s" %(self.__lastDelay[0], secToHMS(self.__videos[-1].length))
          print(s)

        # New video
        print("[ResyncPlayer] New video: %s" %matches.groups()[0], file=sys.stderr)
        self.__videos.append(VideoDelays(matches.groups()[0]))
        self.__lastDelay = (0, 0)
        self.__currentDelayPosition = float("inf")

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
    # Workaround for uncaught exceptions unexpectedly closing the channels
    self.__player.stdout._dispatcher.handle_error = self.__dummy
    self.__player.stderr._dispatcher.handle_error = self.__dummy
    self.__running = True
    # Start polling
    self.__poll()
    # Main loop
    asyncore.loop()
    #print("asyncore loop stopped", file=sys.stderr)
    self.__running = False
    self.__pollTimer.cancel()
    # Fixup the last video delays
    if len(self.__videos) > 0 and self.__videos[-1].length is not None:
      self.__videos[-1]._delays.append((self.__lastDelay[0], self.__videos[-1].length))
      s = "%+.3f --> %s" %(self.__lastDelay[0], secToHMS(self.__videos[-1].length))
      print(s)
