#! /usr/bin/env python2
# coding=utf-8

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

import os
import sys
import copy

import yaml

from .singleton import singleton, ignore_subsequent 

@singleton
class Configuration(object):

  DEFAULT_REALM = 0
  CURRENT_REALM = 1

  FILENAME = "msubresync.yaml"

  @ignore_subsequent
  def __init__(self):
    self.__realms = {}
    self.__initDefaults(self.DEFAULT_REALM)
    self.__loadConfig(self.CURRENT_REALM)

  def __initDefaults(self, realm):
    self.__realms[realm] = {
      "ResyncPlayer": {
        "Polling Resolution": 0.1,
        "Auto-resync": True,
        "Bindings": {
          "F11": "Push Delay",
          "MOUSE_BUTTON1": "Push Delay",
          "MOUSE_BTN1": "Push Delay",
        },
      },
      "Subtitles": {
        "Encoding": "utf-8"
      },
    }

  def __loadConfig(self, realm):
    if "XDG_CONFIG_HOME" in os.environ:     # XDG compliant systems
      fileName = os.path.join(os.environ["XDG_CONFIG_HOME"], "msubresync", self.FILENAME)
    elif "APPDATA" in os.environ:           # Windows
      fileName = os.path.join(os.environ["APPDATA"], "msubresync", self.FILENAME)
    elif sys.platform == "darwin":          # Mac OS X
      fileName = os.path.expanduser(os.path.join("~", "Library", "Preferences", "msubresync", self.FILENAME))
    else:                                   # Other: adopt XDG conventions
      fileName = os.path.expanduser(os.path.join("~", ".config", "msubresync", self.FILENAME))

    if os.path.exists(fileName):
      self.__load(realm, fileName)
    else:
      self.__initDefaults(realm)
      self.__save(realm, fileName)

  def __save(self, realm, fileName):
    try:
      os.makedirs(os.path.dirname(fileName))
    except os.error:
      pass

    with open(fileName, "w") as f:
      yaml.dump(self.__realms[realm], f)

  def __load(self, realm, fileName):
    with open(fileName, "r") as f:
      self.__realms[realm] = yaml.load(f)

  @staticmethod
  def mergeDictionaries(dst, src):
    stack = [(dst, src)]
    while stack:
      currentDst, currentSrc = stack.pop()
      for key in currentSrc:
        if key not in currentDst:
          currentDst[key] = copy.deepcopy(currentSrc[key])
        else:
          if isinstance(currentSrc[key], dict) and isinstance(currentDst[key], dict) :
            stack.append((currentDst[key], currentSrc[key]))
          else:
            currentDst[key] = copy.deepcopy(currentSrc[key])
    return dst

  @property
  def values(self):
    return self.mergeDictionaries(self.__realms[self.CURRENT_REALM], self.__realms[self.DEFAULT_REALM])


