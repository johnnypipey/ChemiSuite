# splashscreen.py
import tkinter as tk
from PIL import Image, ImageTk
import threading

# --------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------
SPLASH_IMAGE = "assets\Splash Screen.png"   # PNG with transparency
SCALE = 0.4                                  # Resize PNG (0.4 = 40%)
DURATION_MS = 5000                           # Show time in ms
TRANSPARENT_COLOR = "black"                  # Key color (not visible)
# --------------------------------------------------------

_splash_window = None

def show_splash():
    """Display the configured splash screen in a separate thread."""
    global _splash_window

    def run_splash():
        global _splash_window
        _splash_window = tk.Tk()
        _splash_window.overrideredirect(True)

        # Transparent background using alpha channel
        _splash_window.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        _splash_window.wm_attributes("-topmost", True)
        _splash_window.wm_attributes("-alpha", 1.0)
        _splash_window.config(bg=TRANSPARENT_COLOR)

        # Load and scale the PNG, preserving alpha channel
        img = Image.open(SPLASH_IMAGE)
        # Convert to RGBA if not already to preserve transparency
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        new_w = int(img.width * SCALE)
        new_h = int(img.height * SCALE)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)

        # Display image
        label = tk.Label(_splash_window, image=tk_img, bg=TRANSPARENT_COLOR, borderwidth=0, highlightthickness=0)
        label.pack(padx=0, pady=0)

        # Center the window
        sw = _splash_window.winfo_screenwidth()
        sh = _splash_window.winfo_screenheight()
        x = (sw - new_w) // 2
        y = (sh - new_h) // 2
        _splash_window.geometry(f"{new_w}x{new_h}+{x}+{y}")

        # Auto close after delay
        _splash_window.after(DURATION_MS, close_splash)
        _splash_window.mainloop()

    # Run splash in a separate thread so it doesn't block
    splash_thread = threading.Thread(target=run_splash, daemon=True)
    splash_thread.start()


def close_splash():
    """Close the splash screen if it's still open."""
    global _splash_window
    if _splash_window:
        try:
            _splash_window.destroy()
            _splash_window = None
        except:
            pass
