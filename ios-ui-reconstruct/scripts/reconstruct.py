
import frida
import json
import time
import sys
from pathlib import Path

class ReconstructEngine:
    def __init__(self, bundle_id, process_name):
        self.bundle_id = bundle_id
        self.process_name = process_name
        self.device = frida.get_usb_device()
        self.session = None
        self.script = None
        self.dump_data = None
        self.error_received = None

    def on_message(self, message, data):
        if message['type'] == 'send':
            payload = message['payload']
            if isinstance(payload, dict):
                p_type = payload.get('type')
                if p_type == 'progress':
                    print(f"[*] [Progress] {payload.get('payload')}")
                elif p_type == 'dump_result':
                    self.dump_data = payload.get('payload')
                elif p_type == 'error':
                    self.error_received = payload.get('payload')
                    print(f"[-] [JS Error] {self.error_received}")
                elif p_type == 'log':
                    print(f"[*] [JS Log] {payload.get('payload')}")
            else:
                print(f"[*] [JS Message] {payload}")
        elif message['type'] == 'error':
            print(f"[-] [JS Exception] {message.get('stack', message.get('description'))}")
            self.error_received = message.get('description')

    def connect(self):
        print(f"[*] Attaching to {self.process_name}...")
        try:
            self.session = self.device.attach(self.process_name)
            script_path = Path(__file__).parent / "_ui_reconstruct.js"
            with open(script_path, "r") as f:
                self.script = self.session.create_script(f.read())
            self.script.on('message', self.on_message)
            self.script.load()
            return True
        except Exception as e:
            print(f"[-] Connection failed: {e}")
            return False

    def run(self):
        if not self.connect():
            return

        try:
            print("[*] Foundation testing: Sending ping via RPC...")
            pong = self.script.exports_sync.ping()
            print(f"[*] Ping result: {pong}")

            print("[*] Requesting full UI dump via RPC (this may take a moment)...")
            self.dump_data = self.script.exports_sync.dump()

            if self.dump_data:
                temp_dir = Path(__file__).parent.parent / "temp"
                temp_dir.mkdir(exist_ok=True)
                dump_path = temp_dir / "ui_dump.json"
                with open(dump_path, "w", encoding="utf-8") as f:
                    json.dump(self.dump_data, f, indent=2)
                print(f"[*] UI dump saved to {dump_path}")

                print("[*] Starting project generation...")
                from project_generator import ProjectGenerator
                output_dir = Path(__file__).parent.parent / "output"
                gen = ProjectGenerator(output_dir)
                gen.generate(self.dump_data)
                print(f"[*] Project generation complete. Output: {output_dir}")
            else:
                print("[!] Baseline FAILED: No data returned")
        except Exception as e:
            print(f"[-] RPC Error: {e}")
            import traceback
            traceback.print_exc()

        
        finally:
            self.session.detach()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python reconstruct.py <bundle_id> <process_name>")
        sys.exit(1)
    
    engine = ReconstructEngine(sys.argv[1], sys.argv[2])
    engine.run()
