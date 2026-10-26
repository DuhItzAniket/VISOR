# Rendering profile

Recorded 2026-10-26 from clean source 891e899 on the local Windows/headless OpenCV 4.11.0/Qt 6.11.2 environment. These are offscreen presentation measurements, not native interaction latency, registration accuracy or portable performance guarantees.

The profile analyzes the checked-in ORB fixture once, uniformly scales its images and existing feature/corner coordinates, and measures drawing and canvas upload separately. It does not redetect features at each resolution. Settings use keypoints, rainbow match lines and 6 px thickness. Each size has one excluded warmup and five measured repetitions.

The controlled comparison changes only the canvas class: the baseline loads that class from bc03d7e; both runs otherwise use 891e899 drawing code and identical parameters. Baseline source identity is explicit in the raw report. Every report includes exact runtime, source/input hashes and individual measurements. These source worktrees were clean during measurement. Run order and local cache/load effects can affect results; no cross-platform speed factor is claimed.

| Input size, each image | Baseline canvas upload median | Owned BGR upload median |
|---|---:|---:|
| 560 × 420 | 2.73 ms | 1.10 ms |
| 2240 × 1680 | 41.75 ms | 9.74 ms |
| 3920 × 2940 | 108.24 ms | 28.21 ms |

Raw evidence: [baseline](rendering-891e899-baseline.json), [owned BGR](rendering-891e899-current.json). The BGR path avoids a separate NumPy RGB channel-reversal copy and retains owned QImage bytes. Qt documents BGR888 and buffer-lifetime requirements in [QImage](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QImage.html).

Drawing still takes substantial time for large overlays. I17 moves it to one background worker with one replaceable pending style and cooperative cancellation. Tests hold the worker while verifying UI timer delivery, cancellation/input invalidation, latest-style delivery, safe close and consistent exports. This is separate from upload speed: QPixmap construction remains on the GUI thread. Native scaling, screen-reader, physical drag and interaction reviews remain I14.

To profile current code in a clean build environment:

```text
python scripts/profile_rendering.py --output build/rendering-new.json
```

Use QT_QPA_PLATFORM=offscreen when reproducing these offscreen measurements. The tool refuses to overwrite an existing output. A future comparison should retain the same inputs, settings and runtime and identify any substituted source implementation explicitly.
