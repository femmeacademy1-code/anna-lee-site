// Gently sharpen a transparent PNG without touching its alpha edge.
// usage: swift sharpen.swift in.png out.png radius intensity
import Foundation
import CoreImage
import AppKit
let a = CommandLine.arguments
guard let img = CIImage(contentsOf: URL(fileURLWithPath: a[1])) else { fatalError("read") }
let f = CIFilter(name: "CIUnsharpMask")!
f.setValue(img, forKey: kCIInputImageKey)
f.setValue(Double(a[3])!, forKey: kCIInputRadiusKey)
f.setValue(Double(a[4])!, forKey: kCIInputIntensityKey)
let out = f.outputImage!.cropped(to: img.extent)
let ctx = CIContext()
let cg = ctx.createCGImage(out, from: img.extent, format: .RGBA8, colorSpace: CGColorSpace(name: CGColorSpace.sRGB)!)!
let rep = NSBitmapImageRep(cgImage: cg)
try rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: a[2]))
print("saved", cg.width, cg.height)
