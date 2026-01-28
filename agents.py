import mesa
import mesa_geo as mg
import networkx as nx
from shapely.geometry import Point

class SafeZone(mg.GeoAgent):
    def __init__(self, model, geometry, crs):
        super().__init__(model, geometry, crs)
        self.capacity = 1000  # Example capacity

class Road(mg.GeoAgent):
    def __init__(self, model, geometry, crs):
        super().__init__(model, geometry, crs)
        self.length = geometry.length if geometry else 0

class Civilian(mg.GeoAgent):
    def __init__(self, model, geometry, crs):
        super().__init__(model, geometry, crs)
        self.in_safe_zone = False
        self.path = []
        self.speed = 0.0001  # degrees per step approx
        self.status = "Safe"
        self.destination_zone = None

    def step(self):
        if self.in_safe_zone:
            return

        # Check water level at current location
        for layer in self.model.space.layers:
            if isinstance(layer, mg.RasterLayer) and layer.name == 'water':
                # We assume raster is named 'water'
                pass # need proper access to water grid

        # Actually, let's keep it simple. If we don't have a path, compute one.
        if not self.path:
            self.find_path()

        if self.path:
            # Move towards next node
            target_node = self.path[0]
            # Since mesa-geo network is typically node-based matching geometries,
            # Let's just snap to the road nodes or interpolate.
            # Simplify: teleport to next node
            target_node = self.path[0]
            if hasattr(self.model, 'road_graph'):
                data = self.model.road_graph.nodes[target_node]
                target_point = Point(data['x'], data['y'])
            
            # Update location
            if hasattr(self, 'model') and target_point:
                self.geometry = target_point
                self.start_node = self.path.pop(0)

                # Check if arrived
                if not self.path:
                    self.in_safe_zone = True
                    self.status = "Saved"

    def find_path(self):
        if not self.model.safe_zones:
            return

        G = getattr(self.model, 'road_graph', None)
        if not G or not hasattr(self, 'start_node'):
            return
            
        import random
        import networkx as nx
        import osmnx as ox

        if not self.destination_zone:
            self.destination_zone = random.choice(list(self.model.safe_zones))
            
        target_pt = self.destination_zone.geometry.centroid
        
        try:
            target_node = ox.nearest_nodes(G, target_pt.x, target_pt.y)
        except AttributeError:
            try:
                target_node = ox.distance.nearest_nodes(G, target_pt.x, target_pt.y)
            except AttributeError:
                target_node = list(G.nodes())[0] # Fallback if API changed

        try:
            self.path = nx.shortest_path(G, self.start_node, target_node, weight='length')
            # Pop the first node since we are already there
            if self.path and self.path[0] == self.start_node:
                self.path.pop(0)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            self.path = []

