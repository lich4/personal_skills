# Metadata Capture

## Phase 3: Visual Mirroring

### CALayer Properties
- **Visuals**: Capture `shadows`, `gradients`, `cornerRadius`, and `borders`.
- **Special Effects**: Identify `UIVisualEffectView` (Blur style) and `CAShapeLayer` (Path data).
- **Custom Drawing**: Detect `drawRect:` overrides. Use `snapshotViewAfterScreenUpdates:` to capture high-fidelity images for custom views.

### Typography & Strings
- Capture `NSAttributedString` attributes (Font, ForegroundColor, ParagraphStyle, Kerning).
- Map to `NSMutableAttributedString` initialization code.
- Collect all static strings for `Localizable.strings`.

## Phase 4: Layout Reverse-Engineering

### Auto Layout Deconstruction
- Iterate through `constraints`.
- Parse relationships (Leading, Trailing, Top, Bottom, Width, Height, Multipliers).

### Semantic Containers
- **UIStackView**: Extract `axis`, `distribution`, `alignment`, and `spacing`. Reconstruct as a `UIStackView` container rather than raw constraints.
- **Size Classes**: Detect `Regular/Compact` state differences by simulating device rotation or different device models.
- **Safe Area**: Record `safeAreaInsets` and Dynamic Island offsets.

## Phase 5: Interaction & Control State

### Target-Action Mapping
- Extract `allTargets` and `actionsForTarget:forControlEvent:` for `UIControl`.
- Generate `IBAction` stubs or Target-Action binding code.

### Gesture Recognizers
- Scan `UIGestureRecognizer` and record callback function names.
- Detect `pointInside:withEvent:` overrides for custom hit testing.

### Multi-State Sampling
- Cycle through `Highlighted`, `Selected`, and `Disabled` states for `UIControl` to capture visual differences.

## Phase 6: Deep Introspection

### Instance Variable (Ivar) Inspection
- Do not rely solely on public properties. Use `ObjC.Object(ptr).$ivars` to extract private state or models attached to views that dictate their rendering.
- Check `NSUserDefaults` via `[NSUserDefaults standardUserDefaults]` to capture user preferences that might affect the UI theme or layout.

### Responder Chain & Event Routing
- Traverse the `nextResponder` chain for complex views to identify the specific controller responsible for handling actions.

### Network Mocking
- Hook `NSURLSession` or underlying network methods to capture incoming JSON data during the dump. Use this intercepted data to generate realistic mock data models for the reconstructed Objective-C project.
