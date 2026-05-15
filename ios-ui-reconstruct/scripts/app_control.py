import frida
import time
import sys
import argparse

def get_device():
    try:
        return frida.get_usb_device(timeout=5)
    except Exception as e:
        print(f"[-] USB Device not found: {e}")
        return None

def get_frontmost():
    """Returns the bundle identifier of the frontmost application."""
    device = get_device()
    if not device: return None
    try:
        session = device.attach("SpringBoard")
        script_code = """
            const SBSPort = new NativeFunction(Module.findGlobalExportByName("SBSSpringBoardServerPort"), "int", []);
            const SBFrontmost = new NativeFunction(Module.findGlobalExportByName("SBFrontmostApplicationDisplayIdentifier"), "void", ["int", "pointer"]);
            rpc.exports = {
                getFrontmost: function() {
                    const port = SBSPort();
                    const buf = Memory.alloc(1024);
                    SBFrontmost(port, buf);
                    return buf.readUtf8String();
                }
            };
        """
        script = session.create_script(script_code)
        script.load()
        bundle_id = script.exports_sync.get_frontmost()
        session.detach()
        return bundle_id
    except Exception as e:
        print(f"[-] Failed to get frontmost app: {e}")
        return None

def kill_app(bundle_id):
    """Force-kills all instances of the application."""
    device = get_device()
    if not device: return False
    print(f"[*] Force-killing {bundle_id}...")
    try:
        apps = device.enumerate_applications()
        killed = False
        for app in apps:
            if app.identifier == bundle_id and app.pid != 0:
                print(f"[*] Killing PID {app.pid}")
                device.kill(app.pid)
                killed = True
        if not killed:
            print(f"[*] No running instances of {bundle_id} found.")
        time.sleep(1)
        return True
    except Exception as e:
        print(f"[-] Kill failed: {e}")
        return False

def launch_app(bundle_id):
    """Cleanly launches an application and waits for stability."""
    device = get_device()
    if not device: return None
    
    kill_app(bundle_id)
    
    print(f"[*] Launching {bundle_id}...")
    try:
        pid = device.spawn([bundle_id])
        device.resume(pid)
        print(f"[*] Spawned PID {pid}. Waiting 5s for UI stabilization...")
        time.sleep(5)
        return pid
    except Exception as e:
        print(f"[-] Launch failed: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="iOS App Control Utility")
    parser.add_argument("action", choices=["launch", "kill", "frontmost"], help="Action to perform")
    parser.add_argument("bundle_id", nargs="?", help="Target Bundle Identifier (required for launch/kill)")
    
    args = parser.parse_args()
    
    if args.action == "frontmost":
        bid = get_frontmost()
        if bid: print(f"Frontmost: {bid}")
        else: sys.exit(1)
    elif args.action == "kill":
        if not args.bundle_id:
            print("[-] Error: bundle_id is required for kill action.")
            sys.exit(1)
        if kill_app(args.bundle_id): print("[+] Kill command sent.")
        else: sys.exit(1)
    elif args.action == "launch":
        if not args.bundle_id:
            print("[-] Error: bundle_id is required for launch action.")
            sys.exit(1)
        pid = launch_app(args.bundle_id)
        if pid: print(f"[+] Launched successfully (PID: {pid})")
        else: sys.exit(1)
