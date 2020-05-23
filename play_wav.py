#
# This file is part of the MicroPython ESP32 project
# 
# The MIT License (MIT)
#
# Copyright (c) 2019 Mike Teachman
# Copyright (c) 2020 Mauro Riva - lemariva.com
# https://opensource.org/licenses/MIT
# 
# working with M5Stack ATOM Echo

  
from machine import I2S
from machine import Pin
from config import *

SAMPLES_PER_SECOND = 44100

bck_pin = Pin(device_config['bck'])     # Bit clock output
ws_pin = Pin(device_config['ws'])       # Word clock output
sdout_pin = Pin(device_config['sdout']) # Serial data output
sdin_pin = Pin(device_config['sdin'])   # Serial data output


# channelformat settings:
#    stereo WAV:  channelformat=I2S.RIGHT_LEFT
#    mono WAV:    channelformat=I2S.ONLY_RIGHT
audio_out = I2S(I2S.NUM1, bck=bck_pin, ws=ws_pin, sdout=sdout_pin, 
              standard=I2S.PHILIPS, mode=I2S.MASTER_TX,
              dataformat=I2S.B16, channelformat=I2S.ONLY_RIGHT,
              samplerate=SAMPLES_PER_SECOND,
              dmacount=8, dmalen=512)

s = open('test-audio.wav','rb')
s.seek(44) # advance to first byte of Data section in WAV file

# continuously read audio samples from the WAV file 
# and write them to an I2S DAC
while True:
    try:
        audio_samples = bytearray(s.read(1024))
        numwritten = 0
        if len(audio_samples) == 0:
            s.seek(44) # advance to first byte of Data section
        else:
            # loop until samples can be written to DMA
            while numwritten == 0:
                # return immediately when no DMA buffer is available (timeout=0)
                numwritten = audio_out.write(audio_samples, timeout=0)
                
                # await - allow other coros to run   
    except KeyboardInterrupt:  
        s.close()
        audio_out.deinit()
        break