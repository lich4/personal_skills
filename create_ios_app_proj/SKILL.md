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
3.  **Configure App Name**: 
    - Rename `template.ent` to `<AppName>.ent`.
    - In `project.yml`, replace all occurrences of `AppName` with your desired `<AppName>`.
    - In `Info.plist`, update `CFBundleName` and `PRODUCT_BUNDLE_IDENTIFIER` as needed.
4.  **Generate Project**: Run `xcodegen generate` in the project folder. This will create `<AppName>.xcodeproj`.
5.  **Build**: Run `xcodebuild` targeting `generic/platform=iOS`.

## Project Structure Consistency

To ensure the build and signing scripts work correctly, maintain the following naming consistency:
- **Project Name**: `<AppName>.xcodeproj` (generated from `project.yml` name)
- **Target Name**: `<AppName>` (defined in `project.yml` targets)
- **Entitlements File**: `<AppName>.ent` (referenced in `project.yml` settings)

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
