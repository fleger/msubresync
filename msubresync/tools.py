#! /usr/bin/env python2
# coding=utf-8

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

import re

import aeidon

from .configuration import Configuration

__HMS = re.compile("^([0-9]{2}):([0-9]{2}):([0-9]{2}\.[0-9]{3})$")

def hmsToSec(hms):
  m = __HMS.match(hms)
  if hms is None:
    raise ValueError
  else:
    return int(m.groups()[0]) * 3600 + int(m.groups()[1]) * 60 + float(m.groups()[2])

def secToHMS(seconds):
  h = int(seconds / 3600)
  seconds %= 3600
  m = int(seconds / 60)
  seconds %= 60
  return "%02d:%02d:%06.3f" %(h, m, seconds)

def applyDelaysToSubtitles(delays, fileName):
  currentIndex = 0
  conf = Configuration()
  p = aeidon.Project()
  p.open_main(fileName, encoding=conf.values["Subtitles"]["Encoding"])
  for s in p.subtitles:
    if (hmsToSec(s.get_start(aeidon.modes.TIME)) + delays[currentIndex][0] > delays[currentIndex][1]) and (currentIndex < (len(delays) - 1)):
      currentIndex += 1
    s.shift_positions(delays[currentIndex][0])
  p.save_main()