import frida
import json
import time
import sys
import subprocess
import argparse
from pathlib import Path
from app_control import get_frontmost, launch_app, kill_app

class CaptureManager:
    def __init__(self, bundle_id):
        self.bundle_id = bundle_id
        try:
            self.device = frida.get_usb_device(timeout=5)
        except Exception as e:
            print(f"[-] USB Device not found: {e}")
            sys.exit(1)
        self.script_src = Path(__file__).parent / "ui_capture.js"
        self.script_out = Path("temp/_ui_capture.js")
        self.captures_dir = Path("captures")
        self.captures_dir.mkdir(exist_ok=True)
        self.script = None
        self.session = None

    def compile_script(self):
        self.script_out.parent.mkdir(exist_ok=True, parents=True)
        try:
            subprocess.run(["frida-compile", str(self.script_src.name), "-o", str(self.script_out.absolute())], 
                           cwd=str(self.script_src.parent),
                           check=True, timeout=30, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"[-] Compilation failed: {e.stderr.decode('utf-8') if e.stderr else e}")
            return False

    def setup_session(self):
        """Attaches to existing process or launches new one."""
        self.compile_script()
        
        # 1. Try to find existing PID
        try:
            apps = self.device.enumerate_applications()
            target_pid = next((app.pid for app in apps if app.identifier == self.bundle_id and app.pid != 0), None)
            
            if not target_pid:
                print(f"[*] Launching {self.bundle_id}...")
                target_pid = launch_app(self.bundle_id)
            
            if target_pid:
                self.session = self.device.attach(target_pid)
                with open(self.script_out, "r") as f:
                    self.script = self.session.create_script(f.read())
                self.script.load()
                time.sleep(1) # Wait for script environment to settle
                return True
        except Exception as e:
            print(f"[-] Session setup failed: {e}")
        return False

    def safe_call(self, func_name, *args):
        try:
            method = getattr(self.script.exports_sync, func_name)
            return method(*args)
        except Exception as e:
            print(f"[-] RPC Error in {func_name}: {e}")
            return None

    def dump(self):
        """Captures JSON + PNG for the current screen."""
        if not self.setup_session(): return None
        
        data = self.safe_call("dump")
        if not data or "error" in data: return None
        
        vc_class = data.get("vcClass", "Unknown")
        title = data.get("title", "")
        # Sanitize title for filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        name = f"{vc_class}-{safe_title}" if safe_title else vc_class
        
        json_path = self.captures_dir / f"{name}.json"
        png_path = self.captures_dir / f"{name}.png"
        
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
            
        print(f"[*] Taking screenshot: {png_path.name}")
        subprocess.run(["idevicescreenshot", "-u", self.device.id, str(png_path)], 
                       check=True, timeout=30, capture_output=True)
        
        return json_path, name

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="iOS UI Capture Manager (Agent Interface)")
    parser.add_argument("bundle_id", help="Target Bundle Identifier")
    parser.add_argument("action", choices=["dump", "click_text", "click_pos", "highlight", "highlight_text", "highlight_bulk", "back"], help="Action to perform")
    parser.add_argument("--text", help="Text to click (for click_text)")
    parser.add_argument("--pos", help="Coordinates 'x,y' (for click_pos)")
    parser.add_argument("--color", default="red", help="Color for highlight (red, green, blue, yellow)")
    parser.add_argument("--data", help="JSON string for bulk operations")
    
    args = parser.parse_args()
    manager = CaptureManager(args.bundle_id)
    
    if args.action == "dump":
        result = manager.dump()
        if result:
            path, name = result
            print(f"[+] Dump saved to: {path}")
            # Also print the name so the caller can read it easily
            print(f"NAME:{name}")
        else: sys.exit(1)
    
    elif args.action == "click_text":
        if not args.text:
            print("[-] Error: --text is required")
            sys.exit(1)
        if manager.setup_session():
            if manager.safe_call("click_by_text", args.text):
                print(f"[+] Clicked text: {args.text}")
                time.sleep(2)
                result = manager.dump()
                if result:
                    print(f"NAME:{result[1]}")
            else:
                print(f"[-] Could not find text: {args.text}")
                sys.exit(1)
                
    elif args.action == "highlight_text":
        if not args.text:
            print("[-] Error: --text is required")
            sys.exit(1)
        if manager.setup_session():
            if manager.safe_call("highlight_by_text", args.text, args.color):
                print(f"[+] Highlighted text: {args.text} in {args.color}")
            else:
                print(f"[-] Could not find text to highlight: {args.text}")
                sys.exit(1)
                
    elif args.action == "click_pos":
        if not args.pos:
            print("[-] Error: --pos is required")
            sys.exit(1)
        x, y = map(int, args.pos.split(","))
        if manager.setup_session():
            if manager.safe_call("click_at", x, y):
                print(f"[+] Clicked position: {x},{y}")
                time.sleep(2)
                result = manager.dump()
                if result:
                    print(f"NAME:{result[1]}")
            else:
                print(f"[-] Click at {x},{y} failed")
                sys.exit(1)

    elif args.action == "back":
        if manager.setup_session():
            if manager.safe_call("go_back"):
                print("[+] Back command sent")
                time.sleep(1.5)
                result = manager.dump()
                if result:
                    print(f"NAME:{result[1]}")
            else:
                print("[-] Could not go back")
                sys.exit(1)

    elif args.action == "highlight":
        if not args.pos:
            print("[-] Error: --pos is required")
            sys.exit(1)
        x, y = map(int, args.pos.split(","))
        if manager.setup_session():
            manager.safe_call("highlightAt", x, y, args.color)
            print(f"[+] Highlighted {x},{y} in {args.color}")
            
    elif args.action == "highlight_bulk":
        if not args.data:
            print("[-] Error: --data is required")
            sys.exit(1)
        if manager.setup_session():
            manager.safe_call("drawBBoxes", args.data)
            print(f"[+] Highlighted bulk data")
