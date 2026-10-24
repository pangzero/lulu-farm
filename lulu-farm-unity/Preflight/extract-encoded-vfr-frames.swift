import Foundation
import AVFoundation
import ImageIO
import UniformTypeIdentifiers

// Inspection only: decode frames from an existing encoded movie. These PNGs are
// clearly separate from the untouched Unity framebuffer source sequence.
let args = CommandLine.arguments
guard args.count >= 5 else {
    fputs("Usage: swift extract-encoded-vfr-frames.swift VIDEO RECORDING_DIRECTORY NEW_OUTPUT_DIRECTORY FRAME_INDEX ...\n", stderr)
    exit(2)
}
do {
    let video = URL(fileURLWithPath: args[1])
    let root = URL(fileURLWithPath: args[2], isDirectory: true)
    let dest = URL(fileURLWithPath: args[3], isDirectory: true)
    guard !FileManager.default.fileExists(atPath: dest.path) else { throw NSError(domain: "Refusing overwrite", code: 1) }
    let rows = try String(contentsOf: root.appendingPathComponent("frames.jsonl"), encoding: .utf8)
        .split(whereSeparator: \.isNewline)
        .map { try JSONSerialization.jsonObject(with: Data($0.utf8)) as! [String: Any] }
    let first = rows[0]["elapsedSeconds"] as! Double
    let asset = AVURLAsset(url: video)
    let generator = AVAssetImageGenerator(asset: asset)
    generator.appliesPreferredTrackTransform = true
    generator.requestedTimeToleranceBefore = .zero
    generator.requestedTimeToleranceAfter = .zero
    try FileManager.default.createDirectory(at: dest, withIntermediateDirectories: true)
    var results: [[String: Any]] = []
    for arg in args.dropFirst(4) {
        guard let index = Int(arg), index >= 0, index < rows.count else { throw NSError(domain: "Invalid frame", code: 2) }
        let target = CMTime(seconds: (rows[index]["elapsedSeconds"] as! Double) - first, preferredTimescale: 60000)
        var actual = CMTime.zero
        let image = try generator.copyCGImage(at: target, actualTime: &actual)
        let path = dest.appendingPathComponent(String(format: "decoded-frame-%06d.png", index))
        guard let writer = CGImageDestinationCreateWithURL(path as CFURL, UTType.png.identifier as CFString, 1, nil) else {
            throw NSError(domain: "Cannot create PNG", code: 3)
        }
        CGImageDestinationAddImage(writer, image, nil)
        guard CGImageDestinationFinalize(writer) else { throw NSError(domain: "Cannot write PNG", code: 4) }
        results.append(["source_index": index, "requested_pts": CMTimeGetSeconds(target),
            "decoded_pts": CMTimeGetSeconds(actual), "file": path.path, "width": image.width, "height": image.height])
    }
    let record: [String: Any] = ["source_video": video.path, "source_png_directory": root.path,
        "type": "actual_video_decoded_frames_not_original_Unity_capture", "frames": results,
        "visual_inspection": "pending_actual_open"]
    try JSONSerialization.data(withJSONObject: record, options: [.prettyPrinted, .sortedKeys])
        .write(to: dest.appendingPathComponent("extraction.json"))
    print("Decoded \(results.count) actual video frames into \(dest.path)")
} catch {
    fputs("Decode inspection failed: \(error)\n", stderr)
    exit(1)
}
