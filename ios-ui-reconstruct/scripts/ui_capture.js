import ObjC from "frida-objc-bridge";

/** 
 * FOUNDATION: UI Extractors 
 */

function getVisibleViewController(root) {
    if (!root) return null;
    if (root.isKindOfClass_(ObjC.classes.UINavigationController)) {
        return getVisibleViewController(root.visibleViewController());
    }
    if (root.isKindOfClass_(ObjC.classes.UITabBarController)) {
        return getVisibleViewController(root.selectedViewController());
    }
    if (root.presentedViewController()) {
        return getVisibleViewController(root.presentedViewController());
    }
    return root;
}

function getViewInfo(view) {
    if (!view) return null;
    var info = {
        class: view.class().toString(),
        frame: {
            x: view.frame()[0][0],
            y: view.frame()[0][1],
            width: view.frame()[1][0],
            height: view.frame()[1][1]
        },
        windowFrame: {
            x: 0, y: 0, width: 0, height: 0
        },
        alpha: view.alpha(),
        isHidden: view.isHidden(),
        subviews: []
    };

    try {
        var bounds = view.bounds();
        var winRect = view.convertRect_toView_(bounds, null);
        info.windowFrame = {
            x: winRect[0][0],
            y: winRect[0][1],
            width: winRect[1][0],
            height: winRect[1][1]
        };
    } catch(e) {}

    try {
        if (view.isKindOfClass_(ObjC.classes.UILabel)) {
            info.text = view.text() ? view.text().toString() : "";
        } else if (view.isKindOfClass_(ObjC.classes.UIButton)) {
            var title = view.titleForState_(0);
            info.title = title ? title.toString() : "";
        }
    } catch (e) {}

    var subviews = view.subviews();
    for (var i = 0; i < subviews.count(); i++) {
        var subInfo = getViewInfo(subviews.objectAtIndex_(i));
        if (subInfo) info.subviews.push(subInfo);
    }
    return info;
}

/**
 * PRIMITIVE ACTIONS: Thread-Safe & Stable
 */

