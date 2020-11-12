import unittest

from PyQt5.QtCore import QPointF

import coordmap


class CoordMapTest(unittest.TestCase):
    def test_coord_map(self):
        coord = coordmap.coordinate_map(QPointF(50, 50),
                                        0.0, 0.0,
                                        200.0, 400.0,
                                        100, 100)
        self.assertEqual(coord.x(), 100.0, "coord x should be 100")
        self.assertEqual(coord.y(), 200.0, "coord x should be 200")

    def test_pixel_map(self):
        coord = coordmap.pixel_map(QPointF(50.0, 50.0),
                                   0.0, 0.0,
                                   100.0, 100.0,
                                   402, 800)
        self.assertEqual(coord.x(), 201.0, "coord x should be 201")
        self.assertEqual(coord.y(), 400.0, "coord x should be 400")


if __name__ == '__main__':
    unittest.main()
