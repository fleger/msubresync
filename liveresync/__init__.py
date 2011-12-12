#! /usr/bin/env python2
# coding=utf-8

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
