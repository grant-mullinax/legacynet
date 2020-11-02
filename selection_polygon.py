from edge import Edge
from node import Node


class SelectionPolygon:
    def __init__(self, points, scene):
        first_node = Node()
        print((points[0][0], points[0][1]))
        first_node.setPos(points[0][0], points[0][1])

        self._nodes = [first_node]
        self._edges = []
        self._scene = scene

        self._scene.addItem(first_node)

        for idx in range(1, len(points)):
            new_node = Node()
            new_node.setPos(points[idx][0], points[idx][1])
            self._scene.addItem(new_node)

            new_edge = Edge(self._nodes[idx - 1], new_node)
            self._scene.addItem(new_edge)

            self._nodes.append(new_node)
            self._edges.append(new_edge)

        # connect last edge to first
        new_edge = Edge(self._nodes[len(self._nodes) - 1], self._nodes[0])
        self._scene.addItem(new_edge)
        self._edges.append(new_edge)

    def detach_from_scene(self):
        for edge in self._edges:
            self._scene.removeItem(edge)

        for node in self._nodes:
            self._scene.removeItem(node)
