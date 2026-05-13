# Code Generation & Delivery

## Phase 7: Semantic Refactoring

### Naming Conventions
- Use `accessibilityIdentifier` as the primary source for variable names.
- Fallback: Scrape Runtime `ivars` for existing internal names.
- Secondary Fallback: Generate camelCase names based on text content (e.g., "Login" button -> `loginButton`).

### Hierarchy Flattening
- Identify and remove redundant container `UIView` instances that have no visual features or interaction logic.
- Optimize the view tree for better rendering performance in the reconstructed project.

## Phase 8: Validation & Audit

### Consistency Checks
- Export a layout tree snapshot from the reconstructed project.
- Compare the MD5 of the view hierarchy against the original App.
- Perform pixel-level diffing between the original and reconstructed screens.

## Phase 9: Engineering Delivery

### Project Structure
- `Resources/`: `.xcassets`, `Localizable.strings`, fonts.
- `Sources/Views/`: Custom view classes and cells.
- `Sources/Controllers/`: ViewControllers.
- Generate `.xcodeproj` or `Package.swift`.

### Hybrid & Swift Support
- Detect `UIHostingController` (SwiftUI) and infer `VStack/HStack/ZStack` logic.
- Handle Swift/Objective-C interop by generating necessary bridging headers or interface stubs.

### Build Verification
- Execute `xcodebuild` in the terminal to ensure the project compiles and links correctly.
- Verify that all assets are correctly referenced.