rpc.exports = {
    dump: function() {
        if (!ObjC.available) return { error: "ObjC runtime not available" };
        var result = null;
        
        // Dump is relatively safe but we'll still use main thread for consistency if needed
        // For dump, we often can read properties directly, but let's be safe.
        var app = ObjC.classes.UIApplication.sharedApplication();
        var window = app.keyWindow() || (app.windows().count() > 0 ? app.windows().objectAtIndex_(0) : null);
        if (!window) return { error: "No window found" };
        
        var rootVC = window.rootViewController();
        var currentVC = getVisibleViewController(rootVC);
        
        var vcTitle = "";
        if (currentVC) {
            try {
                if (currentVC.title()) {
                    vcTitle = currentVC.title().toString();
                } else if (currentVC.navigationItem() && currentVC.navigationItem().title()) {
                    vcTitle = currentVC.navigationItem().title().toString();
                }
            } catch (e) {}
        }
        
        return {
            vcClass: currentVC ? currentVC.class().toString() : "Unknown",
            title: vcTitle,
            hierarchy: getViewInfo(window)
        };
    },
    
    clickByText: function(targetText) {
        var found = false;
        
        // Find matched control in background (ObjC.choose is slow)
        ObjC.choose(ObjC.classes.UIControl, {
            onMatch: function(control) {
                var matched = false;
                if (control.isKindOfClass_(ObjC.classes.UIButton)) {
                    var t = control.titleForState_(0);
                    if (t && t.toString() === targetText) matched = true;
                }
                
                if (!matched) {
                    var subviews = control.subviews();
                    for (var i = 0; i < subviews.count(); i++) {
                        var sub = subviews.objectAtIndex_(i);
                        if (sub.isKindOfClass_(ObjC.classes.UILabel) && sub.text() && sub.text().toString() === targetText) {
                            matched = true;
                            break;
                        }
                    }
                }

                if (matched) {
                    // CRITICAL: Perform action on Main Thread
                    ObjC.schedule(ObjC.mainQueue, function() {
                        control.sendActionsForControlEvents_(1 << 6);
                    });
                    found = true;
                    return 'stop';
                }
            },
            onComplete: function() {}
        });

        // TabBar fallback
        if (!found) {
            ObjC.choose(ObjC.classes.UITabBar, {
                onMatch: function(tabBar) {
                    var items = tabBar.items();
                    for (var i = 0; i < items.count(); i++) {
                        var item = items.objectAtIndex_(i);
                        if (item.title() && item.title().toString() === targetText) {
                            ObjC.schedule(ObjC.mainQueue, function() {
                                tabBar.setSelectedItem_(item);
                                var delegate = tabBar.delegate();
                                if (delegate && delegate.respondsToSelector_(ObjC.selector("tabBar:didSelectItem:"))) {
                                    delegate.tabBar_didSelectItem_(tabBar, item);
                                }
                            });
                            found = true;
                            return 'stop';
                        }
                    }
                },
                onComplete: function() {}
            });
        }
        
        return found;
    },

    clickAt: function(x, y) {
        // CRITICAL: All UI logic in main thread
        ObjC.schedule(ObjC.mainQueue, function() {
            try {
                var app = ObjC.classes.UIApplication.sharedApplication();
                var window = app.keyWindow() || (app.windows().count() > 0 ? app.windows().objectAtIndex_(0) : null);
                if (!window) return;

                var point = [x, y]; // Correct CGPoint [x, y]
                var view = window.hitTest_withEvent_(point, null);
                
                if (view) {
                    var target = view;
                    // Bubble up to nearest UIControl
                    while (target && !target.isKindOfClass_(ObjC.classes.UIControl)) {
                        target = target.superview();
                    }
                    if (target) {
                        target.sendActionsForControlEvents_(1 << 6);
                    }
                }
            } catch (e) {
                console.log("clickAt error: " + e);
            }
        });
        return true; 
    },

    goBack: function() {
        ObjC.schedule(ObjC.mainQueue, function() {
            var app = ObjC.classes.UIApplication.sharedApplication();
            var window = app.keyWindow() || (app.windows().count() > 0 ? app.windows().objectAtIndex_(0) : null);
            var rootVC = window.rootViewController();
            var currentVC = getVisibleViewController(rootVC);
            
            if (currentVC.navigationController()) {
                currentVC.navigationController().popViewControllerAnimated_(true);
            } else if (currentVC.presentingViewController()) {
                currentVC.dismissViewControllerAnimated_completion_(true, null);
            }
        });
        return true;
    },

    highlightAt: function(x, y, colorStr) {
        ObjC.schedule(ObjC.mainQueue, function() {
            try {
                var app = ObjC.classes.UIApplication.sharedApplication();
                var window = app.keyWindow() || (app.windows().count() > 0 ? app.windows().objectAtIndex_(0) : null);
                if (!window) return;

                var point = [x, y];
                var view = window.hitTest_withEvent_(point, null);
                
                if (view) {
                    var target = view;
                    while (target && !target.isKindOfClass_(ObjC.classes.UIControl)) {
                        target = target.superview();
                    }
                    var highlightTarget = target || view;
                    var UIColor = ObjC.classes.UIColor;
                    var color = UIColor.redColor();
                    if (colorStr === "green") color = UIColor.greenColor();
                    else if (colorStr === "blue") color = UIColor.blueColor();
                    else if (colorStr === "yellow") color = UIColor.yellowColor();

                    highlightTarget.layer().setBorderColor_(color.CGColor());
                    highlightTarget.layer().setBorderWidth_(3.0);
                }
            } catch(e) {
                console.log("highlight error: " + e);
            }
        });
        return true;
    },

    highlightByText: function(targetText, colorStr) {
        var found = false;
        
        ObjC.choose(ObjC.classes.UIControl, {
            onMatch: function(control) {
                var matched = false;
                if (control.isKindOfClass_(ObjC.classes.UIButton)) {
                    var t = control.titleForState_(0);
                    if (t && t.toString() === targetText) matched = true;
                }
                
                if (!matched) {
                    var subviews = control.subviews();
                    for (var i = 0; i < subviews.count(); i++) {
                        var sub = subviews.objectAtIndex_(i);
                        if (sub.isKindOfClass_(ObjC.classes.UILabel) && sub.text() && sub.text().toString() === targetText) {
                            matched = true;
                            break;
                        }
                    }
                }

                if (matched) {
                    ObjC.schedule(ObjC.mainQueue, function() {
                        var UIColor = ObjC.classes.UIColor;
                        var color = UIColor.redColor();
                        if (colorStr === "green") color = UIColor.greenColor();
                        else if (colorStr === "blue") color = UIColor.blueColor();
                        else if (colorStr === "yellow") color = UIColor.yellowColor();

                        control.layer().setBorderColor_(color.CGColor());
                        control.layer().setBorderWidth_(3.0);
                    });
                    found = true;
                }
            },
            onComplete: function() {}
        });

        // Always check UILabels too, in case there are plain labels with that text
        ObjC.choose(ObjC.classes.UILabel, {
            onMatch: function(label) {
                if (label.text() && label.text().toString() === targetText) {
                    ObjC.schedule(ObjC.mainQueue, function() {
                        var UIColor = ObjC.classes.UIColor;
                        var color = UIColor.redColor();
                        if (colorStr === "green") color = UIColor.greenColor();
                        else if (colorStr === "blue") color = UIColor.blueColor();
                        else if (colorStr === "yellow") color = UIColor.yellowColor();

                        label.layer().setBorderColor_(color.CGColor());
                        label.layer().setBorderWidth_(3.0);
                    });
                    found = true;
                }
            },
            onComplete: function() {}
        });
        
        return found;
    },

    drawBBoxes: function(boxesJson) {
        ObjC.schedule(ObjC.mainQueue, function() {
            try {
                var boxes = JSON.parse(boxesJson);
                var app = ObjC.classes.UIApplication.sharedApplication();
                var window = app.keyWindow() || (app.windows().count() > 0 ? app.windows().objectAtIndex_(0) : null);
                if (!window) return;
                
                var UIColor = ObjC.classes.UIColor;

                for (var i = 0; i < boxes.length; i++) {
                    var box = boxes[i];
                    var point = [box.x, box.y];
                    var view = window.hitTest_withEvent_(point, null);
                    if (view) {
                        var target = view;
                        while (target && !target.isKindOfClass_(ObjC.classes.UIControl)) {
                            target = target.superview();
                        }
                        var highlightTarget = target || view;
                        
                        var color = UIColor.redColor();
                        if (box.color === "green") color = UIColor.greenColor();
                        else if (box.color === "blue") color = UIColor.blueColor();
                        else if (box.color === "yellow") color = UIColor.yellowColor();
                        
                        highlightTarget.layer().setBorderColor_(color.CGColor());
                        highlightTarget.layer().setBorderWidth_(3.0);
                    }
                }
            } catch(e) {
                console.log("drawBBoxes error: " + e);
            }
        });
        return true;
    }
};
