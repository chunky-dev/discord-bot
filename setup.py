#!/usr/bin/env python

from distutils.core import setup

setup(
    name='Chunky Discord Bot',
    version='0.1.0',
    description='Friendly bot for the Chunky Discord server.',
    url='https://github.com/chunky-dev/discord-bot',
    packages=['src'],
    install_requires=[
        "discord.py~=1.7.3",
        "discord-py-slash-command~=3.0.3",
        "PyGithub~=1.55",
    ],
)
