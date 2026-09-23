from __future__ import annotations

import math
from collections import Counter
from typing import Literal

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QScrollArea,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from visor.models import AnalysisResult, ComparisonResult, KeypointInfo


class AnalysisDetailsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._mode: Literal["tab", "tree"] = "tab"
        self._data: list[tuple[str, list[tuple[str, list[tuple[str, str]]]]]] = []
        self._keypoints_data: list[tuple[str, list[tuple[str, str]]]] = []

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._widget: QWidget | None = None

        self._apply_theme()
        self.set_mode(self._mode)

    def _apply_theme(self) -> None:
        self.setStyleSheet("""
            QWidget {
                background-color: #171c23;
                color: #c8d1dd;
            }
            QGroupBox {
                border: 1px solid #29313b;
                margin-top: 2ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 3px;
                color: #c8d1dd;
            }
            QLabel {
                color: #c8d1dd;
            }
            .value-label {
                font-family: Consolas;
                font-size: 11px;
            }
            QTreeWidget {
                border: 1px solid #29313b;
            }
            QTreeWidget::item {
                padding: 2px;
            }
            QTabWidget::pane {
                border: 1px solid #29313b;
            }
            QTabBar::tab {
                background: #171c23;
                border: 1px solid #29313b;
                padding: 6px 12px;
                color: #c8d1dd;
            }
            QTabBar::tab:selected {
                background: #29313b;
                font-weight: bold;
            }
        """)

    def set_mode(self, mode: str) -> None:
        if mode not in ("tab", "tree"):
            raise ValueError(f"Invalid mode: {mode}")
        self._mode = mode  # type: ignore[assignment]
        self._render()

    def clear(self) -> None:
        self._data.clear()
        self._keypoints_data.clear()
        self._render()

    def populate(self, result: AnalysisResult) -> None:
        self._data = [
            self._build_overview(result),
            self._build_engine(result),
            self._build_geometry(result),
            self._build_performance(result),
        ]
        self._keypoints_data.clear()
        self._render()

    def populate_comparison(self, comparison: ComparisonResult) -> None:
        self._data = [
            self._build_overview(comparison.sift),
            self._build_engine(comparison.sift),
            self._build_geometry(comparison.sift),
            self._build_performance(comparison.sift),
            self._build_overview(comparison.orb),
            self._build_engine(comparison.orb),
            self._build_geometry(comparison.orb),
            self._build_performance(comparison.orb),
        ]
        self._keypoints_data.clear()
        self._render()

    def append_keypoint(self, engine: str, index: int, point: KeypointInfo) -> None:
        title = f"SELECTED {engine.upper()} KEYPOINT #{index}"
        fields = [
            ("X", f"{point.x:.2f} px"),
            ("Y", f"{point.y:.2f} px"),
            ("Size", f"{point.size:.2f} px"),
            ("Angle", f"{point.angle:.1f}°"),
            ("Response", f"{point.response:.6f}"),
            ("Pyramid octave", str(point.octave)),
            ("Class ID", str(point.class_id)),
        ]
        self._keypoints_data.append((title, fields))
        self._render()

    def _render(self) -> None:
        if self._widget is not None:
            self._layout.removeWidget(self._widget)
            self._widget.deleteLater()
            self._widget = None

        if not self._data and not self._keypoints_data:
            self._widget = QLabel("No analysis data available.")
            self._widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(self._widget)
            return

        if self._mode == "tab":
            self._widget = self._render_tab_mode()
        else:
            self._widget = self._render_tree_mode()

        self._layout.addWidget(self._widget)

    def _render_tab_mode(self) -> QWidget:
        tabs = QTabWidget()
        for tab_title, groups in self._data:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            layout = QVBoxLayout(content)
            for group_title, fields in groups:
                group_box = QGroupBox(group_title)
                form = QFormLayout(group_box)
                for key, value in fields:
                    val_label = QLabel(value)
                    val_label.setProperty("class", "value-label")
                    form.addRow(QLabel(key + ":"), val_label)
                layout.addWidget(group_box)
            layout.addStretch(1)
            scroll.setWidget(content)
            tabs.addTab(scroll, tab_title)

        if self._keypoints_data:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            layout = QVBoxLayout(content)
            for title, fields in self._keypoints_data:
                group_box = QGroupBox(title)
                form = QFormLayout(group_box)
                for key, value in fields:
                    val_label = QLabel(value)
                    val_label.setProperty("class", "value-label")
                    form.addRow(QLabel(key + ":"), val_label)
                layout.addWidget(group_box)
            layout.addStretch(1)
            scroll.setWidget(content)
            tabs.addTab(scroll, "Selected Keypoints")

        return tabs

    def _render_tree_mode(self) -> QWidget:
        tree = QTreeWidget()
        tree.setHeaderLabels(["Category / Property", "Value"])
        tree.setColumnCount(2)
        tree.header().setStretchLastSection(True)

        for tab_title, groups in self._data:
            tab_item = QTreeWidgetItem(tree, [tab_title, ""])
            tab_item.setExpanded(True)
            for group_title, fields in groups:
                group_item = QTreeWidgetItem(tab_item, [group_title, ""])
                group_item.setExpanded(True)
                for key, value in fields:
                    item = QTreeWidgetItem(group_item, [key, value])
                    item.setFont(1, self._get_value_font())

        if self._keypoints_data:
            kp_item = QTreeWidgetItem(tree, ["Selected Keypoints", ""])
            kp_item.setExpanded(True)
            for title, fields in self._keypoints_data:
                group_item = QTreeWidgetItem(kp_item, [title, ""])
                group_item.setExpanded(True)
                for key, value in fields:
                    item = QTreeWidgetItem(group_item, [key, value])
                    item.setFont(1, self._get_value_font())

        tree.resizeColumnToContents(0)
        return tree

    def _get_value_font(self) -> QFont:
        return QFont("Consolas", 11)

    def _keypoint_statistics(self, keypoints: tuple[KeypointInfo, ...]) -> tuple[float, float, float, str]:
        if not keypoints:
            return 0.0, 0.0, 0.0, "none"
        mean_size = sum(point.size for point in keypoints) / len(keypoints)
        mean_response = sum(point.response for point in keypoints) / len(keypoints)
        sine = sum(math.sin(math.radians(point.angle)) for point in keypoints)
        cosine = sum(math.cos(math.radians(point.angle)) for point in keypoints)
        mean_angle = math.degrees(math.atan2(sine, cosine)) % 360
        octave_counts = Counter(point.octave for point in keypoints)
        octaves = ", ".join(f"{level}: {count}" for level, count in octave_counts.most_common(5))
        return mean_size, mean_response, mean_angle, octaves

    def _build_overview(self, result: AnalysisResult) -> tuple[str, list[tuple[str, list[tuple[str, str]]]]]:
        ref_file = result.reference_path.name
        tgt_file = result.target_path.name
        rw, rh = result.reference_size
        tw, th = result.target_size
        
        groups = [
            ("INPUT", [
                ("Reference", f"{ref_file} ({rw} x {rh} px)"),
                ("Target", f"{tgt_file} ({tw} x {th} px)"),
            ]),
            ("EXTRACTION", [
                ("Reference keypoints", str(len(result.reference_features.keypoints))),
                ("Target keypoints", str(len(result.target_features.keypoints))),
                ("Extraction time (ref)", f"{result.reference_features.extraction_ms:.1f} ms"),
                ("Extraction time (target)", f"{result.target_features.extraction_ms:.1f} ms"),
            ]),
            ("MATCHING", [
                ("Raw matches (KNN pairs)", str(result.match_set.candidate_count)),
                ("Good matches", str(result.match_set.good_count)),
                ("Matcher", result.match_set.matcher),
                ("Filter", f"{result.match_set.filter_name} ({result.match_set.threshold})"),
            ])
        ]
        return f"Overview ({result.engine})", groups

    def _build_engine(self, result: AnalysisResult) -> tuple[str, list[tuple[str, list[tuple[str, str]]]]]:
        engine = result.engine
        config = result.engine_configuration
        ref = result.reference_features
        target = result.target_features
        
        mean_size, mean_response, mean_angle, octaves = self._keypoint_statistics(target.keypoints)
        
        if engine == "SIFT":
            groups = [
                ("SIFT CONFIGURATION", [
                    ("Max features", str(config.get("max_features", 0))),
                    ("Octave layers", str(config.get("octave_layers", 3))),
                    ("Contrast threshold", str(config.get("contrast_threshold", 0.04))),
                    ("Edge threshold", str(config.get("edge_threshold", 10.0))),
                    ("Sigma", str(config.get("sigma", 1.6))),
                ]),
                ("KEYPOINT STATISTICS", [
                    ("Total", str(len(target.keypoints))),
                    ("Mean size", f"{mean_size:.2f} px"),
                    ("Mean response", f"{mean_response:.6f}"),
                    ("Mean angle", f"{mean_angle:.1f}°"),
                    ("Octave distribution", octaves),
                ]),
                ("DESCRIPTOR", [
                    ("Dimensions", str(ref.descriptor_info.dimensions)),
                    ("Type", ref.descriptor_info.dtype),
                    ("Distance", ref.descriptor_info.distance),
                    ("Memory", f"{target.descriptor_info.bytes_used} bytes"),
                ])
            ]
        else:
            groups = [
                ("ORB CONFIGURATION", [
                    ("Max features", str(config.get("max_features", 1500))),
                    ("Scale factor", str(config.get("scale_factor", 1.2))),
                    ("Pyramid levels", str(config.get("levels", 8))),
                    ("Edge threshold", str(config.get("edge_threshold", 31))),
                    ("First level", str(config.get("first_level", 0))),
                    ("WTA_K", str(config.get("wta_k", 2))),
                    ("Score type", str(config.get("score_type", "HARRIS"))),
                    ("Patch size", str(config.get("patch_size", 31))),
                    ("FAST threshold", str(config.get("fast_threshold", 20))),
                ]),
                ("KEYPOINT STATISTICS", [
                    ("Total", str(len(target.keypoints))),
                    ("Mean size", f"{mean_size:.2f} px"),
                    ("Mean response", f"{mean_response:.6f}"),
                    ("Mean angle", f"{mean_angle:.1f}°"),
                    ("Pyramid-level distribution", octaves),
                ]),
                ("DESCRIPTOR", [
                    ("Length", f"{ref.descriptor_info.dimensions} bytes / {ref.descriptor_info.dimensions * 8} bits"),
                    ("Type", ref.descriptor_info.dtype),
                    ("Distance", ref.descriptor_info.distance),
                    ("Memory", f"{target.descriptor_info.bytes_used} bytes"),
                ])
            ]
        return f"Engine ({engine})", groups

    def _build_geometry(self, result: AnalysisResult) -> tuple[str, list[tuple[str, list[tuple[str, str]]]]]:
        g = result.geometry
        
        inliers = [
            ("Inlier count", str(g.inlier_count)),
            ("Outlier count", str(g.outlier_count)),
            ("Inlier ratio", f"{g.inlier_ratio:.1%}"),
            ("Mean reprojection error", f"{g.reprojection_error_px:.2f} px" if g.reprojection_error_px is not None else "unavailable"),
        ]
        
        if g.valid and g.projected_corners and len(g.projected_corners) == 4 and g.center:
            tl, tr, br, bl = g.projected_corners
            cx, cy = g.center
            loc = [
                ("Detected", "yes"),
                ("Center", f"({cx:.1f}, {cy:.1f}) px"),
                ("Top-left", f"({tl[0]:.1f}, {tl[1]:.1f}) px"),
                ("Top-right", f"({tr[0]:.1f}, {tr[1]:.1f}) px"),
                ("Bottom-right", f"({br[0]:.1f}, {br[1]:.1f}) px"),
                ("Bottom-left", f"({bl[0]:.1f}, {bl[1]:.1f}) px"),
            ]
        else:
            loc = [
                ("Detected", "no"),
                ("Center", "unavailable"),
                ("Top-left", "unavailable"),
                ("Top-right", "unavailable"),
                ("Bottom-right", "unavailable"),
                ("Bottom-left", "unavailable"),
            ]
            
        groups = [
            ("STATUS", [
                ("Valid", "yes" if g.valid else "no"),
                ("Message", g.message),
            ]),
            ("INLIERS", inliers),
            ("LOCALIZATION", loc)
        ]
        return f"Geometry ({result.engine})", groups

    def _build_performance(self, result: AnalysisResult) -> tuple[str, list[tuple[str, list[tuple[str, str]]]]]:
        p = result.performance
        groups = [
            ("TIMING", [
                ("Image loading", f"{p.image_loading_ms:.1f} ms"),
                ("Extraction (reference)", f"{p.extraction_reference_ms:.1f} ms"),
                ("Extraction (target)", f"{p.extraction_target_ms:.1f} ms"),
                ("Matching", f"{p.matching_ms:.1f} ms"),
                ("Geometry", f"{p.geometry_ms:.1f} ms"),
                ("Total", f"{p.total_ms:.1f} ms"),
            ])
        ]
        return f"Performance ({result.engine})", groups
