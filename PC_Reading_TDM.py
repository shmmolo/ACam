import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


import time
import serial
import numpy as np
import soundfile as sf
from acoular import TimeSamples
from traits.api import Any

# Match this to your Teensy’s actual sample rate:
AUDIO_SAMPLE_RATE = 44100

class SerialTimeSamples(TimeSamples):
    """Read int32 blocks from Teensy via USB-Serial and expose as floats to Acoular."""
    # Declare everything we want to set via __init__ as Traits:
    ser          = Any()
    port         = Any()
    baudrate     = Any()
    n_channels   = Any()
    block_len    = Any()
    bit_depth    = Any()
    _data_buffer = Any()
    freq         = Any()
    m            = Any()

    def __init__(self,
                 port: str,
                 baudrate: int    = 2_000_000,
                 n_channels: int  = 16,
                 block_len: int   = 32,
                 bit_depth: int   = 24):
        super().__init__()               # init Acoular’s TimeSamples machinery
        # Store parameters as traits
        self.port       = port
        self.baudrate   = baudrate
        self.n_channels = n_channels
        self.block_len  = block_len
        self.bit_depth  = bit_depth
        self._data_buffer = None

        # For Acoular
        self.freq = AUDIO_SAMPLE_RATE     # sampling rate
        self.m    = self.n_channels       # number of channels

        # Open & flush the serial port
        self.ser = serial.Serial(self.port,
                                 self.baudrate,
                                 timeout=2)
        # Give Teensy a moment to reboot on open:
        time.sleep(0.1)
        self.ser.reset_input_buffer()

    def result(self, num=None):
        """Read one block (or `num` samples) and return an array of shape (num, n_channels)."""
        if num is None:
            num = self.block_len
        total_bytes = self.n_channels * self.block_len * 4
        raw = self.ser.read(total_bytes)

        # ── DEBUG: show we actually got raw binary!
        print(f"DEBUG: read {len(raw)} bytes, head={raw[:16].hex()} …")

        if len(raw) < total_bytes:
            raise IOError(f"Timeout: expected {total_bytes} bytes, got {len(raw)}")

        # Interpret as little-endian int32 and reshape
        arr = np.frombuffer(raw, dtype='<i4')
        arr = arr.reshape(self.block_len, self.n_channels)

        # Normalize to float32 in [-1, +1]
        norm = float((2**(self.bit_depth - 1)) - 1)
        self._data_buffer = arr.astype(np.float32) / norm

        # Slice off `num` samples and return
        out = self._data_buffer[:num, :]
        self._data_buffer = (
            self._data_buffer[num:, :]
            if num < self.block_len else None
        )
        return out

    def close(self):
        """Close serial port."""
        if self.ser and self.ser.is_open:
            self.ser.close()


if __name__ == "__main__":
    # Simple infinite loop to prove data is coming in
    sts = SerialTimeSamples(
        port="COM7",
        baudrate=2_000_000,
        n_channels=16,
        block_len=32,
        bit_depth=24
    )
    ##try:
    ##    while True:
    ##        block = sts.result()
    ##        print(f"→ block shape {block.shape}, "
    ##              f"min={block.min():.3f}, max={block.max():.3f}")
    ##except KeyboardInterrupt:
    ##    print("Interrupted, cleaning up…")
    ##finally:
    ##    sts.close()
    
    frames = []
    try:
        print("Recording... press Ctrl+C to stop.")
        while True:
            block = sts.result()
            frames.append(block)
            print(f"-> got block {len(frames):4d}: shape={block.shape}")
    except KeyboardInterrupt:
        print("\nRecording stopped, now saving…")
    finally:
        sts.close()

    # Stack all frames into a single (N_samples, n_channels) array
    data = np.vstack(frames)

    # Write a multi-channel WAV
    sf.write("MultiChannel.wav", data, sts.freq)
    print(f"Saved multi-channel WAV: MultiChannel.wav  (shape={data.shape})")

    # Write just channel 0 as mono WAV
    mono = data[:, 0]
    sf.write("MonoChannel.wav", mono, sts.freq)
    print(f"Saved mono WAV: MonoChannel.wav  (length={len(mono)})")
