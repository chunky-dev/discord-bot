# Chunky Discord Bot

Discord bot for the [Chunky discord](https://discord.gg/VqcHpsF) community.

- Catches GitHub pull request / issue numbers in messages and adds links
- Adds a `/gh [number]` command for pull request / issues
- Moderates the `#renders` channel to remove non-image posts

## How to debug

1. Install Python 3 and pip3
2. Install dependencies using `pip3 install -r requirements.txt`
3. Run usage: `main.py --debug-guild <your server id> <discord api token>` (`--debug-guild` is only needed for slash commands)
