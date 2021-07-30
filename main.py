#!/usr/bin/python3
# -*- coding:utf-8 -*-

import datetime
from lib.display import Display
from lib.resources import Resources
from lib.services.stocks import Stocks
from lib.services.todoist import Todoist
from lib.services.weather import Weather
import logging
import os
from PIL import Image, ImageDraw
import sys
import time
import traceback
import yaml

logging.basicConfig(level=logging.DEBUG)

def should_refresh(config, last_refresh: datetime.datetime, now: datetime.datetime) -> bool:
    for refresh_time in config['refresh']:
        t = datetime.time.fromisoformat(refresh_time)
        if last_refresh.time() < t and now.time() >= t:
            return True
    return False

with open("config.yml", 'r') as conf_file:
    try:
        config = yaml.safe_load(conf_file)
    except yaml.YAMLError as e:
        logging.error("Exception while parsing config: {}", e)
        sys.exit(1)

try:
    logging.info("Initialising...")
    display = Display(invert = True)
    resources = Resources(os.path.join(os.path.dirname(__file__), 'resources'))

    weather = Weather(config['weather'], resources)
    todoist = Todoist(config['todoist'], resources)
    stocks = Stocks(config['stocks'], resources)

    last_refresh = datetime.datetime.now()

    while True:
        try:
            image = Image.new('1', (display.DISPLAY_WIDTH, display.DISPLAY_HEIGHT), 255)

            weather_image = Image.new('1', (160, display.DISPLAY_HEIGHT), 255)
            weather.render(weather_image)
            image.paste(weather_image, box=(480, 0))

            todoist_image = Image.new('1', (display.DISPLAY_WIDTH - 160, display.DISPLAY_HEIGHT - 40), 255)
            todoist.render(todoist_image)
            image.paste(todoist_image, box=(0, 0))

            stocks_image = Image.new('1', (display.DISPLAY_WIDTH - 160, 20), 255)
            stocks.render(stocks_image)
            image.paste(stocks_image, box=(10, display.DISPLAY_HEIGHT - 30))

            now = datetime.datetime.now()
            refresh = should_refresh(config, last_refresh, now)
            last_refresh = now
        except Exception:
            logging.exception("Exception while rendering image")
            image = Image.new('1', (display.DISPLAY_WIDTH, display.DISPLAY_HEIGHT), 255)
            draw = ImageDraw.Draw(image)
            stacktrace = "".join(traceback.format_exc())
            draw.text((10, 10), 'Exception', fill=0, font=resources.font_large())
            draw.multiline_text((10, 60), stacktrace, fill=0, font=resources.font_small())
            refresh = True

        display.update(image.getdata(), refresh)

        time.sleep(15 * 60)

except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    sys.exit(0)