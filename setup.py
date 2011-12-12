#! /usr/bin/env python2
# coding=utf-8

from setuptools import setup, find_packages

setup(
  name = "liveresync",
  version = "0.1.0",
  packages = find_packages(),
  entry_points = {
    "console_scripts": [
      "liveresync-player = liveresync:mainResyncPlayer",
      "liveresync-apply = liveresync:mainApplyTransform",
    ],
  },

  install_requires = ['mplayer.py>=0.7'],
  dependency_links = [
    "http://home.gna.org/gaupol/download.html"
  ],

  author = "Florian Léger",
  author_email = "florian6.leger@laposte.net",
  description = "Simple wrapper around MPlayer aimed at simplifying subtitles resynchronization.",
  license = "WTFPL",
  keywords = "mplayer subtitles resynchronization",
  url = "https://github.com/fleger/liveresync",
)