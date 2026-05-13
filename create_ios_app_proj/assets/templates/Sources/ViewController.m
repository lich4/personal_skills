#import "ViewController.h"

@implementation ViewController
- (void)viewDidLoad {
    [super viewDidLoad];
    self.view.backgroundColor = [UIColor whiteColor];
    UILabel *label = [[UILabel alloc] initWithFrame:self.view.bounds];
    label.text = @"Hello World JBDev";
    label.textAlignment = NSTextAlignmentCenter;
    [self.view addSubview:label];
}
@end
