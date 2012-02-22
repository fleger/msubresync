#! /usr/bin/env python2
# coding=utf-8

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

from setuptools import setup, find_packages

setup(
  name = "msubresync",
  version = "0.1.0",
  packages = find_packages(),
  entry_points = {
    "console_scripts": [
      "msubresync = msubresync:main",
    ],
  },

  install_requires = ['mplayer.py>=0.7', 'PyYAML'],

  author = "Florian Léger",
  author_email = "florian6.leger@laposte.net",
  description = "Simple wrapper around MPlayer aimed at simplifying subtitles resynchronization.",
  license = "WTFPL",
  keywords = "mplayer subtitles resynchronization",
  url = "https://github.com/fleger/msubresync",
)
