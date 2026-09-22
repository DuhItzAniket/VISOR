# VISOR development rules

- Keep computer-vision logic independent from Qt widgets.
- Use typed Python and small modules with clear responsibilities.
- Use OpenCV's built-in SIFT and ORB implementations; do not train models.
- Run expensive image processing outside the UI thread.
- Label homography, scale, and rotation values as estimates and state planar assumptions.
- Keep documentation aligned with implemented behavior; do not describe roadmap items as complete.
- Do not commit secrets, local environments, caches, or generated build output.
- Prefer focused commits using conventional commit messages.

