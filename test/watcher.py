import psutil
import time
import os

def watch_tr_patcher_simple():
    """Simpler version - print all available info"""
    while True:
        os.system('cls')
        print(f"TR PATCHER MONITOR - {time.strftime('%H:%M:%S')}")
        print("="*50)
        
        found = False
        for proc in psutil.process_iter():
            try:
                if "TR Patcher" in proc.name() or "TRPatcher" in proc.name() or "TR" in proc.name() or "Patcher" in proc.name():
                    found = True
                    
                    # Print EVERYTHING
                    print(f"\nProcess: {proc.name()} (PID: {proc.pid})")
                    print(f"Status: {proc.status()}")
                    print(f"CPU: {proc.cpu_percent(interval=0.5)}%")
                    print(f"Memory: {proc.memory_info().rss / 1024 / 1024:.2f} MB")
                    print(f"Path: {proc.exe()}")
                    print(f"Command: {' '.join(proc.cmdline())}")
                    print(f"User: {proc.username()}")
                    print(f"Created: {time.ctime(proc.create_time())}")
                    print(f"Threads: {proc.num_threads()}")
                    
                    # Parent process
                    if proc.parent():
                        print(f"Parent: {proc.parent().name()} (PID: {proc.parent().pid})")
                    
                    # Children
                    children = proc.children()
                    if children:
                        print(f"Children: {', '.join([c.name() for c in children])}")
                    
                    # Open files
                    try:
                        files = proc.open_files()
                        if files:
                            print(f"Open Files: {len(files)}")
                            for f in files[:3]:
                                print(f"  - {f.path}")
                    except:
                        pass
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if not found:
            print("\n❌ TR PATCHER NOT RUNNING")
        
        time.sleep(2)

watch_tr_patcher_simple()