# -*- coding: utf-8 -*-
import os
import textwrap

from uniseg import graphemecluster as gc
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageOps


EMOJI_FILES_PATH = "./apple_color_emoji/set_160"


class EmojiFilesCache(object):
    EMOJI_FILES = []

    TONE_MODIFIER_MAP = {
        'u1F3FB.png': "1",
        'u1F3FC.png': "2",
        'u1F3FD.png': "3",
        'u1F3FE.png': "4",
        'u1F3FF.png': "5",
    }

    @classmethod
    def get_emoji_files(cls):
        if not cls.EMOJI_FILES:
            for (path, dirs, files) in os.walk(EMOJI_FILES_PATH):
                cls.EMOJI_FILES = files
        return cls.EMOJI_FILES


def get_image_for_emoji(emoji_str, files):
    cands = []
    for filename in files:
        if (u"%s.png" % emoji_str).upper() == filename.upper():
            cands.append(filename)
        elif (u"%s.0.png" % emoji_str).upper() == filename.upper():
            cands.append(filename)
    if cands:
        return cands[0]
    return None


def normalize_escape_seq(seq):
    new_seq = seq
    if new_seq[:2] == "\u":
        new_seq = new_seq[2:]
    if new_seq[:3] == "000":
        new_seq = new_seq[3:]
    return new_seq


def normalize_emoji_str(emoji):
    emoji_str = str(emoji.encode("unicode_escape")).lower()
    emoji_arr = emoji_str.split("\u")
    emoji_arr = ["u%s" % normalize_escape_seq(seq) for seq in emoji_arr if seq]
    emoji_str = "_".join(emoji_arr)
    return emoji_str


def get_emoji_im_for_unicode(emoji, size):
    files = EmojiFilesCache.get_emoji_files()
    normalized_emoji = normalize_emoji_str(emoji)
    filename = get_image_for_emoji(normalized_emoji, files)
    if not filename:
        # Try splitting the first part...maybe there was an
        # extra modifier on there.
        filename = get_image_for_emoji(normalized_emoji.split("_")[0], files)
    if filename:
        filepath = os.path.join(EMOJI_FILES_PATH, filename)
        emoji_im = Image.open(filepath)
        emoji_im.thumbnail(size, Image.ANTIALIAS)
        return emoji_im, filename
    return None, None


def draw_strs_and_images(im, from_point, strs_and_images, font=None, font_color=(255, 255, 255)):
    y_text = from_point[1]
    offset = 0
    for val in strs_and_images:
        # Draw the text
        if isinstance(val, basestring):
            if not font:
                font = ImageFont.truetype(AVENIR_MEDIUM_FONT_PATH, 40)

            draw = ImageDraw.Draw(im)
            draw.text((from_point[0] + offset, y_text), val, font_color, font=font)

            width, height = font.getsize(val)
            offset += width
        else:
            # Paste in the emoji
            im.paste(val, (from_point[0] + offset, int(y_text + 0.1 * val.height)), val)
            width, height = val.size
            offset += width


def get_strs_and_emojis_for_text(text, emoji_size=(38, 38)):
    # Get ordered text to write
    vals = []
    for txt in gc.grapheme_clusters(text):
        image_file, image_filename = get_emoji_im_for_unicode(txt, emoji_size)

        modifier = EmojiFilesCache.TONE_MODIFIER_MAP.get(image_filename)
        if modifier and len(vals) >= 1:
            last_emoji = vals[-1]
            filename = os.path.basename(last_emoji.filename)
            if filename.endswith(".0.png"):
                filename = filename[:-len(".0.png")]
                filename = "%s.%s.png" % (filename, modifier)
                filepath = os.path.join(EMOJI_FILES_PATH, filename)
                emoji_im = Image.open(filepath)
                emoji_im.thumbnail(emoji_size, Image.ANTIALIAS)
                vals[-1] = emoji_im
            else:
                vals.append(image_file)
        else:
            if image_file:
                vals.append(image_file)
            else:
                vals.append(txt)

    # Collapse text into contiguous strings punctuated by images
    result = []
    prev_idx = 0
    for idx, val in enumerate(vals):
        if not isinstance(val, basestring):
            res = ''.join(vals[prev_idx:idx])
            if res:
                result.append(res)
            result.append(val)
            prev_idx = idx + 1

    return vals


def colormoji_draw_text(im, text, from_point, font, font_color=(0, 0, 0), columns=100):
    y_pos = from_point[1]

    # Figure out the height of a line of text
    draw = ImageDraw.Draw(im)
    sizer_text = "m"
    _, height = draw.textsize(sizer_text, font=font)

    # Handle wrapping the text to fit on multiple lines
    lines = textwrap.wrap(text, width=columns)
    for line in lines:
        strs_and_images = get_strs_and_emojis_for_text(line, emoji_size=(height, height))
        new_from_point = (from_point[0], y_pos)
        draw_strs_and_images(im,
                             new_from_point,
                             strs_and_images,
                             font_color=font_color,
                             font=font)
        y_pos += height
    return y_pos
