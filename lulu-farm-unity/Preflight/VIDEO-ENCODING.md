# Actual Unity frame recordings → VFR video

Use the Mac's existing Command Line Tools, AVFoundation and VideoToolbox. No ffmpeg, Python multimedia package, download or system installation is required. This machine has Swift 6.3.3 and the macOS SDK available through `/usr/bin/xcrun`.

The recording must be stopped and contain `recording.json`, `frames.jsonl` and all original PNG files. The encoder verifies each PNG SHA256, dimensions and frame ordering before appending it. Input files are read only. Existing output files are never overwritten.

From the Unity project root:

```sh
sh Preflight/encode-vfr-recording.sh \
  Evidence/m1-manual-20261023/walkthrough-192249-665 \
  Evidence/m1-manual-20261023/walkthrough-vfr-r02.mp4
```

`.mov` is also supported, with the same H.264 encoding. Choose a fresh output name for each run. In an automation sandbox, the system video encoder may require the normal macOS execution context; the restricted attempt here could not start AVAssetWriter, whereas the same tool outside the sandbox encoded successfully. This is unrelated to installing dependencies.

Timing and image treatment:

- Append every PNG exactly once at its recorded elapsed time minus the first frame's timestamp. Preserve the original wall-clock variable intervals; do not use the requested capture FPS as a fixed playback rate.
- End the movie at the recording's actual stop time, relative to that first frame. Capture and PNG overhead remain present; this movie is not a device-performance measurement.
- Preserve native pixel size. H.264 requires even dimensions here, so an odd width/height receives only black padding at the right/bottom. The 867×434 M1 capture becomes 868×434. No crop, resize, fabricated frame or motion interpolation occurs.
- H.264 is lossy and uses standard sRGB/Rec.709 transfer; the original PNGs remain the pixel-level evidence. The movie is a convenient playback derivative.
- Read the encoded video back and check the real sample count, every presentation timestamp and total duration. AVAssetReader's zero-byte control markers are excluded and separately recorded; they are not image frames.

The output `.encoding.json` contains input hashes, source-frame hash checks, sample count, time error, output SHA256, dimensions and remaining inspection status. A successful encode does not mark the game or video visually accepted.

Decode selected actual video frames for visual comparison:

```sh
/usr/bin/xcrun swift -module-cache-path /tmp/lulu-farm-swift-module-cache \
  Preflight/extract-encoded-vfr-frames.swift \
  Evidence/m1-manual-20261023/walkthrough-vfr-r02.mp4 \
  Evidence/m1-manual-20261023/walkthrough-192249-665 \
  Evidence/m1-manual-20261023/decoded-vfr-r02 \
  0 28 40 1254
```

The decode tool refuses to reuse its output directory. Open the resulting frames and compare with the originals; keep the extraction record and visual findings. These are labeled decoded video images, never passed off as fresh Unity screenshots.

The commands above have already been executed for this recording; choose fresh names to rerun. `walkthrough-vfr-r02.mp4.encoding.json` verifies 1,255 real frames, 188.639883 seconds and a maximum per-frame timestamp error of 0.000016651 seconds. `decoded-vfr-r02/visual-review.json` records the four decoded images actually opened. Earlier encoder verification probes are separated under `Evidence/m1-manual-20261023/encoding-probes/`.

For the first M1 recording, the original review's near-house obstruction, near clipping and cyan transition defects remain valid. Video encoding does not repair them. The sequence proves limited Walk/Idle in the Editor; Run, mouse-drag orbit, the full farm route, installed-build operation and device performance require their own actual evidence.

The independent asset-index file/path/hash audit is in `delivery-index-check-20261023.json`. It does not change asset selections or promote Unity/visual/device acceptance.
