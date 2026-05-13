# Exploration & Containers

## Phase 1: Controller Topology

### Recursive DFS Traversal
- Start from `rootViewController` of the `keyWindow`.
- Maintain `visited_pages` (Hash = Class + Title + Layout Hash) to avoid loops.
- Map `childViewControllers` and `presentedViewController` relationships.
- Record `navigationController` and `tabBarController` structures.

### Scene & Window Management
- Identify `UIWindowScene` on iOS 13+.
- Scan all `UIWindow` instances (Alerts, Floating Windows, overlays).
- Convert all view frames to the main window's coordinate system using `convertRect:toView:`.

## Phase 2: Container Sampling

### List-Deep Sampling
- **UITableView**: Sample the first 2-3 rows to identify unique `UITableViewCell` classes/templates.
- **UICollectionView**: Sample cells and capture `UICollectionViewCompositionalLayout` parameters if present.
- **Scrolling**: If `contentSize > bounds`, perform segmented scrolling to capture off-screen content.

### Interactive Triggering
- Prefer calling `delegate` methods (e.g., `didSelectRowAtIndexPath:`) to trigger transitions.
- Fallback: Physical click simulation via coordinate transformation to `cell.center`.

### WebView Sniffing
- Identify `WKWebView`.
- Record the `URL` or capture the HTML/Content characteristics.
- Export a placeholder boundary in the reconstructed view tree.

## Phase 3: Backtrack & Recovery
- Identify "Back" buttons or force `pop/dismiss` to return to previous states.
- If the app hangs, log the current `exploration_path` and restart the process, resuming from the last known state in `exploration_log.json`.

## Phase 4: Advanced Runtime Exploration (Heap & State)
- **Heap Object Scanning**: Use `ObjC.choose()` to search the heap for unattached `UIViewController` or `UIView` instances that are alive but not currently in the `keyWindow` hierarchy. This helps capture hidden or pre-loaded UI components.
- **State Manipulation**: Dynamically modify `isHidden` or `alpha` properties on views to reveal and capture hidden elements.
- **UI Lock Bypass**: If exploration is blocked by overlays or login screens, hook `viewWillAppear:` on the blocking controller to force `dismissViewControllerAnimated:completion:`.
