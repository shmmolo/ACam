# overlay_server.py

# 1. Use the non-GUI Agg backend before importing pyplot
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Flask, send_file, request
from flask_cors import CORS
import io
import atexit

# 2. Your beamforming helper
from teest import get_Lm, rg, close as close_beam

app = Flask(__name__)
CORS(app)  # allow cross-origin requests from your browser

# 3. Prevent browser caching
@app.after_request
def add_no_cache(resp):
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/overlay.png')
def overlay():
    """
    Each time /overlay.png is requested:
      a) pull one fresh Lm (2D dB map)
      b) render it to a transparent PNG
      c) return it with no caching
    """
    # 4. Optional query params to control size & opacity
    width  = request.args.get('w', type=int,   default=400)
    height = request.args.get('h', type=int,   default=400)
    alpha  = request.args.get('alpha', type=float, default=0.6)

    # 5. Grab your beamformed map
    Lm = get_Lm()                       # shape=(nx,ny)

    # 6. Create a figure exactly the right size
    fig, ax = plt.subplots(
        figsize=(width/100, height/100),  # inches = px / dpi
        dpi=100
    )
    # 7. Make both figure and axes backgrounds transparent
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)

    # 8. Draw the dB map
    im = ax.imshow(
        Lm.T,                            # transpose so x/y align
        origin='lower',
        extent=rg.extend(),              # real-world coordinates
        cmap='viridis',
        vmin= Lm.max() - 15,             # e.g. show only top 15 dB
        vmax= Lm.max(),
        alpha=alpha
    )
    ax.set_axis_off()                   # drop ticks & border

    # 9. Remove all margins so PNG is tight around your map
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # 10. Render to an in-memory buffer
    buf = io.BytesIO()
    fig.savefig(
        buf,
        format='png',
        transparent=True,
        bbox_inches='tight',
        pad_inches=0
    )
    plt.close(fig)
    buf.seek(0)

    # 11. Send it back as a PNG (no unsupported args here)
    return send_file(buf, mimetype='image/png')


# 12. Clean up your serial port when Flask exits
atexit.register(close_beam)

if __name__ == '__main__':
    # threaded=True lets multiple clients (video+overlay) hit this endpoint
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)
