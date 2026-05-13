import ObjC from 'frida-objc-bridge';

/**
 * UI Reconstruction Engine - Full Reconstruction (RPC Mode)
 * Using frida-objc-bridge + frida-compile + rpc.exports
 */

rpc.exports = {
    ping() {
        return "Pong from JS!";
    },
    
    async dump() {
        if (!ObjC.available) {
            throw new Error("ObjC bridge not available");
        }

        return new Promise((resolve, reject) => {
            ObjC.schedule(ObjC.mainQueue, function() {
                try {
                    var keyWindow = ObjC.classes.UIWindow.keyWindow();
                    if (!keyWindow) {
                        var windows = ObjC.classes.UIWindow.allWindows();
                        if (windows && windows.count() > 0) {
                            keyWindow = windows.objectAtIndex_(0);
                        }
                    }

                    if (!keyWindow) {
                        reject(new Error("No keyWindow found"));
                        return;
                    }

                    var rootVC = keyWindow.rootViewController();
                    if (!rootVC) {
                        reject(new Error("No rootViewController found"));
                        return;
                    }

                    var dump = {
                        class: keyWindow.$className,
                        handle: keyWindow.handle.toString(),
                        rootVC: dumpVC(rootVC)
                    };

                    resolve(dump);
                } catch (e) {
                    reject(new Error(e.toString()));
                }
            });
        });
    }
};

function dumpVC(vc) {
    if (!vc) return null;

    var result = {
        class: vc.$className,
        handle: vc.handle.toString(),
        view: dumpView(vc.view()),
        children: [],
        presented: vc.presentedViewController() ? dumpVC(vc.presentedViewController()) : null
    };

    var childVCs = vc.childViewControllers();
    var count = childVCs.count();
    for (var i = 0; i < count; i++) {
        result.children.push(dumpVC(childVCs.objectAtIndex_(i)));
    }

    return result;
}

function dumpView(view) {
    if (!view) return null;

    var frame = view.frame();
    var result = {
        class: view.$className,
        handle: view.handle.toString(),
        frame: {
            x: frame[0][0],
            y: frame[0][1],
            width: frame[1][0],
            height: frame[1][1]
        },
        alpha: view.alpha(),
        hidden: view.isHidden(),
        subviews: []
    };

    // Color
    var bgColor = view.backgroundColor();
    if (bgColor) {
        var components = bgColor.description().toString().match(/([\d\.]+)/g);
        if (components && components.length >= 4) {
             // Basic attempt to parse description, better to use CGColor if needed
             // But for now, let's just stick to a simpler representation if possible
        }
    }

    // Label specific
    if (view.isKindOfClass_(ObjC.classes.UILabel)) {
        result.type = "Label";
        var text = view.text();
        result.text = text ? text.toString() : "";
    }

    var subviews = view.subviews();
    var count = subviews.count();
    for (var i = 0; i < count; i++) {
        result.subviews.push(dumpView(subviews.objectAtIndex_(i)));
    }

    return result;
}

console.log("[*] JS Reconstruction Engine Loaded (RPC Mode).");
