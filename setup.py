# -*- coding:utf-8 -*-

try:
  import setuptools
  from setuptools import setup
except ImportError:
  print("Please install setuptools.")

setup_options = dict(
    name        = "pings",
    description = "Simple ping client in Python 3 by using icmp packet via low level socket.",
    author      = "satoshi03",
    author_email = "innamisatoshi@gmail.com",
    license     = "GPL",
    url         = "https://github.com/satoshi03/pings",
    classifiers = [
      "Programming Language :: Python :: 3",
      "Programming Language :: Python :: 3.6",
      'License :: OSI Approved :: GNU General Public License (GPL)'
    ]
)
setup_options["version"] = "0.0.1"
setup_options.update(dict(
  packages         = ['pings'],
))

setup(**setup_options)
