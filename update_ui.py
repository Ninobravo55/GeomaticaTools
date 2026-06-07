import re

path = r'c:\Users\GEOMATICA\V1.9\GeomaticaPe\Script\landsat_pansharpening.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

imports_old = """from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QLineEdit, QFileDialog, QMessageBox, QComboBox, QDialogButtonBox,
    QProgressDialog, QApplication, QWidget, QAbstractItemView,
)
from osgeo import gdal"""

imports_new = """from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QLineEdit, QMessageBox, QComboBox, QDialogButtonBox,
    QProgressDialog, QApplication, QWidget, QAbstractItemView,
)
from qgis.core import QgsProject, QgsRasterLayer, QgsMapLayerProxyModel
from qgis.gui import QgsMapLayerComboBox, QgsFileWidget
from osgeo import gdal"""

content = content.replace(imports_old, imports_new)

algo_old = """PANSHARP_ALGORITHMS = [
    "WeightedBrovey",   # GDAL VRT nativo — pesos espectrales configurables
    "SimpleBrovey",     # Brovey clasico (Python/NumPy)
    "GS",               # Gram-Schmidt Spectral Fusion (Python/NumPy)
    "HSV",              # Hue-Saturation-Value (Python/NumPy, optimo con RGB)
    "HCS",              # Hyperspherical Color Sharpening (Python/NumPy)
]"""

algo_new = """_ALGO_DISPLAY_MAP = {
    "Weighted Brovey (Nativo GDAL)": "WeightedBrovey",
    "Simple Brovey": "SimpleBrovey",
    "Gram-Schmidt (GS)": "GS",
    "Hue-Saturation-Value (HSV)": "HSV",
    "Hyperspherical Color Sharpening (HCS)": "HCS",
}
PANSHARP_ALGORITHMS = list(_ALGO_DISPLAY_MAP.keys())"""

content = content.replace(algo_old, algo_new)

# Find start of dialog classes
start_dialog = content.find('class _QGISSingleLayerPickerDialog(QDialog):')
if start_dialog == -1:
    start_dialog = content.find('class LandsatPansharpeningDialog(QDialog):')

end_dialog = content.find('class LandsatPansharpening:')

