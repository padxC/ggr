import pygetwindow as gw
from PIL import ImageGrab, Image
from datetime import datetime
import ctypes

try:
    # set awareness when using scale 
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass

class Screen:
    @staticmethod
    def getRegion(title):
        """Get current position tuple"""
        windows = gw.getWindowsWithTitle(title)
        
        if windows:
            window = windows[0];
            return (window.left, window.top, window.width, window.height)
        return None

    @staticmethod
    def capture(region):
        """Capture the picture based on Region using PIL"""
        try:
            # region format: (left, top, width, height)
            left, top, width, height = region
            # Calculate bbox (left, top, right, bottom)
            bbox = (left, top, left + width, top + height)
            
            # Capture using PIL ImageGrab
            img = ImageGrab.grab(bbox)
            
            # Set filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"picture_{timestamp}.png"
            
            img.save(filename)
            print(f"✅ Captured: {filename}")
            return img, filename
                
        except Exception as e:
            print(f"❌ Capture error: {e}")
            return None

# Example usage
if __name__ == "__main__":
    # Create screen object
    region = Screen.getRegion("Tales Runner")
    
    if region:
        x, y, w, h = region
        print(f"Found window: X={x}, Y={y}, W={w}, H={h}")
        
        # Capture screenshot
        Screen.capture(region)
    else:
        print("❌ Tales Runner not found")