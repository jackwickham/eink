from datetime import datetime
from lib.resources import Resources
import logging
from PIL import Image, ImageDraw
import requests


class Weather:
    def __init__(self, config, resources: Resources):
        self.config = config
        self.resources = resources

    def render(self, image: Image):
        response = requests.get("https://api.openweathermap.org/data/2.5/onecall", params={
            'lat': self.config['lat'],
            'lon': self.config['long'],
            'appid': self.config['key'],
            'units': 'metric'}).json()

        draw = ImageDraw.Draw(image)
        
        title_len = int(draw.textlength('Weather', font=self.resources.font_large()))
        draw.text(((image.width - title_len) // 2, 10), 'Weather', fill=0, font=self.resources.font_large())

        self._draw_weather('Current', response['current']['weather'][0]['id'], response['current']['temp'], 60, image, draw)
        self._draw_weather('Next Hour', response['hourly'][1]['weather'][0]['id'], response['hourly'][1]['temp'], 170, image, draw)
        if datetime.now().hour >= 18:
            self._draw_weather('Tomorrow', response['daily'][1]['weather'][0]['id'], response['daily'][1]['temp']['day'], 280, image, draw)
        else:
            self._draw_weather('Today', response['daily'][0]['weather'][0]['id'], response['daily'][0]['temp']['day'], 280, image, draw)

    # https://openweathermap.org/weather-conditions#Weather-Condition-Codes-2
    def _get_icon(code: int) -> str:
        if code < 200:
            logging.warn("Unknown weather code {}", code)
            return 'Moon-New'
        elif code < 300:
            return 'Cloud-Lightning'
        elif code < 400:
            return 'Cloud-Drizzle'
        elif code < 500:
            logging.warn("Unknown weather code {}", code)
            return 'Moon-New'
        elif code < 510:
            return 'Cloud-Rain'
        elif code < 520:
            return 'Cloud-Snow-Alt'
        elif code < 600:
            return 'Cloud-Rain-Sun'
        elif code < 700:
            return 'Cloud-Snow-Alt'
        elif code < 800:
            return 'Cloud-Fog'
        elif code == 800:
            return 'Sun'
        elif code < 804:
            return 'Cloud-Sun'
        elif code == 804:
            return 'Cloud'
        else:
            logging.warn("Unknown weather code {}", code)
            return 'Moon-New'

    def _draw_weather(self, label: str, weather_code: int, temp: float, y: int, image: Image, draw: ImageDraw):
        icon = self.resources.icon(Weather._get_icon(weather_code))
        image.paste(icon, (10, y + 30))

        temp_text = "{}°C".format(round(temp))
        temp_len = int(draw.textlength("30°C", font=self.resources.font_medium()))
        draw.text((image.width - 10 - temp_len, y + 40), temp_text, fill=0, font=self.resources.font_medium())

        text_len = int(draw.textlength(label, font=self.resources.font_medium()))
        draw.text(((image.width - text_len) // 2, y), label, fill=0, font=self.resources.font_medium())
