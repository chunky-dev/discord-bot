from typing import *
import sys
import os

import discord

from imposter import *

sys.path.insert(1, os.path.join(sys.path[0], '../src'))
import utils


TEST_FILES_IMAGES = [
    "test.jpg",
    "test.JPG",
    "test.jpeg",
    "test.JPEG",
    "test.png",
    "test.PNG",
    "test.tif",
    "test.TIF",
    "test.tiff",
    "test.TIFF",
    "test.webp",
    "test.WEBP",
    "test.gif",
    "test.GIF",
    "test.mp4",
    "test.MP4",
]
TEST_FILES_NOT_IMAGES = [
    "test.bitmap",
    "test.raw",
    "test.psd",
    "test.txt",
    "test.docx",
    "test.123213123123 1231231 23123 yes png",
    "test.not a jpeg",
]


def test_match_fname():
    for file in TEST_FILES_IMAGES:
        assert utils._match_fname(file)
    for file in TEST_FILES_NOT_IMAGES:
        assert not utils._match_fname(file)


def _create_message(attachments: List[ImposterAttachment], content: str) -> ImposterMessage:
    message = ImposterMessage()
    message.attachments = attachments
    message.content = content
    return message


def _create_embed_message():
    message = ImposterMessage()
    message.embeds.append(discord.Embed())
    return message


def test_is_image():
    for file in TEST_FILES_IMAGES:
        message = _create_message([ImposterAttachment(file)], "")
        assert utils.is_image(message)
        message = _create_message([ImposterAttachment("Not an image")], f"http://test/{file}")
        assert utils.is_image(message)
        message = _create_message([ImposterAttachment("Not an image")], f"https://test/{file}")
        assert utils.is_image(message)

    for file in TEST_FILES_NOT_IMAGES:
        message = _create_message([ImposterAttachment(file)], "")
        assert not utils.is_image(message)
        message = _create_message([ImposterAttachment("Not an image")], f"http://test/{file}")
        assert not utils.is_image(message)
        message = _create_message([ImposterAttachment("Not an image")], f"https://test/{file}")
        assert not utils.is_image(message)

    # Test an invalid url
    message = _create_message([ImposterAttachment("Not an image")], "http://[test/yes.png")
    assert not utils.is_image(message)

    # Test for embeds
    message = _create_embed_message()
    message.embeds[0].set_image(url="some url")
    assert utils.is_image(message)

    message = _create_embed_message()
    message.embeds[0].set_thumbnail(url="some url")
    assert utils.is_image(message)

    message = _create_embed_message()
    message.embeds[0]._video = {"url": "some url"}
    assert utils.is_image(message)

    message = _create_embed_message()
    message.embeds[0]._video = {"proxy_url": "some url"}
    assert utils.is_image(message)

    message = _create_embed_message()
    assert not utils.is_image(message)
