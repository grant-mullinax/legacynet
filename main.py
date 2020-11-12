import io
import json

from PIL.ImageQt import ImageQt, toqpixmap
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QBuffer, QPointF, QRegExp
from PyQt5.QtGui import QIntValidator, QImage, QPixmap, QRegExpValidator
from PyQt5.QtWidgets import QSizePolicy, QLineEdit, QComboBox, QInputDialog, QMessageBox

from QPropertyLineEdit import QPropertyLineEdit
from photoviewer import PhotoViewer
from database import Database
import coordmap

from ml import inference, image_cut
import tensorflow as tf
import PIL
from PIL import Image

from selection_polygon import SelectionPolygon

# turns off max size on pil img loads
PIL.Image.MAX_IMAGE_PIXELS = None


def all_are_same(polys, selector):
    value = selector(polys[0])
    for poly in polys:
        if selector(poly) != value:
            return False
    return True


def format_selection_text(polys, selector):
    if not all_are_same(polys, selector):
        return "..."
    if selector(polys[0]) is not None:
        return str(selector(polys[0]))
    else:
        return ""


class Window(QtWidgets.QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.viewer = PhotoViewer(self)
        self.viewer.update_selected = self.selected_updated

        self.image = None
        self.detect_fn = None
        self.database_manager = None

        # Set of buttons to disable, and enable after loading an image
        self.enable_on_load = []

        # Create the layout
        self._create_left_layout()
        self._create_right_layout()

        # arrange layout
        grid_layout = QtWidgets.QGridLayout(self)
        grid_layout.setColumnStretch(1, 3)
        grid_layout.addLayout(self.vert_left_layout, 0, 0)
        grid_layout.addWidget(self.viewer, 0, 1)
        grid_layout.addLayout(self.vert_right_layout, 0, 3)

        # Disable UI buttons
        for button in self.enable_on_load:
            button.setEnabled(False)

    def _create_left_layout(self):
        ''' Build left layout '''
        self.vert_left_layout = QtWidgets.QVBoxLayout()
        self.vert_left_layout.setAlignment(QtCore.Qt.AlignTop)

        # load image button
        self.load_btn = QtWidgets.QPushButton()
        self.load_btn.setText('Load Image')
        # self.load_btn.setStyleSheet("padding: 20px 15px 20px 15px")
        self.load_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.load_btn.clicked.connect(self.load_image)
        self.vert_left_layout.addWidget(self.load_btn)

        # create box button
        self.create_box_btn = QtWidgets.QPushButton(self)
        self.create_box_btn.setText('Create Box')
        self.create_box_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.create_box_btn.setStyleSheet("padding: 20px 15px 20px 15px")
        self.create_box_btn.setShortcut("h")
        self.create_box_btn.clicked.connect(self.enable_box_creation_mode)
        self.enable_on_load.append(self.create_box_btn)
        self.vert_left_layout.addWidget(self.create_box_btn)

        # opem db button
        self.open_db_btn = QtWidgets.QPushButton(self)
        self.open_db_btn.setText('Open Database')
        self.open_db_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.open_db_btn.clicked.connect(self.open_db)
        self.enable_on_load.append(self.open_db_btn)
        self.vert_left_layout.addWidget(self.open_db_btn)

        # import button
        self.import_btn = QtWidgets.QPushButton(self)
        self.import_btn.setText('Import Table')
        self.import_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.import_btn.clicked.connect(self.import_table)
        self.enable_on_load.append(self.import_btn)
        self.vert_left_layout.addWidget(self.import_btn)

        # export db button
        self.export_db_btn = QtWidgets.QPushButton(self)
        self.export_db_btn.setText('Export Table')
        self.export_db_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.export_db_btn.clicked.connect(self.export_as_database)
        self.enable_on_load.append(self.export_db_btn)
        self.vert_left_layout.addWidget(self.export_db_btn)

        # export js button
        self.export_js_btn = QtWidgets.QPushButton(self)
        self.export_js_btn.setText('Export Geojson')
        self.export_js_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.export_js_btn.clicked.connect(self.export_as_geojson)
        self.enable_on_load.append(self.export_js_btn)
        self.vert_left_layout.addWidget(self.export_js_btn)

        # Padding
        self.vert_left_layout.addStretch()

        # Detect button
        self.detect_btn = QtWidgets.QPushButton(self)
        self.detect_btn.setText('Detect')
        self.detect_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.detect_btn.setStyleSheet("padding: 20px 15px 20px 15px")
        self.detect_btn.clicked.connect(self.detect_gravestones)
        self.enable_on_load.append(self.detect_btn)
        self.vert_left_layout.addWidget(self.detect_btn)

    def _create_right_layout(self):
        ''' Build right layout '''
        self.vert_right_layout = QtWidgets.QVBoxLayout()
        self.vert_right_layout.setAlignment(QtCore.Qt.AlignTop)

        # Begin 'Edit Polygon' group
        poly_edit_group = QtWidgets.QGroupBox('Edit Polygon')

        # QIntValidator allows commas for some reason- and thats a problem. so we make our own
        integer_validator = QRegExpValidator(QRegExp("[0-9]*"))

        # ID label
        poly_edit_layout = QtWidgets.QGridLayout()
        self.id_label = QtWidgets.QLabel()
        self.id_label.setText("id")
        poly_edit_layout.addWidget(self.id_label, 0, 0)

        # ID box
        self.id_txtbox = QPropertyLineEdit(self)
        self.id_txtbox.setMaximumWidth(100)
        self.id_txtbox.setValidator(integer_validator)
        poly_edit_layout.addWidget(self.id_txtbox, 0, 1)

        # Row label
        self.row_label = QtWidgets.QLabel()
        self.row_label.setText("row")
        poly_edit_layout.addWidget(self.row_label, 1, 0)

        # Row box
        self.row_txtbox = QPropertyLineEdit(self)
        self.row_txtbox.setMaximumWidth(100)
        self.id_txtbox.setValidator(integer_validator)
        poly_edit_layout.addWidget(self.row_txtbox, 1, 1)

        # Col label
        self.col_label = QtWidgets.QLabel()
        self.col_label.setText("col")
        poly_edit_layout.addWidget(self.col_label, 2, 0)

        # Col box
        self.col_txtbox = QPropertyLineEdit(self)
        self.col_txtbox.setMaximumWidth(100)
        self.id_txtbox.setValidator(integer_validator)
        poly_edit_layout.addWidget(self.col_txtbox, 2, 1)

        # Update button
        self.poly_update = QtWidgets.QPushButton()
        self.poly_update.setText('Update')
        self.poly_update.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.poly_update.setShortcut("u")
        self.poly_update.clicked.connect(self.update_selected)
        poly_edit_layout.addWidget(self.poly_update, 3, 1)

        # Close 'Edit Polygon' group
        poly_edit_group.setLayout(poly_edit_layout)
        self.vert_right_layout.addWidget(poly_edit_group)

        # Begin 'Database' group
        db_box_group = QtWidgets.QGroupBox('Database')
        db_box_layout = QtWidgets.QVBoxLayout()

        # DB combo box
        self.table_select = QComboBox()
        self.table_select.addItems([])
        self.table_select.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        db_box_layout.addWidget(self.table_select)

        # Create table button
        self.create_table_btn = QtWidgets.QPushButton()
        self.create_table_btn.setText('Create Table')
        self.create_table_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.create_table_btn.clicked.connect(self.create_table_popup)
        db_box_layout.addWidget(self.create_table_btn)

        # Close 'Database' group
        db_box_group.setLayout(db_box_layout)
        self.vert_right_layout.addWidget(db_box_group)

        self.vert_right_layout.addStretch()

    def load_image(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', 'c:/',
                                                          "Image files (*.jpg *.gif *.png *.tif *.tiff)")
        # user didnt select anything
        if file_name == '':
            return

        # todo maybe fix loading it twice, i tried really hard to get it to only work once but all the methods i
        # tried crashed mysteriously, even those in the pil library itself see toqpixmap()
        self.image = Image.open(file_name)
        pixmap = QtGui.QPixmap(file_name)

        # Remove any present polygons before loading
        self.viewer.remove_all()

        # Enable interface buttons
        for button in self.enable_on_load:
            button.setEnabled(True)

        self.viewer.set_photo(pixmap)

    def open_db(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', '',
                                                          "Database files (*.db)")
        # user didnt select anything
        if file_name == '':
            return

        self.database_manager = Database(file_name)
        self.table_select.clear()
        self.table_select.addItems(self.database_manager.get_tables())

    def import_table(self):
        if self.database_manager is None:
            no_db_prompt = QMessageBox()
            no_db_prompt.setText("Please load a database to export a table from!")
            no_db_prompt.setWindowTitle("No database selected")
            no_db_prompt.exec()
            return
        dataframe = self.database_manager.get_gravestones(self.table_select.currentText())
        for _, row in dataframe.iterrows():
            polygon_coords = [QPointF(row['toplx'], row['toply']),
                              QPointF(row['toprx'], row['topry']),
                              QPointF(row['botrx'], row['botry']),
                              QPointF(row['botlx'], row['botly'])]
            width, height = self.viewer.pixmap_width_and_height()
            adjusted_polygon_points = [coordmap.pixel_map(point,
                                                          28.713230, -81.554677,
                                                          28.718706, -81.547055,
                                                          width, height) for point in polygon_coords]
            selection_polygon = SelectionPolygon(adjusted_polygon_points, self.viewer)

            self.viewer.add_selection_polygon(selection_polygon)

    def enable_box_creation_mode(self):
        if not self.viewer.has_photo():
            return
        self.viewer.box_creation_mode = True
        self.viewer.setDragMode(QtWidgets.QGraphicsView.NoDrag)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.viewer.delete_selected()
        elif event.key() == Qt.Key_Control:
            self.viewer.ctrl_held = True
        elif event.key() == Qt.Key_Shift:
            self.viewer.line_selection_mode = True
            self.viewer.setDragMode(QtWidgets.QGraphicsView.NoDrag)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.viewer.ctrl_held = False
        elif event.key() == Qt.Key_Shift:
            self.viewer.scene.removeItem(self.viewer.line_graphic)

            self.viewer.line_selection_mode = False
            self.viewer.start_line_select = None
            self.viewer.line_graphic = None
            self.viewer.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def selected_updated(self):
        polygons = self.viewer.selected_polygons
        if len(polygons) == 0:
            self.id_txtbox.setText("")
            self.row_txtbox.setText("")
            self.col_txtbox.setText("")
            return
        self.id_txtbox.setText(format_selection_text(polygons, lambda p: p.id))
        self.row_txtbox.setText(format_selection_text(polygons, lambda p: p.row))
        self.col_txtbox.setText(format_selection_text(polygons, lambda p: p.col))

    def update_selected(self):
        for polygon in self.viewer.selected_polygons:
            if self.id_txtbox.text() != "" and self.id_txtbox.text() != "...":
                polygon.id = int(self.id_txtbox.text())
            if self.row_txtbox.text() != "" and self.row_txtbox.text() != "...":
                polygon.row = int(self.row_txtbox.text())
            if self.col_txtbox.text() != "" and self.col_txtbox.text() != "...":
                polygon.col = int(self.col_txtbox.text())

    def export_as_database(self):
        print("exporting..")

        if self.database_manager is None:
            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save file', '',
                                                              "Database File (*.db)")

            if file_name == '':
                return

            self.database_manager = Database(file_name)
            self.create_table_popup()

        for polygon in self.viewer.selection_polygons:
            width, height = self.viewer.pixmap_width_and_height()
            centroid = coordmap.coordinate_map(polygon.centroid(),
                                               28.713230, -81.554677,
                                               28.718706, -81.547055,
                                               width, height)
            adjusted_polygon_points = [coordmap.coordinate_map(point,
                                                               28.713230, -81.554677,
                                                               28.718706, -81.547055,
                                                               width, height) for point in polygon.polygon_points]

            self.database_manager.add_entry(self.table_select.currentText(), polygon.id, polygon.row, polygon.col,
                                            toplx=adjusted_polygon_points[0].x(), toply=adjusted_polygon_points[0].y(),
                                            toprx=adjusted_polygon_points[1].x(), topry=adjusted_polygon_points[1].y(),
                                            botrx=adjusted_polygon_points[2].x(), botry=adjusted_polygon_points[2].y(),
                                            botlx=adjusted_polygon_points[3].x(), botly=adjusted_polygon_points[3].y(),
                                            centroidx=centroid.x(), centroidy=centroid.y())
        print("export complete")

    def export_as_geojson(self):
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save file', '',
                                                          "Geojson File (*.geojson)")
        # user didnt select anything
        if file_name == '':
            return

        geojson = {'type': 'FeatureCollection', 'name': self.table_select.currentText(), 'features': []}
        for polygon in self.viewer.selection_polygons:
            width, height = self.viewer.pixmap_width_and_height()
            centroid = coordmap.coordinate_map(polygon.centroid(),
                                               28.713230, -81.554677,
                                               28.718706, -81.547055,
                                               width, height)
            adjusted_polygon_points = [coordmap.coordinate_map(point,
                                                               28.713230, -81.554677,
                                                               28.718706, -81.547055,
                                                               width, height) for point in polygon.polygon_points]
            feature = {'type': 'Feature', 'properties': {}, 'geometry': {'type': 'MultiPolygon', 'coordinates': []}}
            feature['geometry']['coordinates'] = [
                [adjusted_polygon_points[0].x(), adjusted_polygon_points[0].y()],
                [adjusted_polygon_points[1].x(), adjusted_polygon_points[1].y()],
                [adjusted_polygon_points[2].x(), adjusted_polygon_points[2].y()],
                [adjusted_polygon_points[3].x(), adjusted_polygon_points[3].y()],
                [adjusted_polygon_points[0].x(), adjusted_polygon_points[0].y()]]
            feature['properties']['id'] = polygon.id
            feature['properties']['row'] = polygon.row
            feature['properties']['col'] = polygon.col
            feature['properties']['centroid'] = [centroid.x(), centroid.y()]
            geojson['features'].append(feature)

        with open(file_name, 'w') as output_file:
            json.dump(geojson, output_file, indent=2)

    def detect_gravestones(self):
        if self.detect_fn is None:
            saved_model_path = 'ml/run9/saved_model'
            self.detect_fn = tf.saved_model.load(saved_model_path)
        print("model loaded!")

        width, height = self.image.size

        # Make the crops
        image_cuts = image_cut.crop_image_with_padding((320, 320), 300, self.image)

        # Run model on image crops
        print(f'Running inferences...')
        detections = inference.detect_and_combine(self.detect_fn, image_cuts,
                                                  (width, height), 300,
                                                  0.35)

        for box in detections['detection_boxes']:
            polygon_coords = [QPointF(box[1] * width, box[0] * height),
                              QPointF(box[1] * width, box[2] * height),
                              QPointF(box[3] * width, box[2] * height),
                              QPointF(box[3] * width, box[0] * height)]
            selection_polygon = SelectionPolygon(polygon_coords, self.viewer)
            self.viewer.add_selection_polygon(selection_polygon)

    def create_table_popup(self):
        item, ok = QInputDialog.getText(self, "Enter Table To Create", "Table To Create:")
        if ok and item:
            self.database_manager.create_table(item)
            self.table_select.addItem(item)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.setWindowTitle("LegacyNet Editor")
    window.setGeometry(500, 300, 1000, 600)
    window.show()

    sys.exit(app.exec_())
