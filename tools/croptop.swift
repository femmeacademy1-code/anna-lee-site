// keep the top `h` pixel rows of a PNG
import Foundation
import AppKit
let a = CommandLine.arguments
let r = NSBitmapImageRep(data: try Data(contentsOf: URL(fileURLWithPath: a[1])))!
let keep = Int(a[3])!
let cg = r.cgImage!.cropping(to: CGRect(x: 0, y: 0, width: r.pixelsWide, height: keep))!
try NSBitmapImageRep(cgImage: cg).representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: a[2]))
print(cg.width, cg.height)
