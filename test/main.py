import mss
from datetime import datetime
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
from pynput import keyboard

class ScreenCaptureViewer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Screen Capture Tool - Press G to Capture")
        self.root.geometry("900x700")
        self.root.configure(bg='#2b2b2b')
        
        # Create UI
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_var = tk.StringVar(value="Ready - Press 'G' to capture screen")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Arial", 12, "bold"))
        status_label.pack(pady=(0, 10))
        
        # Image display
        self.canvas = tk.Canvas(main_frame, bg='#1e1e1e', height=500)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.image_label = ttk.Label(self.canvas, background='#1e1e1e')
        self.canvas.create_window((0, 0), window=self.image_label, anchor='nw')
        
        # Info
        self.info_var = tk.StringVar(value="No captures yet")
        info_label = ttk.Label(main_frame, textvariable=self.info_var, font=("Arial", 9))
        info_label.pack(pady=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        capture_btn = ttk.Button(button_frame, text="📸 Capture (G)", command=self.capture_screen)
        capture_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(button_frame, text="🗑️ Clear", command=self.clear_image)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.current_image = None
        
        # Start keyboard listener in separate thread
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.daemon = True
        self.listener.start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_key_press(self, key):
        """Handle key press events"""
        try:
            # Check for 'g' key
            if hasattr(key, 'char') and key.char == 'g':
                print("G key pressed!")
                # Schedule capture in main thread
                self.root.after(0, self.capture_screen)
            # Check for F5
            elif key == keyboard.Key.f5:
                print("F5 key pressed!")
                self.root.after(0, self.capture_screen)
        except Exception as e:
            print(f"Key error: {e}")
    
    def capture_screen(self):
        """Capture screen"""
        try:
            self.status_var.set("📸 Capturing screen...")
            self.root.update()
            
            # Capture screenshot
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # Primary monitor
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                
                # Save with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                img.save(filename)
                
                self.display_image(img, filename, screenshot.size)
                
        except Exception as e:
            self.status_var.set(f"❌ Error: {e}")
            print(f"Capture error: {e}")
    
    def display_image(self, img, filename, size):
        """Display captured image"""
        try:
            self.current_image = img
            
            # Resize to fit canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 100:
                img_width, img_height = img.size
                ratio = min(canvas_width / img_width, canvas_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                display_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                display_img = img
            
            photo = ImageTk.PhotoImage(display_img)
            self.image_label.configure(image=photo)
            self.image_label.image = photo
            
            self.info_var.set(f"📁 {filename} | 📐 {size[0]}x{size[1]}")
            self.status_var.set("✅ Capture complete! Press 'G' again")
            
        except Exception as e:
            self.status_var.set(f"❌ Display error: {e}")
            print(f"Display error: {e}")
    
    def clear_image(self):
        """Clear display"""
        self.image_label.configure(image='')
        self.image_label.image = None
        self.current_image = None
        self.info_var.set("No captures yet")
        self.status_var.set("Ready - Press 'G' to capture screen")
    
    def on_closing(self):
        """Clean up"""
        if self.listener:
            self.listener.stop()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ScreenCaptureViewer()
    app.run()