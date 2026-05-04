import tkinter as tk
from PIL import Image, ImageTk
import mss
import keyboard
from datetime import datetime
import threading

class ScreenSnipper:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Screen Snipper - Press F5 to start snipping")
        self.root.geometry("300x150")
        self.root.configure(bg='#2b2b2b')
        
        # UI
        label = tk.Label(self.root, text="Press F5 to snip\nClick and drag to select region\nPress ESC to cancel", 
                         bg='#2b2b2b', fg='white', font=('Arial', 12))
        label.pack(expand=True)
        
        self.status = tk.Label(self.root, text="Ready", bg='#2b2b2b', fg='#00ff00')
        self.status.pack()
        
        self.snipping = False
        self.selection_window = None
        
        # Hotkey
        keyboard.add_hotkey('f5', self.start_snipping)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def start_snipping(self):
        """Start the snipping tool"""
        if self.snipping:
            return
        
        self.snipping = True
        self.status.config(text="Snipping... Select area")
        
        # Create fullscreen overlay for selection
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.attributes('-alpha', 0.3)
        self.selection_window.configure(bg='black', cursor='cross')
        
        # Variables for selection
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        # Bind mouse events
        self.selection_window.bind('<ButtonPress-1>', self.on_mouse_down)
        self.selection_window.bind('<B1-Motion>', self.on_mouse_drag)
        self.selection_window.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.selection_window.bind('<Escape>', self.cancel_snipping)
        
        # Bring to front
        self.selection_window.lift()
        self.selection_window.focus_force()
    
    def on_mouse_down(self, event):
        """Start selection"""
        self.start_x = event.x_root
        self.start_y = event.y_root
        
        # Create rectangle
        self.rect = tk.Canvas(self.selection_window, highlightthickness=0)
        self.rect.place(x=self.start_x, y=self.start_y, width=0, height=0)
    
    def on_mouse_drag(self, event):
        """Update selection"""
        if self.rect and self.start_x and self.start_y:
            current_x = event.x_root
            current_y = event.y_root
            
            width = abs(current_x - self.start_x)
            height = abs(current_y - self.start_y)
            x = min(self.start_x, current_x)
            y = min(self.start_y, current_y)
            
            self.rect.place(x=x, y=y, width=width, height=height)
            self.rect.configure(bg='white', bd=2)
    
    def on_mouse_up(self, event):
        """Capture the selected region"""
        if self.rect and self.start_x and self.start_y:
            end_x = event.x_root
            end_y = event.y_root
            
            # Calculate region
            x = min(self.start_x, end_x)
            y = min(self.start_y, end_y)
            width = abs(end_x - self.start_x)
            height = abs(end_y - self.start_y)
            
            if width > 5 and height > 5:  # Minimum size
                self.capture_region(x, y, width, height)
        
        self.cancel_snipping()
    
    def cancel_snipping(self, event=None):
        """Cancel snipping"""
        if self.selection_window:
            self.selection_window.destroy()
            self.selection_window = None
        self.snipping = False
        self.status.config(text="Ready - Press F5 to snip")
    
    def capture_region(self, x, y, width, height):
        """Capture the selected region"""
        try:
            with mss.mss() as sct:
                # Define region
                region = {
                    'left': x,
                    'top': y,
                    'width': width,
                    'height': height
                }
                
                # Capture
                screenshot = sct.grab(region)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                
                # Save
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"snipped_{timestamp}.png"
                img.save(filename)
                
                # Show result
                img.show()
                
                self.status.config(text=f"✓ Saved: {filename}")
                print(f"✓ Captured region ({width}x{height}) - {filename}")
                
        except Exception as e:
            self.status.config(text=f"Error: {e}")
            print(f"Error: {e}")
    
    def on_closing(self):
        """Clean exit"""
        keyboard.unhook_all()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ScreenSnipper()
    app.run()