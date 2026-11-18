// Cut only the person (Vision person segmentation, accurate), keep full frame, save PNG.
import Foundation
import Vision
import CoreImage
import AppKit
let a = CommandLine.arguments
let ci = CIImage(contentsOf: URL(fileURLWithPath: a[1]))!
let req = VNGeneratePersonSegmentationRequest()
req.qualityLevel = .accurate
req.outputPixelFormat = kCVPixelFormatType_OneComponent8
try VNImageRequestHandler(ciImage: ci).perform([req])
let mask = CIImage(cvPixelBuffer: req.results!.first!.pixelBuffer)
let sx = ci.extent.width / mask.extent.width, sy = ci.extent.height / mask.extent.height
let m = mask.transformed(by: CGAffineTransform(scaleX: sx, y: sy))
let clear = CIImage(color: .clear).cropped(to: ci.extent)
let out = ci.applyingFilter("CIBlendWithMask", parameters: [kCIInputBackgroundImageKey: clear, kCIInputMaskImageKey: m])
let cg = CIContext().createCGImage(out, from: ci.extent, format: .RGBA8, colorSpace: CGColorSpace(name: CGColorSpace.sRGB)!)!
try NSBitmapImageRep(cgImage: cg).representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: a[2]))
print("ok")
