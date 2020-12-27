# The specification for the display can be found at
# http://www.waveshare.net/w/upload/b/b6/7.5inch-e-paper-specification.pdf
# The specification has a number of inconsistencies, but this code seems to
# work.
#
# I referred to the waveshare examples to construct this. They can be found at
# https://github.com/waveshare/e-Paper/tree/master/RaspberryPi_JetsonNano/python

import gpiozero
from typing import Union, Iterable
import time
import logging
import spidev

class Display:
    DISPLAY_WIDTH    = 640
    DISPLAY_HEIGHT   = 384

    PIXEL_WHITE = 0b11
    PIXEL_BLACK = 0b00
    PIXEL_WHITE_NO_REFRESH = 0b10
    PIXEL_BLACK_NO_REFRESH = 0b01

    def __init__(self):
        self.reset_pin = gpiozero.DigitalOutputDevice(17, active_high=False)
        self.command_mode = gpiozero.DigitalOutputDevice(
            25, active_high=False, initial_value=True)
        self.chip_select = gpiozero.DigitalOutputDevice(8, active_high=False)
        self.busy_pin = gpiozero.DigitalInputDevice(24, None, False)

        self.spi = None
        self.prev_image = None

    def _send_command(self, command: int):
        # Switch to command mode
        self.command_mode.on()
        # Send the command
        self._send_spi([command])

    def _send_data(self, data: Iterable[int]):
        if isinstance(data, int):
            data = [data]
        # Switch to data mode and enable the chip
        self.command_mode.off()
        # Send the data
        self._send_spi(data)

    def _send_spi(self, data: Iterable[int]) -> None:
        for item in data:
            self.chip_select.on()
            self.spi.writebytes([item])
            self.chip_select.off()

    def _read_spi(self) -> int:
        return self.spi.readbytes(1)[0]

    def _wait_for_busy(self, timeout = None) -> None:
        time.sleep(0.05)
        return self.busy_pin.wait_for_inactive(timeout)

    def _enable(self) -> None:
        self.spi = spidev.SpiDev(0, 0)
        self.spi.mode = 0b00
        self.spi.max_speed_hz = 4000000

        # Assert reset (clear any config and wake from deep sleep)
        self.reset_pin.off()
        time.sleep(0.2)
        self.reset_pin.on() 
        time.sleep(0.01)
        self.reset_pin.off()
        time.sleep(0.2)

        # Initialise a bunch of stuff - I don't know what half of it really does
        # or whether it is all needed, but certainly some of it is and the order
        # matters at least in some cases.

        # Power setting
        self._send_command(0b00000001)
        self._send_data([0x37, 0x00])

        # Panel settings
        self._send_command(0x00)
        self._send_data(0xCF)
        self._send_data(0x08)

        # Booster soft start
        self._send_command(0b00000110)
        self._send_data([0xC7, 0xCC, 0x28])

        # Power on
        self._send_command(0b00000100)

        if not self._wait_for_busy(5):
            raise SystemError("Initialisation wait timeout - device not available")

        # PLL Control
        self._send_command(0b00110000)
        self._send_data([0x3C])

        # VCOM and data interval
        self._send_command(0b001010000)
        self._send_data(0b01110111)
        
        # TCON
        self._send_command(0x60)
        self._send_data(0x22)

        # Display resolution
        self._send_command(0b01100001)
        self._send_data([
            self.DISPLAY_WIDTH >> 8, self.DISPLAY_WIDTH & 0xFF,
            self.DISPLAY_HEIGHT >> 8, self.DISPLAY_HEIGHT & 0xFF
        ])
        
        # Voltage setting
        self._send_command(0x82)
        self._send_data(0x1E)
        
        # Flash mode
        self._send_command(0xE5)
        self._send_data(0x03)

        # All set up and ready to send the image
        logging.debug("Initialised")

    def _disable(self) -> None:
        if self.spi is not None:
            #  Power off
            self._send_command(0b00000010)
            if not self._wait_for_busy(5):
                logging.warning("Power off wait timeout")
            # Deep sleep
            self._send_command(0b00000111)
            self._send_data([0b10100101])
            # Shut down SPI
            self.spi.close()
            # Set the other pins, apparently this is necessary
            self.reset_pin.on()
            self.command_mode.on()

            logging.debug("Shut down SPI")

    def _get_pixel_value(self, pixel: bool, index: int) -> int:
        if pixel:
            if self.prev_image is not None and self.prev_image[index]:
                return self.PIXEL_BLACK_NO_REFRESH
            else:
                return self.PIXEL_BLACK
        else:
            if self.prev_image is not None and not self.prev_image[index]:
                return self.PIXEL_WHITE_NO_REFRESH
            else:
                return self.PIXEL_WHITE

    def _send_image(self, data: Iterable[bool]) -> None:
        if len(data) != self.DISPLAY_WIDTH * self.DISPLAY_HEIGHT:
            logging.error("Image did not have correct dimensions")
        # Start data transmission
        self._send_command(0x10)
        # Then send the pixels
        for i in range(0, self.DISPLAY_WIDTH * self.DISPLAY_HEIGHT, 2):
            self._send_data((self._get_pixel_value(data[i], i) << 4) | self._get_pixel_value(data[i+1], i+1))
        # Display refresh
        self._send_command(0x12)
        logging.debug("sent image data")
        self.prev_image = data
        # Wait for it to finish updating
        if not self._wait_for_busy(40):
            logging.warning("Busy pin didn't go low in time")

    def update(self, image: Iterable[bool]) -> None:
        try:
            self._enable()
            self._send_image(image)
        finally:
            self._disable()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    display = Display()
    display.update((([True] * (display.DISPLAY_WIDTH // 2)) + ([False] * (display.DISPLAY_WIDTH // 2))) * display.DISPLAY_HEIGHT)
