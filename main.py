import audiocore
import board
import audiobusio
import sdcardio
import storage
import terminalio
import displayio
import busio
import digitalio
import time
from adafruit_display_text import label
from adafruit_st7735r import ST7735R

pin = digitalio.DigitalInOut(board.GP17)
pin.direction = digitalio.Direction.OUTPUT
pin.value = True
try:
    from fourwire import FourWire
except ImportError:
    from displayio import FourWire

displayio.release_displays()

spi = busio.SPI(board.GP18, MOSI=board.GP19, MISO=board.GP16)
tft_cs = board.GP20
tft_dc = board.GP22
sd_cs = board.GP21

sdcard = sdcardio.SDCard(spi, sd_cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")
audio = audiobusio.I2SOut(bit_clock=board.GP10, word_select=board.GP11, data=board.GP9)
display_bus = FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=board.GP26)
display = ST7735R(display_bus, width=160, height=128, rotation=270, bgr=True)

color_bitmap = None
splash = None
bg_sprite = None
inner_bitmap = None
text_group = None

def display_song(song_list, index):
    global color_bitmap, display, splash, bg_sprite, inner_bitmap, text_group
    splash = displayio.Group()
    display.root_group = splash
    color_bitmap = displayio.Bitmap(160, 128, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0x000000
    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite)

    inner_bitmap = displayio.Bitmap(160, 43, 1)
    inner_palette = displayio.Palette(1)
    inner_palette[0] = 0xffffff
    inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=0, y=0)
    splash.append(inner_sprite)

    text_group = displayio.Group(scale=1, x=10, y=12)
    text_area = label.Label(terminalio.FONT, text=song_list[index], color=0x000000)
    text_group.append(text_area)
    splash.append(text_group)

    text_group = displayio.Group(scale=1, x=10, y=55)
    text_area = label.Label(terminalio.FONT, text="press d to play/pause\na to go back", color=0xffffff)
    text_group.append(text_area)
    splash.append(text_group)


def display_menu(items, index):
    global color_bitmap, display, splash, bg_sprite, inner_bitmap, text_group
    splash = displayio.Group()
    display.root_group = splash
    color_bitmap = displayio.Bitmap(160, 128, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0x000000
    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite)

    inner_bitmap = displayio.Bitmap(160, 43, 1)
    inner_palette = displayio.Palette(1)
    inner_palette[0] = 0xffffff
    inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=0, y=42)
    splash.append(inner_sprite)

    text_group1 = displayio.Group(scale=1, x=10, y=10)
    text_area1 = label.Label(terminalio.FONT, text=items[index - 1], color=0xffffff)
    text_group1.append(text_area1)
    splash.append(text_group1)

    text_group2 = displayio.Group(scale=1, x=10, y=55)
    text_area2 = label.Label(terminalio.FONT, text=items[index], color=0x000000)
    text_group2.append(text_area2)
    splash.append(text_group2)

    text_group3 = displayio.Group(scale=1, x=10, y=100)
    text_area3 = label.Label(terminalio.FONT, text=items[index + 1 if index + 1 < len(items) else 0], color=0xffffff)
    text_group3.append(text_area3)
    splash.append(text_group3)
    splash = None


# You have to get audio yourself, this is only an example:
songs = {
    "The Spectre\nby Alan Walker": "/sd/spectre.wav",
    "Not You - Instrumental\nby Alan Walker": "/sd/notyou.wav",
    "Bad Apple!!\nby Somebody": "/sd/badapple.wav"
}
titles = list(songs.keys())

current_index = 0
display_menu(list(songs.keys()), current_index)
wpin = digitalio.DigitalInOut(board.GP5)
wpin.pull = digitalio.Pull.UP
spin = digitalio.DigitalInOut(board.GP7)
spin.pull = digitalio.Pull.UP
apin = digitalio.DigitalInOut(board.GP6)
apin.pull = digitalio.Pull.UP
dpin = digitalio.DigitalInOut(board.GP8)
dpin.pull = digitalio.Pull.UP

while True:
    if not wpin.value:
        current_index -= 1
        current_index %= len(titles)
        display_menu(titles, current_index)
        time.sleep(0.05)
        while not wpin.value:
            pass
        time.sleep(0.05)

    elif not spin.value:
        current_index += 1
        current_index %= len(titles)
        display_menu(titles, current_index)
        time.sleep(0.05)
        while not spin.value:
            pass
        time.sleep(0.05)

    elif not dpin.value:
        display_song(titles, current_index)
        while apin.value:
            if not dpin.value:
                print("pressed")
                print(songs[titles[current_index]])
                wave_file = open(songs[titles[current_index]], "rb")
                print("opened")
                wave = audiocore.WaveFile(wave_file)
                print("loaded audio")
                audio.play(wave)
                time.sleep(0.05)
                while not dpin.value:
                    pass
                time.sleep(0.05)
                while audio.playing or audio.paused:
                    if not dpin.value:
                        if audio.paused:
                            audio.resume()
                        else:
                            audio.pause()
                        time.sleep(0.05)
                        while not dpin.value:
                            pass
                        time.sleep(0.05)
                    elif not apin.value:
                        audio.stop()
                        break
                break	
        display_menu(titles, current_index)

