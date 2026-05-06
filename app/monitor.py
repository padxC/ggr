import psutil
import threading
import time

class Monitor:
    def __init__(self, processName):
        self.processName = processName
        self.running = False
        self.thread = None
        self.callback = None
    
    def start(self, callback):
        """Start monitoring in a separate thread"""
        if self.running:
            print("Monitor already running")
            return False
        
        self.callback = callback
        self.running = True
        self.thread = threading.Thread(target=self._watching, daemon=True)
        self.thread.start()
        print(f"Started monitoring for {self.processName}")
        return True
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        print("Stopped monitoring")
        return True
    
    def _watching(self):
        """Monitor loop running in separate thread"""
        while self.running:
            print("i am watching")
            if self._isProcessRunning():
                print(f"Detected {self.processName}!")
                if self.callback:
                    self.callback()

                # both are break
                self.stop()
                break
            time.sleep(2)
    
    def _isProcessRunning(self):
        """Check if process is running"""
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() == self.processName.lower():
                        return True
                except:
                    continue
        except:
            pass
        return False
    
    def isRunning(self):
        """Check if monitor is active"""
        return self.running