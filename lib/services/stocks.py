from lib.resources import Resources
from PIL import Image, ImageDraw, ImageFont
import requests

class Stocks:
    def __init__(self, config, resources: Resources):
        self.config = config
        self.resources = resources

    def render(self, image: Image):
        headers = {'User-Agent': 'eink-dashbot/1.0 (+https://github.com/jackwickham)'}
        draw = ImageDraw.Draw(image)
        x = 0
        for symbol in self.config['symbols']:
            value = requests.get(
                    "https://query1.finance.yahoo.com/v8/finance/chart/" + symbol,
                    headers = headers
                ).json()['chart']['result'][0]['meta']['regularMarketPrice']
            text = "{}: {}".format(symbol, value)
            text_len = draw.textlength(text, font=self.resources.font_small())
            draw.text((x, 0), text, fill=0, font=self.resources.font_small())
            x += text_len + 5
