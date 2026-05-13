---
name: create-ios-app-proj
description: Create and run a "Hello World" iOS app on a physical device using the JBDev method (unsigned/jailbreak development).
---

# Create iOS App Project (JBDev)

This skill automates the creation of a minimal iOS app project that can be built and run on a physical iOS device without official Apple code signing, leveraging the JBDev framework.

## Prerequisites

- **Xcode** installed.
- **ldid** installed (`brew install ldid`).
- **xcodegen** installed (`brew install xcodegen`).
- **ideviceinstaller** and **libimobiledevice** installed (`brew install ideviceinstaller libimobiledevice`).
- A connected iOS device (usually jailbroken with AppSync Unified).

## Workflow

1.  **Initialize Project Directory**: Create a folder for the app.
2.  **Copy Templates**: Copy the files from `assets/templates/` to the project folder.
3.  **Configure App Name**: Rename `template.ent` to `<AppName>.ent`.
4.  **Generate Project**: Run `xcodegen generate` in the project folder.
5.  **Build**: Run `xcodebuild` targeting `generic/platform=iOS`.

## Project Structure

- `Sources/`: Objective-C source files.
- `Info.plist`: App configuration.
- `project.yml`: XcodeGen project specification.
- `jbdev.plist`: JBDev configuration (type: app/jailbreak/trollstore).
- `jbdev.build.sh`: Custom build script to handle `ldid` signing.
- `<AppName>.ent`: Entitlements for the app.

## Example Commands

### Building
```bash
xcodebuild -project <AppName>.xcodeproj -scheme <AppName> -configuration Debug -sdk iphoneos -destination 'generic/platform=iOS' build
```

### Installing
```bash
ideviceinstaller -u <UDID> install <PathToAppBundle>
```

### Launching
```bash
idevicedebug -u <UDID> run <BundleIdentifier>
```
