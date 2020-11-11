import io

from PIL.ImageQt import ImageQt, toqpixmap
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QBuffer, QPointF
from PyQt5.QtGui import QIntValidator, QImage, QPixmap
from PyQt5.QtWidgets import QSizePolicy, QLineEdit, QComboBox, QInputDialog

from photoviewer import PhotoViewer
from database import Database
import coordmap

from ml import inference, image_cut
import tensorflow as tf
from PIL import Image

from selection_polygon import SelectionPolygon


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

        # CREATE LEFT LAYOUT
        # load image button
        self.load_btn = QtWidgets.QPushButton()
        self.load_btn.setText('Load image')
        # self.load_btn.setStyleSheet("padding: 20px 15px 20px 15px")
        self.load_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.load_btn.clicked.connect(self.load_image)

        # create box button
        self.create_box_btn = QtWidgets.QPushButton(self)
        self.create_box_btn.setText('Create box')
        self.create_box_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.create_box_btn.setStyleSheet("padding: 20px 15px 20px 15px")
        self.create_box_btn.setShortcut("h")
        self.create_box_btn.clicked.connect(self.box_creation_mode)

        # import button
        self.import_btn = QtWidgets.QPushButton(self)
        self.import_btn.setText('Import')
        self.import_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.import_btn.clicked.connect(self.open_db)

        # export button
        self.export_btn = QtWidgets.QPushButton(self)
        self.export_btn.setText('Export')
        self.export_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.export_btn.setStyleSheet("padding: 20px 15px 20px 15px")
        self.export_btn.clicked.connect(self.export_polygons)

        # export button
        self.detect_btn = QtWidgets.QPushButton(self)
        self.detect_btn.setText('Detect')
        self.detect_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.detect_btn.setStyleSheet("padding: 20px 15px 20px 15px")
        self.detect_btn.clicked.connect(self.detect_gravestones)

        vert_left_layout = QtWidgets.QVBoxLayout()
        vert_left_layout.setAlignment(QtCore.Qt.AlignTop)
        vert_left_layout.addWidget(self.load_btn)
        vert_left_layout.addWidget(self.create_box_btn)
        vert_left_layout.addWidget(self.import_btn)
        vert_left_layout.addWidget(self.export_btn)
        vert_left_layout.addStretch()
        vert_left_layout.addWidget(self.detect_btn)
        # END CREATE LEFT LAYOUT

        # CREATE RIGHT LAYOUT
        vert_right_layout = QtWidgets.QVBoxLayout()
        vert_right_layout.setAlignment(QtCore.Qt.AlignTop)

        self.database_label = QtWidgets.QLabel(self)
        self.database_label.setText('DB')
        self.database_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        vert_right_layout.addWidget(self.database_label)

        self.table_select = QComboBox()
        self.table_select.addItems([])
        self.table_select.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        vert_right_layout.addWidget(self.table_select)

        self.create_table_btn = QtWidgets.QPushButton()
        self.create_table_btn.setText('Create Table')
        self.create_table_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.create_table_btn.clicked.connect(self.create_table_popup)
        vert_right_layout.addWidget(self.create_table_btn)

        poly_edit_layout = QtWidgets.QGridLayout()
        self.id_label = QtWidgets.QLabel()
        self.id_label.setText("id")
        poly_edit_layout.addWidget(self.id_label, 0, 0)

        self.id_txtbox = QLineEdit(self)
        self.id_txtbox.setMaximumWidth(100)
        self.id_txtbox.setValidator(QIntValidator())
        poly_edit_layout.addWidget(self.id_txtbox, 0, 1)

        self.row_label = QtWidgets.QLabel()
        self.row_label.setText("row")
        poly_edit_layout.addWidget(self.row_label, 1, 0)

        self.row_txtbox = QLineEdit(self)
        self.row_txtbox.setMaximumWidth(100)
        poly_edit_layout.addWidget(self.row_txtbox, 1, 1)

        self.col_label = QtWidgets.QLabel()
        self.col_label.setText("col")
        poly_edit_layout.addWidget(self.col_label, 2, 0)

        self.col_txtbox = QLineEdit(self)
        self.col_txtbox.setMaximumWidth(100)
        self.col_txtbox.setValidator(QIntValidator())
        poly_edit_layout.addWidget(self.col_txtbox, 2, 1)

        self.poly_update = QtWidgets.QPushButton()
        self.poly_update.setText('Update')
        self.poly_update.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.poly_update.setShortcut("u")
        self.poly_update.clicked.connect(self.update_selected)
        poly_edit_layout.addWidget(self.poly_update, 3, 1)

        vert_right_layout.addLayout(poly_edit_layout)
        vert_right_layout.addStretch()
        # END CREATE RIGHT LAYOUT

        # arrange layout
        grid_layout = QtWidgets.QGridLayout(self)
        grid_layout.setColumnStretch(1, 3)

        grid_layout.addLayout(vert_left_layout, 0, 0)
        grid_layout.addWidget(self.viewer, 0, 1)
        grid_layout.addLayout(vert_right_layout, 0, 3)

    def load_image(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', 'c:/',
                                                          "Image files (*.jpg *.gif *.png *.tiff)")
        # user didnt select anything
        if file_name[0] == '':
            return

        # todo maybe fix loading it twice, i tried really hard to get it to only work once but all the methods i
        # tried crashed mysteriously, even those in the pil library itself see toqpixmap()
        self.image = Image.open(file_name[0])
        pixmap = QtGui.QPixmap(file_name[0])
        self.viewer.set_photo(pixmap)

    def open_db(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', 'c:/',
                                                          "Database files (*.db)")
        # user didnt select anything
        if file_name[0] == '':
            return

        self.database_manager = Database(file_name[0])
        self.table_select.clear()
        self.table_select.addItems(self.database_manager.get_tables())

    def load_db(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', 'c:/',
                                                          "Database files (*.db)")
        # user didnt select anything
        if file_name[0] == '':
            return

        dataframe = self.database_manager.get_gravestones(self.table_select.currentText(), file_name[0])
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

    def box_creation_mode(self):
        if not self.viewer.has_photo():
            return
        self.viewer._box_creation_mode = True
        self.viewer.setDragMode(QtWidgets.QGraphicsView.NoDrag)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.viewer.delete_selected()
        elif event.key() == Qt.Key_Control:
            self.viewer.ctrl_held = True

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.viewer.ctrl_held = False

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
            if self.id_txtbox.text() != "":
                polygon.id = int(self.id_txtbox.text())
            if self.row_txtbox.text() != "":
                polygon.row = int(self.row_txtbox.text())
            if self.col_txtbox.text() != "":
                polygon.col = int(self.col_txtbox.text())

    def export_polygons(self):
        print("exporting..")
        self.database_manager.create_table(self.table_select.currentText())
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

        self.database_manager.export_table(self.table_select.currentText(), "testgravesite.geojson")
        print("export complete")

    def detect_gravestones(self):
        if self.detect_fn is None:
            saved_model_path = 'ml/run10/saved_model'
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
