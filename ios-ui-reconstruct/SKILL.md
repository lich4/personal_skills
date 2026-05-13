---
name: ios-ui-reconstruct
description: Advanced 1:1 iOS UI reconstruction using Frida. Generates a complete, compilable Xcode-Objective-C project (UI and UI interaction only) with zero external dependencies.
---

# iOS UI Reconstruct (Attach Mode)

This skill reverse-engineers iOS application interfaces and reconstructs them as a **complete, compilable Xcode-Objective-C project** focusing exclusively on UI structure and interaction logic.

## Core Rules & Constraints

- **Frida 17+ Modernization**: All Frida scripts MUST use `frida-compile` and `frida-objc-bridge`.
- **Compilable Xcode-ObjC Project**: 
  - The goal is to produce a project that can be opened and built in Xcode with minimal effort.
  - The output project MUST be 100% Objective-C++ (using `.mm` extensions for implementations).
  - Zero external dependencies: Use native UIKit `CGRect` frames for all layouts.
  - Scope: Reconstruction is limited to the visual hierarchy (UI) and basic interaction stubs (UI Response).
- **Data Persistence & Logging**: 
  - All temporary data and scripts must be saved in `./temp/` (relative to the current working directory). 
  - Every step (reasoning, commands, results) MUST be appended to `./task.log`.
  - Do NOT save data inside the skill directory.

## Project Structure (Output)
...

- `Info.plist`: Basic app configuration.
- `Sources/main.mm`: Entry point.
- `Sources/Classes/`: 
  - `AppDelegate.{h,mm}`
  - `[ViewController].{h,mm}` (Semantic UI reconstruction).

## Workflow Overview
...

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
