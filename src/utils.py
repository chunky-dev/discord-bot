import sched
from typing import Optional, Iterator, Tuple
import logging
import re
import urllib.parse

import requests
import discord
import github
import github.Repository

IMAGE_SUFFIXES = [
    ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".gif", ".gifv", ".mp4", ".webm", ".mov"
]

URL_REGEX = re.compile(r"http\S*")


def _match_fname(filename: str) -> bool:
    """ Match a filename against the allowable image suffixes. """
    fname = filename.lower()
    for suffix in IMAGE_SUFFIXES:
        if fname.endswith(suffix):
            return True
    return False


def get_urls(text: str) -> Iterator[urllib.parse.ParseResult]:
    urls = URL_REGEX.findall(text)
    for url in urls:
        try:
            yield urllib.parse.urlparse(url)
        except ValueError:
            pass


def is_image(message: discord.Message) -> bool:
    """ Check if a message contains an image either through an attachment or link. """
    # Image(s) were uploaded
    if len(message.attachments) > 0:
        for attachment in message.attachments:
            if isinstance(attachment.filename, str) and \
                    _match_fname(attachment.filename):
                return True

    # Check for an image URL
    for url in get_urls(message.content):
        if _match_fname(url.path):
            return True

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


def clip_string_length(string: Optional[str], length: int) -> str:
    """ Clip a string to some amount of characters. """
    if string is None:
        return "None"
    if len(string) >= length:
        return string[:length - 3].rstrip() + "..."
    return string


def ensure_embeddable(string: Optional[str]) -> str:
    """ Ensure a string is embeddable """
    if string is None:
        return "None"
    if len(string.strip()) == 0:
        return string + "\u200B"
    return string


def generate_gh_embed(issue: Tuple[str, str, int], gh: github.Github) -> \
        Optional[discord.Embed]:
    """ Generate a single discord embed from a GitHub issue / pull request number. """
    try:
        repo = gh.get_repo(f"{issue[0]}/{issue[1]}")
        issue = repo.get_issue(int(issue[2]))
        embed = discord.Embed(
            title=issue.html_url,
            url=issue.html_url,
            type="rich",
            description=ensure_embeddable(issue.title),
        )
        embed.add_field(
            name="By",
            value=ensure_embeddable(issue.user.login),
            inline=True
        )
        embed.add_field(
            name="Status",
            value=issue.state,
            inline=True
        )
        embed.add_field(
            name="Description",
            value=ensure_embeddable(clip_string_length(issue.body, 200)),
            inline=False
        )
        return embed
    except github.GithubException as e:
        logging.getLogger("github").warning(
            f"Failed to fetch object number {issue[0]}/{issue[1]}. "
            f"{e}")
        return None


def generate_gh_embed_snippet(embed: discord.Embed, issue: Tuple[str, str, int],
                              gh: github.Github):
    """ Generate a partial discord embed from a GitHub issue / pull request number. """
    try:
        repo = gh.get_repo(f"{issue[0]}/{issue[1]}")
        issue = repo.get_issue(int(issue[2]))
        embed.add_field(
            name="Link",
            value=issue.html_url,
            inline=False
        )
        embed.add_field(
            name="Title",
            value=ensure_embeddable(issue.title),
            inline=True
        )
        embed.add_field(
            name="By",
            value=ensure_embeddable(issue.user.login),
            inline=True
        )
        embed.add_field(
            name="Status",
            value=issue.state,
            inline=True
        )
    except github.GithubException as e:
        logging.getLogger("github").warning(
            f"Failed to fetch object number {issue[0]}/{issue[1]}. "
            f"{e}")


class UrlListKeeper:
    _LOGGER = logging.getLogger("url_list_keeper")

    def __init__(self, url: str):
        self._url = url
        self._lists = set()

    def set_url(self, url: str):
        self._url = url
        self._lists = set()

    def match(self, url: urllib.parse.ParseResult):
        loc = url.netloc.strip()
        if len(loc) > 0:
            if loc in self._lists:
                return True
            for url in self._lists:
                if loc.endswith("." + url):
                    return True
        return False

    def update(self):
        self._LOGGER.info("Updating block list...")
        with requests.get(self._url) as res:
            links = res.json()
            links = links["domains"]
            links = {i.strip() for i in links}
            self._lists = links
        self._LOGGER.info(f"Updated block list: {self._url}")

    def update_and_schedule(self, scheduler: sched.scheduler, interval: float):
        self.update()
        scheduler.enter(interval, 0, self.update_and_schedule,
                        argument=(scheduler, interval))
