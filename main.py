from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QSizePolicy

from photoviewer import PhotoViewer


class Window(QtWidgets.QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.viewer = PhotoViewer(self)

        # load image button
        self.load_btn = QtWidgets.QToolButton(self)
        self.load_btn.setText('Load image')
        self.load_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.load_btn.setStyleSheet("padding: 50px 15px 50px 15px")
        self.load_btn.clicked.connect(self.load_image)

        # create box button
        self.create_box_btn = QtWidgets.QToolButton(self)
        self.create_box_btn.setText('Create box')
        self.create_box_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.create_box_btn.setStyleSheet("padding: 50px 15px 50px 15px")
        self.create_box_btn.setShortcut("h")
        self.create_box_btn.clicked.connect(self.box_creation_mode)

        # self.viewer.photoClicked.connect(self.photoClicked)

        # Arrange layout
        horiz_layout = QtWidgets.QHBoxLayout(self)

        vert_left_layout = QtWidgets.QVBoxLayout()
        vert_left_layout.setAlignment(QtCore.Qt.AlignTop)
        vert_left_layout.addWidget(self.load_btn)
        vert_left_layout.addWidget(self.create_box_btn)

        horiz_layout.addLayout(vert_left_layout)
        horiz_layout.addWidget(self.viewer)

    def load_image(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', 'c:/',
                                                          "Image files (*.jpg *.gif *.png *.tiff)")
        pixmap = QtGui.QPixmap(file_name[0])
        self.viewer.set_photo(QtGui.QPixmap(pixmap))

    def box_creation_mode(self):
        self.viewer._box_creation_mode = True
        self.viewer.setDragMode(QtWidgets.QGraphicsView.NoDrag)

    # def photoClicked(self, pos):
    #     if self.viewer.dragMode() == QtWidgets.QGraphicsView.NoDrag:
    #         self.editPixInfo.setText('%d, %d' % (pos.x(), pos.y()))


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.setGeometry(500, 300, 800, 600)
    window.show()
    sys.exit(app.exec_())
