import frida
import subprocess
import sys

def check_frida():
    print("[*] Checking Frida connection...")
    try:
        device = frida.get_usb_device(timeout=5)
        print(f"[+] Connected to: {device.name} ({device.id})")
        return True
    except Exception as e:
        print(f"[-] Frida connection failed: {e}")
        return False

def check_frida_compile():
    print("[*] Checking frida-compile...")
    try:
        subprocess.run(["frida-compile", "--version"], check=True, capture_output=True)
        print("[+] frida-compile is available.")
        return True
    except Exception:
        print("[-] frida-compile not found. Install with: npm install -g frida-compile")
        return False

def check_ideviceinstaller():
    print("[*] Checking ideviceinstaller...")
    try:
        subprocess.run(["ideviceinstaller", "--version"], check=True, capture_output=True)
        print("[+] ideviceinstaller is available.")
        return True
    except Exception:
        print("[-] ideviceinstaller not found. Install with: brew install ideviceinstaller")
        return False

if __name__ == "__main__":
    ok = True
    if not check_frida(): ok = False
    if not check_frida_compile(): ok = False
    if not check_ideviceinstaller(): ok = False
    
    if ok:
        print("\n[+] Environment is READY for UI Reconstruction.")
    else:
        print("\n[-] Environment check FAILED. Please fix the issues above.")
        sys.exit(1)
