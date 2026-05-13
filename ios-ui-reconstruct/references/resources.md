# Assets & Resources

## Phase 5: Asset Catalog Automation

### Image Extraction
- Export images in @2x and @3x resolutions.
- Detect **Light/Dark** mode variations and group them into `Image Sets` in `.xcassets`.
- Use Pixel Hash comparison to deduplicate identical icons across different pages.
- Prefer PDF/SVG vector sources if available.

### Symbols & Fonts
- **SF Symbols**: Capture weight, scale, and multi-color palette configurations.
- **Custom Fonts**: Export `.ttf` or `.otf` files and configure `UIAppFonts` in `Info.plist`.

## Phase 6: Internationalization

### String Extraction
- Collect all UI text from `UILabel`, `UIButton`, and `UITextField`.
- Generate `Localizable.strings` files.
- Replace hardcoded strings in generated code with `NSLocalizedString`.

## Phase 7: Environment Perception

### Appearance & Dynamic Type
- Actively toggle system **Appearance** (Light/Dark) to capture dynamic color changes.
- Test different **Dynamic Type** (Font Size) levels to ensure layout robustness.
- Record `TraitCollection` changes.
