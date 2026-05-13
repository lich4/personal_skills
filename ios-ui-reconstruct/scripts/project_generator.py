import json
import os
from pathlib import Path

# Known public UIKit classes to avoid mapping to UIView
PUBLIC_UIKIT_CLASSES = {
    "UIView", "UILabel", "UIButton", "UIImageView", "UITableView", "UITableViewCell",
    "UICollectionView", "UICollectionViewCell", "UIScrollView", "UITextField", "UITextView",
    "UISwitch", "UISlider", "UIStepper", "UIPageControl", "UIActivityIndicatorView",
    "UIProgressView", "UISegmentedControl", "UINavigationBar", "UIToolbar", "UITabBar",
    "UISearchBar", "UIVisualEffectView", "UIStackView", "UIWindow"
}

class ProjectGenerator:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.sources_dir = self.output_dir / "Sources"
        self.classes_dir = self.sources_dir / "Classes"
        self.classes_dir.mkdir(parents=True, exist_ok=True)
        self.processed_vcs = set()
        self.class_prefix = "RE"

    def get_prefixed_class(self, class_name):
        # If it's a system class, prefix it to avoid collisions
        # e.g. UINavigationController -> REUINavigationController
        if class_name.startswith("UI") or class_name.startswith("NS"):
             return f"{self.class_prefix}{class_name}"
        return f"{self.class_prefix}{class_name}"

    def generate(self, ui_data):
        print("[*] Generating pure Objective-C project scaffold...")
        self.write_scaffold()
        
        if "viewControllers" in ui_data:
            for vc in ui_data["viewControllers"]:
                self.process_vc(vc)
        elif "rootVC" in ui_data:
            self.process_vc(ui_data["rootVC"])

    def write_scaffold(self):
        # Info.plist
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleExecutable</key>
	<string>$(EXECUTABLE_NAME)</string>
	<key>CFBundleIdentifier</key>
	<string>com.reconstruct.app</string>
	<key>CFBundleName</key>
	<string>ReconstructedApp</string>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleShortVersionString</key>
	<string>1.0</string>
	<key>LSRequiresIPhoneOS</key>
	<true/>
	<key>UILaunchStoryboardName</key>
	<string>LaunchScreen</string>
	<key>UISupportedInterfaceOrientations</key>
	<array>
		<string>UIInterfaceOrientationPortrait</string>
	</array>
</dict>
</plist>
"""
        with open(self.output_dir / "Info.plist", "w") as f:
            f.write(plist_content)

        # AppDelegate.h
        app_delegate_h = f"""#import <UIKit/UIKit.h>

@interface AppDelegate : UIResponder <UIApplicationDelegate>
@property (strong, nonatomic) UIWindow *window;
@end
"""
        with open(self.classes_dir / "AppDelegate.h", "w") as f:
            f.write(app_delegate_h)

        # AppDelegate.mm
        app_delegate_mm = f"""#import "AppDelegate.h"

@implementation AppDelegate
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {{
    return YES;
}}
@end
"""
        with open(self.classes_dir / "AppDelegate.mm", "w") as f:
            f.write(app_delegate_mm)

        # main.mm
        main_mm = f"""#import <UIKit/UIKit.h>
#import "AppDelegate.h"

int main(int argc, char * argv[]) {{
    @autoreleasepool {{
        return UIApplicationMain(argc, argv, nil, NSStringFromClass([AppDelegate class]));
    }}
}}
"""
        with open(self.sources_dir / "main.mm", "w") as f:
            f.write(main_mm)

    def process_vc(self, vc_info):
        raw_class_name = vc_info["class"]
        class_name = self.get_prefixed_class(raw_class_name)
        
        if class_name in self.processed_vcs:
            return
        self.processed_vcs.add(class_name)

        print(f"[*] Generating {class_name}...")
        
        self.write_header(class_name)
        self.write_implementation(vc_info, class_name)

        for child in vc_info.get("children", []):
            self.process_vc(child)
        
        if "presented" in vc_info and vc_info["presented"]:
            self.process_vc(vc_info["presented"])

    def write_header(self, class_name):
        content = f"""#import <UIKit/UIKit.h>

@interface {class_name} : UIViewController

@end
"""
        with open(self.classes_dir / f"{class_name}.h", "w") as f:
            f.write(content)

    def write_implementation(self, vc_info, class_name):
        view_info = vc_info.get("view", {})
        setup_views_code = self.generate_setup_views(view_info)

        content = f"""#import "{class_name}.h"

@interface {class_name} ()
@end

@implementation {class_name}

- (void)viewDidLoad {{
    [super viewDidLoad];
    self.view.backgroundColor = [UIColor whiteColor];
    [self setupViews];
}}

- (void)setupViews {{
{setup_views_code}
}}

@end
"""
        with open(self.classes_dir / f"{class_name}.mm", "w") as f:
            f.write(content)

    def generate_setup_views(self, view_info):
        lines = []
        self.view_counter = 0
        self.subview_map = {} # handle -> name
        
        self.walk_view_tree(view_info, "self.view", lines)
        return "\n".join(lines)

    def walk_view_tree(self, view_info, parent_name, lines):
        if not view_info:
            return

        for subview in view_info.get("subviews", []):
            self.view_counter += 1
            var_name = self.get_var_name(subview)
            self.subview_map[subview["handle"]] = var_name
            
            raw_cls = subview["class"]
            
            # Map private or unknown classes to UIView for compilability
            if raw_cls.startswith("_") or raw_cls not in PUBLIC_UIKIT_CLASSES:
                use_cls = "UIView"
            else:
                use_cls = raw_cls
            
            lines.append(f"    {use_cls} *{var_name} = [[{use_cls} alloc] init];")
            
            # Basic properties
            if "backgroundColor" in subview and subview["backgroundColor"]:
                color = subview["backgroundColor"]
                if "rgba" in color:
                    r, g, b, a = color["rgba"]
                    lines.append(f"    {var_name}.backgroundColor = [UIColor colorWithRed:{r} green:{g} blue:{b} alpha:{a}];")
            
            if "alpha" in subview:
                lines.append(f"    {var_name}.alpha = {subview['alpha']};")
            
            if "hidden" in subview and subview["hidden"]:
                lines.append(f"    {var_name}.hidden = YES;")

            # Type specific (only if we know it's a Label)
            if subview.get("type") == "Label":
                # Ensure we cast to UILabel if it was mapped to UIView
                label_var = var_name
                if use_cls == "UIView":
                    label_var = f"((UILabel *){var_name})"
                
                lines.append(f"    {label_var}.text = @\"{subview.get('text', '')}\";")

            lines.append(f"    [{parent_name} addSubview:{var_name}];")
            
            # Layout
            frame = subview.get("frame", {})
            if frame:
                lines.append(f"    {var_name}.frame = CGRectMake({frame['x']}, {frame['y']}, {frame['width']}, {frame['height']});")

            # Recursive call
            self.walk_view_tree(subview, var_name, lines)

    def get_var_name(self, view_info):
        if "accessibilityIdentifier" in view_info:
            name = view_info["accessibilityIdentifier"]
            return name.replace(" ", "_").replace("-", "_").lower()
        
        base = view_info["class"].lower()
        if base.startswith("ui"):
            base = base[2:]
        if base.startswith("_"):
            base = base[1:]
        return f"{base}_{self.view_counter}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python project_generator.py <dump.json> <output_dir>")
        sys.exit(1)
    
    with open(sys.argv[1], "r") as f:
        data = json.load(f)
    
    gen = ProjectGenerator(sys.argv[2])
    gen.generate(data)
