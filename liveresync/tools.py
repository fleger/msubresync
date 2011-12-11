#! /usr/bin/env python2
# coding=utf-8

import re

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