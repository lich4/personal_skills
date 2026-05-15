---
name: ios-ui-capture
description: Agent-led page-by-page iOS UI capture (JSON + PNG) using Frida primitives and deterministic state tracking.
---

# iOS UI Capture (Agent-Led Strategy)

This skill provides an automated workflow to systematically traverse, capture, and track the states of all screens in an iOS application.

## 🛑 GLOBAL FRIDA MANDATES (ALWAYS FOLLOW)

1.  **Mandatory Compilation**: EVERY Frida script must be compiled using **`frida-compile`** to bundle the **`frida-objc-bridge`**. All scripts must include `import "frida-objc-bridge";` at the top. Running uncompiled scripts will fail with "'ObjC' is not defined".
2.  **CLI Quiet Mode**: When calling the base `frida` CLI (e.g., `frida -U ...`), you MUST always include the **`-q`** (quiet) flag to prevent entering interactive mode.
3.  **Timeout Enforcement**: 
    *   **Device Discovery**: Always use `frida.get_usb_device(timeout=5)` in Python scripts to avoid indefinite hangs.
    *   **Subprocess Execution**: EVERY `subprocess.run` or `run_shell_command` involving Frida tools (`frida`, `frida-ps`, `frida-compile`, etc.) MUST include a reasonable **`timeout`** (e.g., 30-60 seconds).
    *   **RPC Calls**: Ensure RPC calls have a 5-second timeout mechanism.
4.  **Strict Foreground Enforcement**: Before ANY operation on a target app, ensure the app process exists and is the frontmost application. If not, force-kill and restart it. Wait at least **2 seconds** after a fresh launch before proceeding.
5.  **5-Second Timeout & Restart**: If a Frida operation (attach, script load, or RPC call) does not return within **5 seconds**, terminate, force-kill the app, and re-attempt.

## 1. State Management (`./state.json`)

The state file tracks the processing status of each visited page and the navigation path required to reach it.

- `state`: The processing status (`pending` or `done`).
- `path`: The sequence of click coordinates required to navigate from the home screen to this page.

**Example format:**
```json
{
    "XXXViewController-title1": {"state": "done", "path": []}, 
    "YYYViewController-title2": {"state": "done", "path": [[111,222], [333,444]]}
}
```

## 2. Core Workflow

0. **Initialize**: Create a dedicated working directory for your target app analysis and navigate to it. The tools will create `state.json`, `captures/`, and `temp/` in your current working directory. Initialize the `State file` (`./state.json`) to record the processing states of pages.
1. **Launch**: Start the application and wait until it enters the home page. Obtain the Objective-C class name (`{XXXViewController}`) and the title of this page. Record `{XXXViewController-title}` in the `State file` with `state` set to `pending` and `path` as `[]`.
2. **Capture**: Run the capture manager script via its absolute or relative path. Use it to dump the UI of the current page as `captures/{XXXViewController-title}.json` and take a screenshot saved as `captures/{XXXViewController-title}.png`. Once completed, update the `state` of `{XXXViewController-title}` to `done` in the `State file`.
    ```bash
    # Run from your current working directory (e.g. /tmp/admanager-analysis)
    python3 /path/to/ios-ui-reconstruct/scripts/capture_manager.py <bundle_id> dump
    ```
3. **Analyze and Traverse**: The agent analyzes the list of clickable elements from the JSON dump. For each element:
    - Click the element.
    - If a **new page** is reached:
        - Obtain the new page's Objective-C class name (`{XXXViewController}`) and title.
        - Record `{XXXViewController-title}` in the `State file` with `state` set to `pending`, along with its current `path` (the sequence of previous clicks + the new click).
        - Execute step **2** (Capture) for this new page.
        - **Restart the app** and use the stored `path` to navigate back to the previous page. (Restarting and navigating via coordinate path is more stable than using a UI back button). Proceed to click the next element on the previous page.
4. **Finish**: Terminate the process when all paths are explored and no more `pending` pages exist.

## 3. Bundled Scripts

- `scripts/ui_capture.js`: Frida primitive implementations.
- `scripts/capture_manager.py`: Command-line interface for the agent.
- `scripts/app_control.py`: Process management (Launch/Kill).
- `scripts/env_check.py`: Environment verification.
