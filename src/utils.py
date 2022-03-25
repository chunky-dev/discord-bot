from typing import Optional
import logging
import re
import urllib.parse

import discord
import github
import github.Repository

IMAGE_SUFFIXES = [
    ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".gif", ".mp4"
]

URL_REGEX = re.compile(r"http\S*")


def _match_fname(filename: str) -> bool:
    """ Match a filename against the allowable image suffixes. """
    fname = filename.lower()
    for suffix in IMAGE_SUFFIXES:
        if fname.endswith(suffix):
            return True
    return False


def is_image(message: discord.Message) -> bool:
    """ Check if a message contains an image either through an attachment or link. """
    # Image(s) were uploaded
    if len(message.attachments) > 0:
        for attachment in message.attachments:
            if isinstance(attachment.filename, str) and \
                    _match_fname(attachment.filename):
                return True

    # Check for an image URL
    urls = URL_REGEX.findall(message.content)
    for url in urls:
        try:
            url = urllib.parse.urlparse(url)
            if _match_fname(url.path):
                return True
        except ValueError:
            pass

    # Check for an image embed
    for embed in message.embeds:
        if embed.image.url != discord.Embed.Empty:
            return True
        if embed.thumbnail.url != discord.Embed.Empty:
            return True
        if embed.video.url != discord.Embed.Empty or \
           embed.video.proxy_url != discord.Embed.Empty:
            return True

    return False


def clip_string_length(string: str, length: int):
    """ Clip a string to some amount of characters. """
    if len(string) >= length:
        return string[:length - 3].rstrip() + "..."
    return string


def generate_gh_embed(number: int, repo: github.Repository.Repository) -> \
        Optional[discord.Embed]:
    """ Generate a single discord embed from a GitHub issue / pull request number. """
    try:
        issue = repo.get_issue(number)
        embed = discord.Embed(
            title=issue.html_url,
            url=issue.html_url,
            type="rich",
            description=issue.title,
        )
        embed.add_field(
            name="By",
            value=issue.user.login,
            inline=True
        )
        embed.add_field(
            name="Status",
            value=issue.state,
            inline=True
        )
        embed.add_field(
            name="Description",
            value=clip_string_length(issue.body, 200),
            inline=False
        )
        return embed
    except github.GithubException as e:
        logging.getLogger("github").warning(f"Failed to fetch object number {number}. "
                                            f"{e}")
        return None


def generate_gh_embed_snippet(embed: discord.Embed, number: id,
                              repo: github.Repository.Repository):
    """ Generate a partial discord embed from a GitHub issue / pull request number. """
    try:
        issue = repo.get_issue(number)
        embed.add_field(
            name="Link",
            value=issue.html_url,
            inline=False
        )
        embed.add_field(
            name="Title",
            value=issue.title,
            inline=True
        )
        embed.add_field(
            name="By",
            value=issue.user.login,
            inline=True
        )
        embed.add_field(
            name="Status",
            value=issue.state,
            inline=True
        )
    except github.GithubException as e:
        logging.getLogger("github").warning(f"Failed to fetch object number {number}. "
                                            f"{e}")
