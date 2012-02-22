#! /usr/bin/env python2
# coding=utf-8

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

import re

from .tools import hmsToSec, secToHMS

__TRS_LINE = re.compile("^([+-][0-9]+\.[0-9]+) --> ([0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3})$")

def optimize(delays):
  # Sort
  sortedDelays = sorted(delays, lambda x, y: cmp(x[1], y[1]))
  # Concat same adjacent delays
  if len(sortedDelays) < 2:
    delays = sortedDelays
  else:
    delays = [sortedDelays[0]]
    for d in sortedDelays[1:]:
      if d[0] == delays[-1][0]:
        delays[-1] = d
      else:
        delays.append(d)
  return delays

def writeTransformFile(fileName, delays):
  delays = optimize(delays)
  with open(fileName, "wt") as f:
    for delay, end in delays:
      f.write("%+.3f --> %s\n" %(delay, secToHMS(end)))

def readTransformFile(fileName):
  delays = []
  with open(fileName, "rt") as f:
    for line in f:
      m = __TRS_LINE.match(line)
      if m is None:
        raise ValueError
      else:
        delays.append((float(m.groups()[0]), hmsToSec(m.groups()[1])))
  return optimize(delays)
