# Architecture

VISOR separates its desktop presentation from computer-vision processing:

```text
PySide6 UI -> analysis pipeline -> feature engines -> matching -> geometry
        \\________________ structured analysis results ________________/
```

The UI owns file selection, drag-and-drop, view state, and presentation. Feature engines own OpenCV extractor configuration and conversion to domain records. Matching chooses a norm appropriate to descriptor type. Geometry estimates planar transforms and reports validity and limitations. The pipeline coordinates the work and records actual elapsed time. Long-running operations belong in a Qt worker, not the event thread.

The initial product does not claim universal 3D pose recovery. Homography projects a planar reference into the target; derived scale and rotation are image-space estimates.

