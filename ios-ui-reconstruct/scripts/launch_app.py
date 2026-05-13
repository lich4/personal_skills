#!/usr/bin/env python3
import frida
import sys
import argparse
import time

def launch_app(bundle_id):
    try:
        device = frida.get_usb_device()
        
        # Check if already running
        try:
            processes = device.enumerate_processes()
            for proc in processes:
                # Some apps might have multiple processes or different names, 
                # but usually bundle_id check is more complex. 
                # Here we just look for exact match or spawn new.
                pass
        except:
            pass

        print(f"[*] Spawning {bundle_id}...")
        pid = device.spawn([bundle_id])
        device.resume(pid)
        
        print(f"[+] Successfully launched {bundle_id} (PID: {pid})")
        # Give it a few seconds to initialize
        time.sleep(3)
        return True
    except frida.ServerNotRunningError:
        print("[-] Error: frida-server is not running on the device.")
    except frida.DeviceNotFoundError:
        print("[-] Error: USB device not found.")
    except Exception as e:
        print(f"[-] Error: {e}")
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch an iOS app via Frida")
    parser.add_argument("bid", help="Bundle identifier")
    args = parser.parse_args()
    
    if launch_app(args.bid):
        sys.exit(0)
    else:
        sys.exit(1)
