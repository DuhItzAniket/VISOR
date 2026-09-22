# Architecture

VISOR separates its desktop presentation from computer-vision processing:

```text
PySide6 UI -> analysis pipeline -> feature engines -> matching -> geometry
        \\________________ structured analysis results ________________/
```

The UI owns file selection, drag-and-drop, view state, and presentation. Feature engines own OpenCV SIFT/ORB extraction and convert keypoints/descriptors to domain records. Matching chooses L2, Hamming, or Hamming2 according to descriptor type and applies a Lowe ratio filter. Geometry estimates planar transforms and reports validity and limitations. The pipeline coordinates image decoding, extraction, matching, geometry, overlays, and actual elapsed time. The Qt analysis worker keeps processing off the event thread.

The initial product does not claim universal 3D pose recovery. Homography projects a planar reference into the target; derived scale and rotation are image-space estimates.
