#!/usr/bin/env python

from distutils.core import setup
from pkg_resources import parse_requirements

setup(
    name='Chunky Discord Bot',
    version='0.1.0',
    description='Friendly bot for the Chunky Discord server.',
    url='https://github.com/chunky-dev/discord-bot',
    packages=['src'],
    install_requires=parse_requirements('requirements.txt'),
)
