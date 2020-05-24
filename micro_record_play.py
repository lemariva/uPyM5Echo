# Copyright 2020 Mauro Riva - lemariva.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0#
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from machine import I2S
from machine import Pin
from config import *
import time

bck_pin = Pin(device_config['bck'])     # Bit clock output
ws_pin = Pin(device_config['ws'])       # Word clock output
sdout_pin = Pin(device_config['sdout']) # Serial data output
sdin_pin = Pin(device_config['sdin'])   # Serial data output

samples = bytearray(36000)

audio_in = I2S(I2S.NUM0,                                  # create I2S peripheral to read audio
               ws=ws_pin, sdin=sdin_pin,                  # 
               standard=I2S.PHILIPS, mode=I2S.MASTER_PDW, # 
               dataformat=I2S.B16,                        # 
               channelformat=I2S.ONLY_LEFT,
               samplerate=8000, 
               dmacount=8,dmalen=512)

num_bytes_read = bytes(audio_in.readinto(samples))

time.sleep_ms(2000)

audio_out = I2S(I2S.NUM1,                                  # create I2S peripheral to write audio
                bck=bck_pin, ws=ws_pin, sdout=sdout_pin,    # sample data to an Adafruit I2S Amplifier
                standard=I2S.PHILIPS, mode=I2S.MASTER_TX,  # breakout board, 
                dataformat=I2S.B16,                        # based on NS4168 device
                channelformat=I2S.ONLY_LEFT,
                samplerate=8000, 
                dmacount=8,dmalen=512)

num_bytes_written = audio_out.write(samples) 
