from acoular import TimeSamples, MicGeom, RectGrid, SteeringVector, BeamformerTime, TimePower, TimeAverage, L_p
import numpy as np
from scipy.io import wavfile # For reading .wav File
import matplotlib.pyplot as plt # For plotting
from matplotlib.animation import FuncAnimation # For animation

# Loading Recorded .wav File
fs, wav = wavfile.read("recording_multich.wav")
fs = 44100 # Setting Sampling Frequency of Mics at 44.1kHz

# Beamforming Pipeline 
ts = TimeSamples(data=wav, sample_freq=fs) # Hand Off to Acoular
mg = MicGeom(file="array_16.xml") # Load Microphone Geometry for Steering Vector calculation
rg = RectGrid(x_min=-0.5, x_max=0.5, y_min=-0.5, y_max=0.5, z=0.5, increment=0.01) # Define the Window Grid
st = SteeringVector(grid=rg, mics=mg) # Calculate Steering Vector Based On Geometry and Grid

bt  = BeamformerTime(source=ts, steer=st) # Do Beamforming (Find Correlation B/W Souce and Steering Vectors)
pt  = TimePower(source=bt) # Calculate Signal Power
avg = TimeAverage(source=pt, naverage=200) # Linear Average of Samples (One Block With 200 Samples)


# Plotting and Animation
fig, ax = plt.subplots(figsize=(6,6))
# Initialize Empty Image: 2D array of zeros, origin at lower left corner, array indices from RectGrid, color scale
im = ax.imshow(np.zeros(rg.shape).T, origin='lower', extent=rg.extend())
cbar = fig.colorbar(im, ax=ax) # Attaching Color Bar 
cbar.set_label('normalized SPL') # Labeling Color Bar

frame_gen = avg.result(1)  # generator over averaged frames

def update(i):
    r  = next(frame_gen) # Get Next Averaged Block
    pm = r[0].reshape(rg.shape) # Flatten + Reshaped For 2D Power Map
    Lm = L_p(pm) # Converting to dB
    data = Lm.reshape(rg.shape).T 
    im.set_data(data) # Updating im (Already Initialized Image)
    im.set_clim(data.min(), data.max()) # Color Scale Adjustment
    ax.set_title(f"Output Map (frame {i+1})") # Title
    return [im]

# Animating: draws in fig, calls update for each frame, number of frames, playback speed, smooth graphing
ani = FuncAnimation(fig, update, frames=range(30), interval=200, blit=True, repeat=False)
plt.show()