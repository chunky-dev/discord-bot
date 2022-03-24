from typing import *
import logging
import re
import urllib.parse

import discord
import github
import github.Repository

IMAGE_SUFFIXES = [
    "jpg", "jpeg", "png", "tif", "tiff", "webp", "gif", "mp4"
]

URL_REGEX = re.compile(r"http\S*")


def _match_fname(filename: str) -> bool:
    fname = filename.lower()
    for suffix in IMAGE_SUFFIXES:
        if fname.endswith(suffix):
            return True
    return False


def is_image(message: discord.Message) -> bool:
    # Image(s) were uploaded
    if len(message.attachments) > 0:
        for attachment in message.attachments:
            assert isinstance(attachment.filename, str)
            if _match_fname(attachment.filename):
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

    return False


def generate_gh_embed(number: int, repo: github.Repository.Repository) -> Optional[discord.Embed]:
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
            value=issue.body,
            inline=False
        )
        return embed
    except github.GithubException as e:
        logging.getLogger("github").warning(f"Failed to fetch object number {number}. {e}")
        return None


def generate_gh_embed_snippet(embed: discord.Embed, number: id, repo: github.Repository.Repository):
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
        logging.getLogger("github").warning(f"Failed to fetch object number {number}. {e}")
