from PyQt5.QtCore import QPointF


def coordinate_map(coordinate, x_min, y_min, x_max, y_max, img_width, img_height):
    coord_width = x_max - x_min
    coord_height = y_max - y_min

    return QPointF((coordinate.x() / img_width * coord_width) + x_min,
                   (coordinate.y() / img_height * coord_height) + y_min)


def pixel_map(coordinate, x_min, y_min, x_max, y_max, img_width, img_height):
    coord_width = x_max - x_min
    coord_height = y_max - y_min

    return QPointF((coordinate.x() - x_min) * img_width / coord_width,
                   (coordinate.y() - y_min) * img_height / coord_height)
