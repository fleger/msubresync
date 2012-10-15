#! /usr/bin/env python2
# coding=utf-8

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.



import sys

from .resyncplayer import ResyncPlayer
from .transform import writeTransformFile, readTransformFile
from .tools import applyDelaysToSubtitles
from .configuration import Configuration

actions = {}

def action(func):
  actions[func.__name__] = func
  return func

@action
def play(*argv):
  player = ResyncPlayer(argv)
  player.run()
  for video in player.videos:
    if len(video.delays) > 0:
      for f in video.subFiles:
        print("Resynchronizing %s" %f)
        applyDelaysToSubtitles(video.delays, f)

@action
def save(*argv):
  player = ResyncPlayer(argv)
  player.run()
  for video in player.videos:
    f = ".".join((video.fileName, "trs"))
    writeTransformFile(f, video.delays)
    print("Transform file saved as %s" %f)

@action
def resync(trs, *subFiles):
  delays = readTransformFile(trs)
  if len(delays) < 1:
    sys.exit(0)
  for f in subFiles:
    applyDelaysToSubtitles(delays, f)

def hlp(*argv):
  print("""Usage: %s action

Actions:

  play [arguments]              Play files with mplayer and directly resynchronize the corresponding
                                subtitle files.
                                arguments: valid mplayer arguments.

  save [arguments]              Play files with mplayer and save the resynchronization information
                                in a .trs file without modifying the subtitles.
                                arguments: valid mplayer arguments.

  resync file.trs subfiles ...  Apply a .trs file to a set of subtitle files.
""" %(sys.argv[0]))
  sys.exit(1)

def main():
  conf = Configuration()
  if len(sys.argv) < 2:
    hlp()
  actions.get(sys.argv[1], hlp)(*sys.argv[2:])
  
    