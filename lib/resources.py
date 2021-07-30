import os
from PIL import Image, ImageFont

class Resources:
    def __init__(self, resources_dir):
        self._resources_dir = resources_dir

        font_file = os.path.join(resources_dir, 'Font.ttc')
        self._font_small = ImageFont.truetype(font_file, 18)
        self._font_medium = ImageFont.truetype(font_file, 24)
        self._font_large = ImageFont.truetype(font_file, 30)

    def font_small(self) -> ImageFont:
        return self._font_small

    def font_medium(self) -> ImageFont:
        return self._font_medium

    def font_large(self) -> ImageFont:
        return self._font_large

    def icon(self, name: str) -> Image:
        return Image.open(os.path.join(self._resources_dir, 'icons', 'bmp', name + '.bmp'))
