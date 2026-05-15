import json
import os
import subprocess
import time
import sys

STATE_FILE = "state.json"
BUNDLE_ID = "com.tigisoftware.ADManager"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def run_cmd(action, *args):
    manager_script = os.path.join(SCRIPT_DIR, "scripts", "capture_manager.py")
    cmd = ["python3", manager_script, BUNDLE_ID, action] + list(args)
    print(f"[*] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[-] Command failed: {' '.join(cmd)}")
        print(result.stderr)
    return result.stdout

def get_name_from_dump(stdout):
    for line in stdout.splitlines():
        if line.startswith("NAME:"):
            return line.split(":", 1)[1]
    return None

def restart_and_navigate(path):
    print(f"[*] Restarting app to navigate back... Path length: {len(path)}")
    app_control_script = os.path.join(SCRIPT_DIR, "scripts", "app_control.py")
    subprocess.run(["python3", app_control_script, BUNDLE_ID, "kill"], capture_output=True)
    time.sleep(2)
    
    # We dump first to let the app launch and settle
    run_cmd("dump")
    time.sleep(1)
    
    for (x, y) in path:
        print(f"[*] Navigating: click at {x},{y}")
        run_cmd("click_pos", "--pos", f"{x},{y}")
        time.sleep(1)

def main():
    state = load_state()
    
    # 0. Initial launch and dump if empty
    if not state:
        print("[*] Initial launch...")
        stdout = run_cmd("dump")
        home_name = get_name_from_dump(stdout)
        if not home_name:
            print("[-] Failed to get home page name.")
            print("Output was:")
            print(stdout)
            return
            
        state[home_name] = {"state": "pending", "path": []}
        save_state(state)
        
    while True:
        # Find a pending page
        pending_name = None
        for name, info in state.items():
            if info["state"] == "pending":
                pending_name = name
                break
                
        if not pending_name:
            print("[+] All pages processed!")
            break
            
        clickable_path = os.path.join("captures", f"{pending_name}-clickable.json")
        json_path = os.path.join("captures", f"{pending_name}.json")
        
        if not os.path.exists(clickable_path):
            print(f"\n[!] AGENT ACTION REQUIRED [!]")
            print(f"[*] Missing clickable elements list for: {pending_name}")
            print(f"[*] Please read {json_path}")
            print(f"[*] Identify actionable elements, and save their coordinates to:")
            print(f"[*] {clickable_path}")
            print(f"[*] Format: [{{\"x\": 100, \"y\": 200}}, ...]")
            break
            
        with open(clickable_path, "r") as f:
            clickables_data = json.load(f)
            
        clickables = []
        for item in clickables_data:
            if isinstance(item, dict) and "x" in item and "y" in item:
                clickables.append((int(item["x"]), int(item["y"])))
            elif isinstance(item, list) and len(item) >= 2:
                clickables.append((int(item[0]), int(item[1])))
                
        print(f"\n[===] Processing pending page: {pending_name} [===]")
        info = state[pending_name]
        path = info["path"]
        
        # Navigate to pending page
        restart_and_navigate(path)
        
        # Ensure we are on the expected page
        stdout = run_cmd("dump")
        current_name = get_name_from_dump(stdout)
        
        if current_name != pending_name:
            print(f"[-] Warning: Reached {current_name} instead of {pending_name}. Will mark {pending_name} as done to prevent loop, and add new page if unknown.")
            if current_name and current_name not in state:
                state[current_name] = {"state": "pending", "path": path}
            state[pending_name]["state"] = "done"
            save_state(state)
            continue
            
        print(f"[*] Found {len(clickables)} clickable elements on {pending_name}")
        
        for idx, (x, y) in enumerate(clickables):
            print(f"[*] Clicking element {idx+1}/{len(clickables)} at {x},{y}...")
            
            # Highlight current as RED
            run_cmd("highlight", "--pos", f"{x},{y}", "--color", "red")
            time.sleep(0.5)
            
            stdout = run_cmd("click_pos", "--pos", f"{x},{y}")
            new_name = get_name_from_dump(stdout)
            
            if not new_name:
                print("[-] Dump failed after click. Restarting...")
                restart_and_navigate(path)
                processed = [{"x": px, "y": py, "color": "green"} for px, py in clickables[:idx+1]]
                if processed: run_cmd("highlight_bulk", "--data", json.dumps(processed))
                continue
                
            if new_name != pending_name:
                print(f"[+] Found new page: {new_name}")
                if new_name not in state:
                    new_path = path + [[x, y]]
                    state[new_name] = {"state": "pending", "path": new_path}
                    save_state(state)
                # Restart to get back to pending_name
                restart_and_navigate(path)
                
                # Verify we got back
                stdout = run_cmd("dump")
                back_name = get_name_from_dump(stdout)
                if back_name != pending_name:
                    print(f"[-] Failed to get back to {pending_name}. Current: {back_name}")
                    break 
                    
                processed_boxes = [{"x": px, "y": py, "color": "green"} for px, py in clickables[:idx+1]]
                if processed_boxes:
                    run_cmd("highlight_bulk", "--data", json.dumps(processed_boxes))
            else:
                # Page didn't change, we can just highlight it green now
                run_cmd("highlight", "--pos", f"{x},{y}", "--color", "green")
                    
        # Done with this page
        state[pending_name]["state"] = "done"
        save_state(state)

if __name__ == "__main__":
    main()