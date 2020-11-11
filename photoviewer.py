from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QBrush, QPen
from PyQt5.QtWidgets import QGraphicsRectItem

from selection_polygon import SelectionPolygon


class PhotoViewer(QtWidgets.QGraphicsView):
    photoClicked = QtCore.pyqtSignal(QtCore.QPoint)

    def __init__(self, parent):
        super(PhotoViewer, self).__init__(parent)

        # all gravestone-denoting polygons
        self.selection_polygons = []

        self._box_creation_mode = False
        self._box_start_point = None
        self._box_graphic = None

        self.ctrl_held = False

        # the polygons currently selected for editing
        self.selected_polygons = []
        self.update_selected = None

        self._zoom = 0
        self._empty = True
        self.scene = QtWidgets.QGraphicsScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()

        self.scene.addItem(self._photo)
        self.setScene(self.scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def add_selected_polygon(self, polygon):
        self.selected_polygons.append(polygon)

        if self.update_selected is not None:
            self.update_selected()

    def remove_selected_polygon(self, polygon):
        self.selected_polygons.remove(polygon)

        if self.update_selected is not None:
            self.update_selected(self.selected_polygons)

    def has_photo(self):
        return not self._empty

    def pixmap(self):
        return self._photo

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.has_photo():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0

    def set_photo(self, pixmap=None):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)

            self.selection_polygons = []
            self._box_creation_mode = False
            self._box_start_point = None
            self._box_graphic = None

            for poly in self.selected_polygons:
                self.remove_selected_polygon(poly)
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
        self.fitInView()

    def wheelEvent(self, event):
        if self.has_photo():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0

    def delete_selected(self):
        for selected in self.selected_polygons:
            selected.deselect()
            self.scene.removeItem(selected)
            self.selection_polygons.remove(selected)

        self.selected_polygons = []

    def any_selection_nodes_under_mouse(self):
        for selected in self.selected_polygons:
            for node in selected._nodes:
                if node.isUnderMouse():
                    return True

        return False

    def mousePressEvent(self, event):
        if not self._photo.isUnderMouse():
            return
        if self._box_creation_mode:
            photo_click_point = self.mapToScene(event.pos()).toPoint()
            self._box_start_point = photo_click_point

            self._box_graphic = QGraphicsRectItem(0, 0, 1, 1)
            self._box_graphic.setBrush(QBrush(Qt.transparent))
            self._box_graphic.setPen(QPen(Qt.blue, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            self._box_graphic.setPos(photo_click_point)
            self.scene.addItem(self._box_graphic)
        else:
            # this is pretty hacky and ugly but it works well
            if not self.any_selection_nodes_under_mouse() and not self.ctrl_held:
                for polygon in self.selected_polygons:
                    polygon.deselect()
                self.selected_polygons = []
                if self.update_selected is not None:
                    self.update_selected()
            super(PhotoViewer, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._box_creation_mode and self._box_start_point is not None and self._box_graphic is not None:
            mouse_point = self.mapToScene(event.pos()).toPoint()
            self._box_graphic.setRect(QRectF(0,
                                             0,
                                             mouse_point.x() - self._box_start_point.x(),
                                             mouse_point.y() - self._box_start_point.y()).normalized())
        super(PhotoViewer, self).mouseMoveEvent(event)

    def add_selection_polygon(self, selection_polygon):
        self.selection_polygons.append(selection_polygon)
        self.scene.addItem(selection_polygon)

    def mouseReleaseEvent(self, event):
        if not self._photo.isUnderMouse():
            return
        if self._box_creation_mode and self._box_start_point is not None:
            photo_click_point = self.mapToScene(event.pos()).toPoint()
            polygon_coords = [QPointF(self._box_start_point.x(), self._box_start_point.y()),
                              QPointF(self._box_start_point.x(), photo_click_point.y()),
                              QPointF(photo_click_point.x(), photo_click_point.y()),
                              QPointF(photo_click_point.x(), self._box_start_point.y())]
            selection_polygon = SelectionPolygon(polygon_coords, self)
            self.add_selection_polygon(selection_polygon)
            self.scene.removeItem(self._box_graphic)

            self._box_creation_mode = False
            self._box_start_point = None
            self._box_graphic = None
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        else:
            super(PhotoViewer, self).mouseReleaseEvent(event)

    def pixmap_width_and_height(self):
        return self._photo.pixmap().width(), self._photo.pixmap().height()