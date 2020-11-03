from PyQt5 import QtCore, QtGui, QtWidgets

from selection_polygon import SelectionPolygon


class PhotoViewer(QtWidgets.QGraphicsView):
    photoClicked = QtCore.pyqtSignal(QtCore.QPoint)

    def __init__(self, parent):
        super(PhotoViewer, self).__init__(parent)

        # all gravestone-denoting polygons
        self.selection_polygons = []

        self._box_creation_mode = False
        self._box_start_point = None

        # the polygons currently selected for editing
        self.selected_polygons = []

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

    def has_photo(self):
        return not self._empty

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
        else:
            # this is pretty hacky and ugly but it works well
            if not self.any_selection_nodes_under_mouse():
                for polygon in self.selected_polygons:
                    polygon.deselect()
                self.selected_polygons = []
            super(PhotoViewer, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if not self._photo.isUnderMouse():
            return
        if self._box_creation_mode:
            photo_click_point = self.mapToScene(event.pos()).toPoint()
            polygon_coords = [(self._box_start_point.x(), self._box_start_point.y()),
                              (self._box_start_point.x(), photo_click_point.y()),
                              (photo_click_point.x(), photo_click_point.y()),
                              (photo_click_point.x(), self._box_start_point.y())]
            selection_polygon = SelectionPolygon(polygon_coords, self)
            self.selection_polygons.append(selection_polygon)
            # self._scene.addItem(selection_polygon)

            self._box_creation_mode = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        else:
            super(PhotoViewer, self).mouseReleaseEvent(event)
