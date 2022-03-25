from typing import List, Tuple
import argparse
import configparser
import logging
import re

import discord
import discord_slash
import github

import utils

REMOVE_EMOJI = discord.PartialEmoji(name="❌")


LOG_LEVEL_MAP = {
    "ALL": logging.NOTSET,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "FATAL": logging.FATAL
}


class Bot(discord.Client):
    """
    The main bot. Handles finding GitHub numbers in messages,
    react-remove messages, and deleting non-images from image only channels.
    """

    GH_REGEX = re.compile(r"#\d+")

    def __init__(self, repo, image_only: List[Tuple[int, str]],
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._repo = repo
        self._image_only = image_only
        self._logger = logging.getLogger("bot")

    async def on_message(self, message: discord.Message):
        """ On message callback. Find GitHub numbers, delete non-images. """

        # Check if the message is from ourselves
        if message.author.id == self.user.id:
            return

        # Check if we are in the renderers channel
        for channel, warn in self._image_only:
            if message.channel.id == channel:
                if not utils.is_image(message):
                    self._logger.info(f"Removing message {message.id} in "
                                      f"{message.channel.id} for not having "
                                      f"an image: {message.content}")
                    warning = await message.reply(
                        content=warn,
                        mention_author=True
                    )
                    await message.delete()
                    await warning.delete(delay=10)
                return

        # Look for GitHub issues / pull requests
        numbers = self.GH_REGEX.findall(message.content)
        numbers = [int(number[1:]) for number in numbers]

        # Create the embed
        embed = None
        if len(numbers) == 1:
            self._logger.info(f"Message {message.id} with one GitHub number.")
            embed = utils.generate_gh_embed(numbers[0], self._repo)
        elif len(numbers) > 1:
            self._logger.info(f"Message {message.id} with {len(numbers)} "
                              f"GitHub numbers.")
            embed = discord.Embed(title="Issues / pull requests")
            for number in numbers:
                utils.generate_gh_embed_snippet(embed, number, self._repo)

        # Send the message
        if embed is not None:
            embed.set_footer(text=f"React with {REMOVE_EMOJI} to remove.\n"
                                  f"{message.author.id}")
            m = await message.reply(
                embed=embed,
                mention_author=False
            )
            await m.add_reaction(REMOVE_EMOJI)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """ Handle react-remove messages. """

        if payload.user_id == self.user.id:
            return  # Event from us
        if payload.emoji != REMOVE_EMOJI:
            return  # Incorrect emoji
        if payload.event_type != "REACTION_ADD":
            return  # Emoji was not added

        # Get the channel
        channel = self.get_channel(payload.channel_id)
        message: discord.Message = await channel.fetch_message(payload.message_id)

        if message.author.id != self.user.id:
            return  # Original author was not us
        if len(message.embeds) != 1:
            return  # Original message had an incorrect number of embeds

        # Try and get the user id from the embed
        embed = message.embeds[0]
        if not isinstance(embed.footer.text, str):
            return  # Invalid embed
        user = embed.footer.text.split("\n")[-1]
        try:
            user = int(user)
        except ValueError:
            return  # Invalid user id
        if user != payload.user_id:
            return  # User does not have permission to remove this

        self._logger.info(f"React-deleting our message {message.id}")
        await message.delete()


class Slash(discord_slash.SlashCommand):
    """ /gh Slash command. """

    def __init__(self, repo, image_only: List[Tuple[int, str]], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._repo = repo
        self._logger = logging.getLogger("bot-slash")
        self._image_only_channels = {i[0] for i in image_only}

        self.add_slash_command(
            self.gh,
            name="gh",
            description="Get a Github pull request / issue from its number."
        )

    async def gh(self, ctx, number: int):
        """ /gh [number] command. """

        if ctx.channel_id in self._image_only_channels:
            self._logger.info(f"Attempted slash command in protected channel "
                              f"{ctx.channel_id}.")
            await ctx.send(content="Cannot send text messages in this channel.",
                           hidden=True)
            return

        embed = utils.generate_gh_embed(number, self._repo)
        if embed is not None:
            self._logger.info(f"Slash command with valid GitHub number #{number}.")
            embed.set_footer(text=f"React with {REMOVE_EMOJI} to remove.\n"
                                  f"{ctx.author_id}")
            m = await ctx.send(embed=embed, hidden=False)
            await m.add_reaction(REMOVE_EMOJI)
        else:
            self._logger.info(f"Slash command with invalid GitHub number #{number}.")
            await ctx.send(content=f"Invalid pull / issue number: #{number}",
                           hidden=True)


# skipcq PY-D0003 - docstring for main
def main():
    parser = argparse.ArgumentParser(description="Chunky Discord Bot")
    parser.add_argument("discord", help="Discord API key.")
    parser.add_argument("--github", help="Github API key.", default=None)
    parser.add_argument("--log-level", help="Log level (default INFO).", default="INFO")
    parser.add_argument("--config", help="Path to the config file.",
                        default="config.ini")
    parser.add_argument("--debug-guild", help="Debug guild id.", default=None)
    args = parser.parse_args()

    # Setup logging
    if args.log_level not in LOG_LEVEL_MAP.keys():
        print("Log level must be one of: ALL, DEBUG, INFO, WARN, ERROR, FATAL")
        return
    logging.basicConfig(level=LOG_LEVEL_MAP.get(args.log_level))

    # Load config
    config = configparser.ConfigParser()
    config.read(args.config)

    # Setup GitHub
    if "GITHUB" not in config:
        print("Config must have [GITHUB] section.")
        return
    if "repository" not in config["GITHUB"]:
        print("Config must have \"repository\" under [GITHUB] section.")
        return
    gh = github.Github(login_or_token=args.github)
    repo = gh.get_repo(config["GITHUB"]["repository"])

    # Image only channels
    image_only: List[Tuple[int, str]] = []
    if "IMAGE_ONLY" in config:
        for key, value in config["IMAGE_ONLY"].items():
            try:
                image_only.append((int(key), value,))
            except ValueError:
                logging.getLogger("bot").error(f"Invalid [IMAGE_ONLY] channel {key}.")
    else:
        logging.getLogger("bot").warning("Config does not contain an [IMAGE_ONLY] "
                                         "section. Bot will not filter any channels.")

    bot = Bot(repo, image_only)
    _slash = Slash(repo, image_only, client=bot, debug_guild=args.debug_guild,
                   sync_commands=True)

    # OAUTH2 must have `bot` and `applications.commands` scopes
    # Bot permissions: 274877982784
    bot.run(args.discord)


if __name__ == '__main__':
    main()
