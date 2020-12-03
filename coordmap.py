from PyQt5.QtCore import QPointF


# read for info


# from coord to pix
def pixel_map(coordinate, a, d, b, e, c, f):  # this is the order of the params in the file
    # formulas were found by solving
    # x1 = Ax + By + C
    # y1 = Dx + Ey + F
    #
    # for x and y
    # x = (-e/b * (x1 - c) + y1 - f)/(-e*a/b + d)
    # y = (x1 - c - Ax)/B

    x = (-e/b * (coordinate.x() - c) + coordinate.y() - f)/(-e*a/b + d)
    y = (coordinate.x() - c - a * x)/b
    return QPointF(x, y)


# from px to coords
def coordinate_map(coordinate, a, d, b, e, c, f):  # this is the order of the params in the file
    return QPointF((a * coordinate.x() + b * coordinate.y() + c),
                   (d * coordinate.x() + e * coordinate.y() + f))
