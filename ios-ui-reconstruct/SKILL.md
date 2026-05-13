---
name: ios-ui-reconstruct
description: Advanced 1:1 iOS UI reconstruction using Frida (attach-mode). Captures app hierarchies and metadata to generate a compilable Objective-C project. Requires the app to be running (use launch_app.py).
---

# iOS UI Reconstruct (Attach Mode)

This skill reverse-engineers iOS application interfaces and reconstructs them as semantic Objective-C projects. It strictly follows an **attach-only** workflow to ensure stability and proper initialization of the Objective-C runtime.

## Core Rules & Constraints

- **Frida 17+ Modernization**: All Frida scripts MUST use `frida-compile` and `frida-objc-bridge`.
  - JS source: `scripts/ui_reconstruct.js` (uses ESM `import ObjC from 'frida-objc-bridge'`).
  - Compiled output: `scripts/_ui_reconstruct.js`.
  - Python MUST load the compiled `_ui_reconstruct.js`.
  - Communication MUST use `rpc.exports` instead of legacy `send`/`recv`.
- **Attach-Only Execution**: Always attach to an existing process. Do NOT use `spawn` (`-f`) to execute scripts directly. 
- **Frida CLI Hygiene**: When using `frida -l`, ALWAYS include the `-q` (quiet) flag to ensure the process exits after script execution instead of hanging in interactive mode.
- **Data Persistence**: All temporary data must be saved in `./temp/`, and logs in `task.log`.

## Workflow Overview

1.  **Launch App**: Use `launch_app.py` to start the target app and wait for it to reach the foreground.
2.  **Attach & Dump**: Use `reconstruct.py` or `frida -l` to attach and capture UI metadata.
3.  **Project Generation**: Convert the captured JSON into a structured Objective-C project.

## Bundled Scripts

- `scripts/launch_app.py`: Spawns and resumes the app by Bundle ID.
- `scripts/reconstruct.py`: The main coordinator (finds PID, attaches, dumps UI, generates code).
- `scripts/ui_reconstruct.js`: The Frida engine that traverses the UI tree.
- `scripts/project_generator.py`: Converts metadata to code.

## Getting Started

### Step 1: Launch the Target App
```bash
# Example: Launch App
python3 scripts/launch_app.py [AppBid]
```

### Step 2: Run Reconstruction (Attach Mode)
```bash
# Option A: Using the coordinator script
python3 scripts/reconstruct.py [AppBid] [AppName]

# Option B: Using Frida CLI directly (for debugging)
frida -U -q -l scripts/ui_reconstruct.js -n [AppName] -e "rpc.exports.dump()"
```

## Safety & Best Practices

- **Avoid UI Freeze**: All heavy operations are scheduled on the main queue with minimal overhead.
- **Absolute Coordinates**: All view frames are converted to the window coordinate system for precision.
- **Clean State**: Ensure keyboards and system alerts are dismissed before starting the dump.