new_ui = """class LandsatPansharpeningDialog(QDialog):
    \"\"\"
    Interfaz nativa de QGIS para pansharpening:
      1. Banda Multiespectral (30 m) - QgsMapLayerComboBox
      2. Banda Pancromatica (15 m) - QgsMapLayerComboBox
      3. Algoritmo Pansharpening
      4. Remuestreo Pixel
      5. Salida Raster 15 m - QgsFileWidget
    \"\"\"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Landsat Pansharpening 30m -> 15m")
        self.resize(580, 360)
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(10)
        main.setContentsMargins(15, 15, 15, 15)

        desc = QLabel(
            "<b>Landsat Pansharpening</b> &mdash; Fusiona todas las bandas "
            "del raster multiespectral (30&nbsp;m) con la banda pancrom&aacute;tica "
            "(15&nbsp;m). Los nombres de banda se preservan en la salida."
        )
        desc.setWordWrap(True)
        main.addWidget(desc)

        sep = QLabel()
        sep.setFixedHeight(4)
        main.addWidget(sep)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(14)

        # 1. MS
        self.cb_ms = QgsMapLayerComboBox()
        self.cb_ms.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.cb_ms.layerChanged.connect(self._update_ms_info)
        form.addRow("<b>Banda Multiespectral 30m</b>", self.cb_ms)

        self.lbl_ms_info = QLabel("")
        self.lbl_ms_info.setStyleSheet("color:#4a7c59; font-size:11px; padding-left:2px;")
        form.addRow("", self.lbl_ms_info)

        # 2. PAN
        self.cb_pan = QgsMapLayerComboBox()
        self.cb_pan.setFilters(QgsMapLayerProxyModel.RasterLayer)
        form.addRow("<b>Banda Pancrom&aacute;tica 15m</b>", self.cb_pan)

        # 3. Algoritmo
        self.combo_alg = QComboBox()
        self.combo_alg.addItems(PANSHARP_ALGORITHMS)
        self.combo_alg.setCurrentText("Gram-Schmidt (GS)")
        self.combo_alg.currentTextChanged.connect(self._on_alg_changed)
        form.addRow("<b>Algoritmo Pansharpening</b>", self.combo_alg)

        self.lbl_alg_desc = QLabel("")
        self.lbl_alg_desc.setWordWrap(True)
        self.lbl_alg_desc.setStyleSheet("color:#555; font-size:11px; padding-left:2px;")
        form.addRow("", self.lbl_alg_desc)

        # 4. Remuestreo
        self.combo_resample = QComboBox()
        self.combo_resample.addItems(PAN_RESAMPLE)
        self.combo_resample.setCurrentText("Cubic")
        form.addRow("<b>Remuestreo Pixel</b>", self.combo_resample)

        # 5. Salida
        self.fw_out = QgsFileWidget()
        self.fw_out.setStorageMode(QgsFileWidget.SaveFile)
        self.fw_out.setFilter("GeoTIFF (*.tif *.tiff)")
        self.fw_out.setDialogTitle("Guardar raster de salida")
        
        try:
            le = self.fw_out.findChild(QLineEdit)
            if le:
                le.setPlaceholderText("[Guardar en archivo temporal]")
        except:
            pass
        form.addRow("<b>Salida Raster 15m</b>", self.fw_out)

        main.addLayout(form)
        main.addStretch(1)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Ejecutar")
        bb.accepted.connect(self._on_ok)
        bb.rejected.connect(self.reject)
        main.addWidget(bb)

        self._update_ms_info(self.cb_ms.currentLayer())
        self._on_alg_changed(self.combo_alg.currentText())

    def _update_ms_info(self, layer):
        if not layer:
            self.lbl_ms_info.setText("\u26a0 Selecciona una capa raster multiespectral.")
            self.lbl_ms_info.setStyleSheet("color:#b05000; font-size:11px; padding-left:2px;")
            self._ms_names = []
            self._ms_nbands = 0
            return
        
        path = layer.source()
        nb = _band_count(path)
        if nb > 0:
            names = []
            for i in range(1, nb + 1):
                nm = _detect_band_name_at(path, i) or _default_name(path, i)
                names.append(_safe_name(nm))
            preview = ", ".join(names[:5])
            if nb > 5:
                preview += f", ... (+{nb - 5} m\u00e1s)"
            self.lbl_ms_info.setText(f"\u2713 {nb} banda(s) detectada(s): {preview}")
            self.lbl_ms_info.setStyleSheet("color:#3a6b4a; font-size:11px; padding-left:2px;")
            self._ms_names = names
            self._ms_nbands = nb
        else:
            self.lbl_ms_info.setText("\u26a0 No se detectaron bandas v&aacute;lidas.")
            self.lbl_ms_info.setStyleSheet("color:#b05000; font-size:11px; padding-left:2px;")
            self._ms_names = []
            self._ms_nbands = 0

    def _on_alg_changed(self, algo_display):
        algo = _ALGO_DISPLAY_MAP.get(algo_display, "")
        desc = _ALGO_DESCRIPTIONS.get(algo, "")
        self.lbl_alg_desc.setText(desc)

    def _on_ok(self):
        ms_lyr = self.cb_ms.currentLayer()
        if not ms_lyr:
            QMessageBox.warning(self, "Pansharpening", "Selecciona el raster multiespectral (30 m).")
            return
        
        if getattr(self, '_ms_nbands', 0) == 0:
            QMessageBox.warning(self, "Pansharpening", "El raster multiespectral no tiene bandas v&aacute;lidas.")
            return

        pan_lyr = self.cb_pan.currentLayer()
        if not pan_lyr:
            QMessageBox.warning(self, "Pansharpening", "Selecciona la banda pancrom&aacute;tica (15 m).")
            return

        out_path = self.fw_out.filePath().strip()
        if not out_path:
            import tempfile
            out_path = os.path.join(tempfile.gettempdir(), f"_geomaticape_pansharpening_{os.getpid()}.tif")
        else:
            if not out_path.lower().endswith((".tif", ".tiff")):
                out_path += ".tif"

        n         = self._ms_nbands
        ms_paths  = [ms_lyr.source()] * n
        ms_bands  = list(range(1, n + 1))
        ms_names  = list(self._ms_names)

        pan_band = 1  # Fijo a la primera banda como se solicito

        algo_display = self.combo_alg.currentText()
        algorithm = _ALGO_DISPLAY_MAP.get(algo_display, "GS")
        resample  = self.combo_resample.currentText()
        compress  = "LZW"

        progress = QProgressDialog("Aplicando pansharpening...", "Cancelar", 0, 100, self)
        progress.setWindowTitle(f"Pansharpening — {algorithm}")
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()

        feedback = _DialogFeedback(progress)
        try:
            ejecutar_pansharpening(
                ms_paths=ms_paths, ms_bands=ms_bands, ms_names=ms_names,
                pan_path=pan_lyr.source(), pan_band=pan_band,
                out_path=out_path,
                algorithm=algorithm, weights=None,
                resample=resample, compress=compress,
                feedback=feedback,
            )
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Pansharpening — Error", str(e))
            return

        progress.close()

        # Cargar resultado en QGIS
        try:
            lyr = QgsRasterLayer(out_path, os.path.basename(out_path))
            if lyr.isValid():
                QgsProject.instance().addMapLayer(lyr)
        except Exception:
            pass

        QMessageBox.information(
            self, "Pansharpening completado",
            f"Algoritmo : {algo_display}\\n"
            f"Salida    : {out_path}\\n\\n"
            f"Bandas a 15 m:\\n  " + "\\n  ".join(
                f"{i+1}. {nm}" for i, nm in enumerate(ms_names)
            )
        )
        self.accept()

# ---------------------------------------------------------------------------
# Wrapper invocado desde el menu Geomaticape -> Procesamiento
# ---------------------------------------------------------------------------
"""

content = content[:start_dialog] + new_ui + content[end_dialog+77:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Exito")
