
import json
import os
from pathlib import Path

class ProjectGenerator:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.classes_dir = self.output_dir / "Classes"
        self.classes_dir.mkdir(parents=True, exist_ok=True)
        self.processed_vcs = set()

    def generate(self, ui_data):
        if "viewControllers" in ui_data:
            for vc in ui_data["viewControllers"]:
                self.process_vc(vc)
        elif "rootVC" in ui_data:
            self.process_vc(ui_data["rootVC"])

    def process_vc(self, vc_info):
        class_name = vc_info["class"]
        if class_name in self.processed_vcs:
            return
        self.processed_vcs.add(class_name)

        print(f"[*] Generating {class_name}...")
        
        self.write_header(class_name)
        self.write_implementation(vc_info)

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

    def write_implementation(self, vc_info):
        class_name = vc_info["class"]
        view_info = vc_info.get("view", {})
        
        setup_views_code = self.generate_setup_views(view_info)

        content = f"""#import "{class_name}.h"
#import <Masonry/Masonry.h>

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
        with open(self.classes_dir / f"{class_name}.m", "w") as f:
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
            
            cls = subview["class"]
            lines.append(f"    {cls} *{var_name} = [[{cls} alloc] init];")
            
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

            # Type specific
            if subview.get("type") == "Label":
                lines.append(f"    {var_name}.text = @\"{subview.get('text', '')}\";")
                if "textColor" in subview and subview["textColor"] and "rgba" in subview["textColor"]:
                    r, g, b, a = subview["textColor"]["rgba"]
                    lines.append(f"    {var_name}.textColor = [UIColor colorWithRed:{r} green:{g} blue:{b} alpha:{a}];")

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
            # basic sanitization
            return name.replace(" ", "_").replace("-", "_")
        
        base = view_info["class"].lower()
        if base.startswith("ui"):
            base = base[2:]
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
