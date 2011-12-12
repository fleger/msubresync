#! /usr/bin/env python2
# coding=utf-8

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

from __future__ import print_function

import sys

import aeidon

from .resyncplayer import ResyncPlayer
from .transform import writeTransformFile, readTransformFile
from .tools import hmsToSec

def resyncPlayer(*argv):
  player = ResyncPlayer(argv)
  player.run()
  f = ".".join((player.subFile, "trs"))
  writeTransformFile(f, player.delays)
  print("Transform file saved as %s" %f)

def applyTransform(trs, *subFiles):
  delays = readTransformFile(trs)
  if len(delays) < 1:
    sys.exit(0)
  for f in subFiles:
    currentIndex = 0
    p = aeidon.Project()
    p.open_main(f)
    for s in p.subtitles:
      if (hmsToSec(s.get_start(aeidon.modes.TIME)) > delays[currentIndex][1]) and (currentIndex < (len(delays) - 1)):
        currentIndex += 1
      s.shift_positions(delays[currentIndex][0])
    p.save_main()

def mainResyncPlayer():
  resyncPlayer(*sys.argv[1:])

def mainApplyTransform():
  applyTransform(*sys.argv[1:])
