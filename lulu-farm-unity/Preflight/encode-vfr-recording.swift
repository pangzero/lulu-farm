import Foundation
import AVFoundation
import CoreGraphics
import CoreVideo
import ImageIO
import CryptoKit

// Real Unity PNG recordings only. Every source frame is appended exactly once at
// its recorded wall-clock timestamp; no FPS normalization or interpolation.
struct CaptureFrame: Decodable {
    let index: Int
    let width: Int
    let height: Int
    let elapsedSeconds: Double
    let file: String
    let sha256: String
}

struct Recording: Decodable {
    let frames: Int
    let width: Int
    let height: Int
    let elapsedSeconds: Double
    let source: String
    let platform: String
    let sceneRevision: String
}

enum EncodeError: Error, CustomStringConvertible {
    case invalid(String)
    var description: String { switch self { case .invalid(let text): return text } }
}

func require(_ test: @autoclosure () -> Bool, _ message: String) throws {
    if !test() { throw EncodeError.invalid(message) }
}

func hash(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}

func run() throws {
    let args = CommandLine.arguments
    try require(args.count == 3, "Usage: encode-vfr-recording <recording-directory> <new-output.mp4|mov>")
    let root = URL(fileURLWithPath: args[1], isDirectory: true).standardizedFileURL
    let output = URL(fileURLWithPath: args[2]).standardizedFileURL
    try require(["mp4", "mov"].contains(output.pathExtension.lowercased()), "Output must be .mp4 or .mov")
    try require(!FileManager.default.fileExists(atPath: output.path), "Refusing to overwrite output")
    let auditURL = output.appendingPathExtension("encoding.json")
    try require(!FileManager.default.fileExists(atPath: auditURL.path), "Refusing to overwrite audit")
    let data = try Data(contentsOf: root.appendingPathComponent("frames.jsonl"))
    let frames = try String(decoding: data, as: UTF8.self).split(whereSeparator: \.isNewline)
        .map { try JSONDecoder().decode(CaptureFrame.self, from: Data($0.utf8)) }
    let recordingData = try Data(contentsOf: root.appendingPathComponent("recording.json"))
    let recording = try JSONDecoder().decode(Recording.self, from: recordingData)
    try require(!frames.isEmpty && frames.count == recording.frames, "Incomplete or empty stopped recording")
    try require(recording.source.contains("actual_Unity"), "Input must declare actual Unity framebuffer source")
    let first = frames[0]
    for (i, frame) in frames.enumerated() {
        try require(frame.index == i, "Frame order/index gap at \(i)")
        try require(frame.width == first.width && frame.height == first.height, "Resolution changed during capture")
        try require(frame.file == URL(fileURLWithPath: frame.file).lastPathComponent, "Frame path must be local basename")
        if i > 0 { try require(frame.elapsedSeconds > frames[i-1].elapsedSeconds, "Non-increasing timestamp") }
    }
    try require(recording.elapsedSeconds > frames.last!.elapsedSeconds, "Stopped recording lacks final-frame duration")
    let width = first.width + (first.width % 2)
    let height = first.height + (first.height % 2)
    let timeScale: CMTimeScale = 60000
    let duration = recording.elapsedSeconds - first.elapsedSeconds
    let fileType: AVFileType = output.pathExtension.lowercased() == "mov" ? .mov : .mp4
    let writer = try AVAssetWriter(outputURL: output, fileType: fileType)
    // Avoid the container's default 600-Hz duration quantization.
    writer.movieTimeScale = timeScale
    let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
        AVVideoCodecKey: AVVideoCodecType.h264,
        AVVideoWidthKey: width,
        AVVideoHeightKey: height,
        AVVideoCompressionPropertiesKey: [
            AVVideoAverageBitRateKey: max(8_000_000, width * height * 12),
            AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel,
            AVVideoAllowFrameReorderingKey: false,
            AVVideoMaxKeyFrameIntervalKey: 30
        ],
        AVVideoColorPropertiesKey: [
            AVVideoColorPrimariesKey: AVVideoColorPrimaries_ITU_R_709_2,
            AVVideoTransferFunctionKey: AVVideoTransferFunction_ITU_R_709_2,
            AVVideoYCbCrMatrixKey: AVVideoYCbCrMatrix_ITU_R_709_2
        ]
    ])
    input.expectsMediaDataInRealTime = false
    input.mediaTimeScale = timeScale
    let attrs: [String: Any] = [
        kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
        kCVPixelBufferWidthKey as String: width,
        kCVPixelBufferHeightKey as String: height,
        kCVPixelBufferCGImageCompatibilityKey as String: true,
        kCVPixelBufferCGBitmapContextCompatibilityKey as String: true,
        kCVPixelBufferIOSurfacePropertiesKey as String: [:]
    ]
    let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: attrs)
    try require(writer.canAdd(input), "AVFoundation rejected H.264 video input")
    writer.add(input)
    try require(writer.startWriting(), "Writer did not start: \(String(describing: writer.error))")
    writer.startSession(atSourceTime: .zero)
    var sourceHashChecks = 0
    do {
        for (i, frame) in frames.enumerated() {
            let waitStart = Date()
            while !input.isReadyForMoreMediaData {
                try require(writer.status == .writing, "Writer failed: \(String(describing: writer.error))")
                try require(Date().timeIntervalSince(waitStart) < 60, "Encoder blocked for 60 seconds")
                Thread.sleep(forTimeInterval: 0.005)
            }
            try autoreleasepool {
                let png = try Data(contentsOf: root.appendingPathComponent(frame.file))
                try require(hash(png) == frame.sha256, "SHA256 mismatch: \(frame.file)")
                sourceHashChecks += 1
                guard let source = CGImageSourceCreateWithData(png as CFData, nil),
                      let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
                    throw EncodeError.invalid("Unreadable PNG: \(frame.file)")
                }
                try require(image.width == frame.width && image.height == frame.height, "PNG dimensions mismatch")
                var buffer: CVPixelBuffer?
                let status = CVPixelBufferCreate(kCFAllocatorDefault, width, height,
                    kCVPixelFormatType_32BGRA, attrs as CFDictionary, &buffer)
                guard status == kCVReturnSuccess, let pixel = buffer else {
                    throw EncodeError.invalid("Cannot allocate pixel buffer: \(status)")
                }
                CVPixelBufferLockBaseAddress(pixel, [])
                defer { CVPixelBufferUnlockBaseAddress(pixel, []) }
                let flags = CGBitmapInfo.byteOrder32Little.rawValue | CGImageAlphaInfo.premultipliedFirst.rawValue
                guard let context = CGContext(data: CVPixelBufferGetBaseAddress(pixel), width: width,
                    height: height, bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(pixel),
                    space: CGColorSpace(name: CGColorSpace.sRGB)!, bitmapInfo: flags) else {
                    throw EncodeError.invalid("Cannot create PNG transfer context")
                }
                context.setFillColor(CGColor(gray: 0, alpha: 1))
                context.fill(CGRect(x: 0, y: 0, width: width, height: height))
                context.interpolationQuality = .none
                // Image stays at native pixel size, with only right/bottom black padding.
                context.draw(image, in: CGRect(x: 0, y: height - image.height, width: image.width, height: image.height))
                let pts = CMTime(seconds: frame.elapsedSeconds - first.elapsedSeconds, preferredTimescale: timeScale)
                try require(adaptor.append(pixel, withPresentationTime: pts), "Append failed: \(String(describing: writer.error))")
            }
            if i % 250 == 0 { print("encoded \(i + 1)/\(frames.count)") }
        }
        writer.endSession(atSourceTime: CMTime(seconds: duration, preferredTimescale: timeScale))
        input.markAsFinished()
        let finished = DispatchSemaphore(value: 0)
        writer.finishWriting { finished.signal() }
        try require(finished.wait(timeout: .now() + 60) == .success, "Finish timed out")
        try require(writer.status == .completed, "Encoding failed: \(String(describing: writer.error))")
    } catch {
        writer.cancelWriting()
        throw error
    }

    // Read compressed samples back: count and every PTS must match originals.
    // A successful encode alone is not a visual review or device benchmark.
    let asset = AVURLAsset(url: output)
    guard let track = asset.tracks(withMediaType: .video).first else {
        throw EncodeError.invalid("Encoded output has no video track")
    }
    let reader = try AVAssetReader(asset: asset)
    let readOutput = AVAssetReaderTrackOutput(track: track, outputSettings: nil)
    reader.add(readOutput)
    try require(reader.startReading(), "Cannot read encoded samples")
    var pts: [Double] = []
    var sampleDurations: [Double] = []
    var emptyControlSamples = 0
    while let sample = readOutput.copyNextSampleBuffer() {
        // AVAssetReader also emits zero-byte start/end/control markers. These
        // are not video frames and can have invalid presentation timestamps.
        if CMSampleBufferGetNumSamples(sample) == 0 && CMSampleBufferGetTotalSampleSize(sample) == 0 {
            emptyControlSamples += 1
            continue
        }
        try require(CMSampleBufferGetNumSamples(sample) == 1, "Unexpected multi-frame sample")
        pts.append(CMTimeGetSeconds(CMSampleBufferGetPresentationTimeStamp(sample)))
        sampleDurations.append(CMTimeGetSeconds(CMSampleBufferGetDuration(sample)))
    }
    try require(reader.status == .completed, "Readback failed: \(String(describing: reader.error))")
    try require(pts.count == frames.count, "Encoded frame count differs: \(pts.count) vs \(frames.count)")
    let maxError = zip(pts, frames).map { abs($0 - ($1.elapsedSeconds - first.elapsedSeconds)) }.max()!
    try require(maxError <= 1.0 / Double(timeScale) + 0.000001, "VFR PTS mismatch: \(maxError)")
    let actualDuration = CMTimeGetSeconds(asset.duration)
    try require(abs(actualDuration - duration) < 0.001, "Output duration differs from recorded interval")
    let audit: [String: Any] = [
        "tool": "macOS system AVFoundation/VideoToolbox; encode-vfr-recording.swift",
        "input_directory": root.path,
        "source_recording_sha256": hash(recordingData),
        "source_frames_jsonl_sha256": hash(data),
        "output": output.path,
        "output_sha256": hash(try Data(contentsOf: output, options: .mappedIfSafe)),
        "source_frame_count": frames.count,
        "source_frame_sha256_checks": sourceHashChecks,
        "encoded_sample_count": pts.count,
        "empty_container_control_samples_excluded": emptyControlSamples,
        "source_dimensions": [first.width, first.height],
        "encoded_dimensions": [width, height],
        "spatial_transformation": "Native pixel size; pad at right/bottom to even dimensions; no resize/crop",
        "temporal_transformation": "Subtract first captured timestamp; retain every relative wall-clock PTS; no duplication/interpolation",
        "source_first_elapsed_seconds": first.elapsedSeconds,
        "encoded_duration_seconds": actualDuration,
        "expected_duration_seconds": duration,
        "maximum_sample_pts_error_seconds": maxError,
        "sample_duration_range_seconds": [sampleDurations.min()!, sampleDurations.max()!],
        "video_codec": "H264 High, 8Mbps minimum, no frame reordering",
        "timing_mode": "VFR",
        "source_platform": recording.platform,
        "scene_revision": recording.sceneRevision,
        "original_frames_modified": false,
        "technical_readback": "passed_count_every_timestamp_and_duration",
        "visual_review": "pending_actual_video_frame_inspection",
        "device_performance": "not_a_benchmark_capture_overhead_present"
    ]
    try JSONSerialization.data(withJSONObject: audit, options: [.prettyPrinted, .sortedKeys]).write(to: auditURL)
    print("Wrote \(output.path) (\(pts.count) real frames, \(actualDuration)s VFR).")
    print("Audit: \(auditURL.path)")
}

do { try run() } catch {
    fputs("Encoding failed: \(error)\n", stderr)
    exit(1)
}
