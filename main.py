import gc
import bluetooth
from micropython import const
from machine import I2S
from machine import Pin
import neopixel
from config import *
from ble_advertising import advertising_payload

## audio setup
SAMPLES_PER_SECOND = 44100

bck_pin = Pin(device_config['bck'])     # Bit clock output
ws_pin = Pin(device_config['ws'])       # Word clock output
sdout_pin = Pin(device_config['sdout']) # Serial data output
sdin_pin = Pin(device_config['sdin'])   # Serial data output

audio_out = I2S(I2S.NUM1, bck=bck_pin, ws=ws_pin, sdout=sdout_pin, 
              standard=I2S.PHILIPS, mode=I2S.MASTER_TX,
              dataformat=I2S.B16, channelformat=I2S.ONLY_RIGHT,
              samplerate=SAMPLES_PER_SECOND,
              dmacount=6, dmalen=1024)

#LED
np = neopixel.NeoPixel(Pin(device_config['led']), 1)

## ble setup
_IRQ_CENTRAL_CONNECT                 = const(1 << 0)
_IRQ_CENTRAL_DISCONNECT              = const(1 << 1)

_DEVICE_UUID = bluetooth.UUID(0x180A)

_AUDIO_UUID = bluetooth.UUID('d9d55015-0525-4e5c-be77-afada8e04e14')
_AUDIO_ON_CHAR = (bluetooth.UUID('d9d55016-0525-4e5c-be77-afada8e04e14'), bluetooth.FLAG_WRITE,)
_AUDIO_SERVICES = (_AUDIO_UUID, (_AUDIO_ON_CHAR,),)

SERVICES =  (_AUDIO_SERVICES,)
_ADV_APPEARANCE_AUDIO= const(1088)

class M5StackBLE:
    def __init__(self, ble, name='m5stack-speaker'):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(handler=self._irq)
        
        ((self._handle_audio,),) = self._ble.gatts_register_services(SERVICES)

        self._connections = set()
        self._payload = advertising_payload(name=name, services=[_DEVICE_UUID], appearance=_ADV_APPEARANCE_AUDIO)
        self._advertise()

    def update_data(self):
        # Read data from central
        audio_data = self._ble.gatts_read(self._handle_audio)
        audio_data = int.from_bytes(audio_data, "big")
        return audio_data

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _, = data
            self._connections.add(conn_handle)
            np[0] = (0, 255, 0)
            np.write()
        elif event == _IRQ_CENTRAL_DISCONNECT:
            np[0] = (255, 0, 0)
            conn_handle, _, _, = data
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

## BLUETOOTH
ble = bluetooth.BLE()
ble_module = M5StackBLE(ble)
np[0] = (255, 0, 0)
np.write()

while True:
    audio_track = ble_module.update_data()
    stop = False

    if audio_track == 1:
        track = open('audio_nr0.wav','rb')
    elif audio_track == 2:
        track = open('audio_nr1.wav','rb')
    elif audio_track == 3:
        track = open('audio_nr3.wav','rb')
    else:
        track = None

    if track is not None:
        track.seek(44)
        while not stop:
            try:
                audio_samples = bytearray(track.read(256))
                numwritten = 0
                if len(audio_samples) == 0:
                    stop = True
                else:
                    # loop until samples can be written to DMA
                    while numwritten == 0:
                        # return immediately when no DMA buffer is available (timeout=0)
                        numwritten = audio_out.write(audio_samples, timeout=0)
                        
                        # await - allow other coros to run   
            except KeyboardInterrupt:  
                track.close()
                audio_out.deinit()
                break
            gc.collect()
            
    gc.collect()