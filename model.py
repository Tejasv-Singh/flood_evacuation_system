import mesa
import mesa_geo as mg
import geopandas as gpd
import rasterio
import osmnx as ox
import numpy as np
import random
from shapely.geometry import Point

from agents import Civilian, Road, SafeZone

class EvacuationModel(mesa.Model):
    def __init__(self, num_civilians=50):
        super().__init__()
        self.num_civilians = num_civilians
        self.space = mg.GeoSpace()
        self.schedule = mesa.time.RandomActivation(self)
        self.water_level = 0.0 # start at 0 relative addition
        self.base_water = 0.0 # will be min elevation

        # Load GeoData
        self.load_data()
        
        # Populate Agents
        self.populate_civilians()
        
        self.datacollector = mesa.DataCollector(
            model_reporters={"Water_Level": "water_level", "Saved": self.count_saved}
        )
        
    def count_saved(self):
        saved = [a for a in self.schedule.agents if getattr(a, 'in_safe_zone', False)]
        return len(saved)

    def load_data(self):
        # 1. Raster Layer (Elevation)
        # Using a dummy or actual elevation.tif
        try:
            with rasterio.open("elevation.tif") as src:
                raster_layer = mg.RasterLayer.from_file(
                    "elevation.tif", cell_cls=mg.Cell, attr_name="elevation", model=self
                )
                raster_layer.name = "elevation"
                self.space.add_layer(raster_layer)
                
                # Create a Water layer of same dimensions
                water_layer = mg.RasterLayer(
                    width=raster_layer.width, 
                    height=raster_layer.height, 
                    crs=raster_layer.crs, 
                    total_bounds=raster_layer.total_bounds,
                    cell_cls=mg.Cell,
                    model=self
                )
                water_layer.name = "water"
                
                # Initialize base water to the minimum elevation
                elevations = [cell.elevation for cell in raster_layer]
                if elevations:
                    self.base_water = min(elevations)
                
                for cell, elev_cell in zip(water_layer, raster_layer):
                    cell.depth = max(0, self.base_water - elev_cell.elevation)
                    
                self.space.add_layer(water_layer)
                
        except Exception as e:
            print(f"Failed to load raster: {e}")

        # 2. Vector Layers
        
        try:
            # Load Roads
            roads_gdf = gpd.read_file("roads.geojson")
            road_creator = mg.AgentCreator(agent_class=Road, model=self)
            roads = road_creator.from_GeoDataFrame(roads_gdf)
            self.space.add_agents(roads)
            
            # Load Safe Zones
            safe_zones_gdf = gpd.read_file("safe_zones.geojson")
            safe_zone_creator = mg.AgentCreator(agent_class=SafeZone, model=self)
            self.safe_zones = safe_zone_creator.from_GeoDataFrame(safe_zones_gdf)
            self.space.add_agents(self.safe_zones)
            
            # Load Graph for routing
            G = ox.load_graphml("roads.graphml")
            self.road_graph = ox.project_graph(G, to_crs="EPSG:3857")
            self.road_nodes = list(self.road_graph.nodes(data=True)) # for random placement
            
        except Exception as e:
            print(f"Failed to load vector data: {e}")
            self.road_graph = None
            self.road_nodes = []
            self.safe_zones = []

    def populate_civilians(self):
        # Place civilians on random road nodes
        if not self.road_nodes:
            return
            
        for i in range(self.num_civilians):
            node_id, data = random.choice(self.road_nodes)
            # data typically has 'x' (lon) and 'y' (lat)
            lon = data['x']
            lat = data['y']
            pt = Point(lon, lat)
            
            # Create civilian
            civ = Civilian(model=self, geometry=pt, crs=self.space.crs)
            # Find nearest safe zone once here to set destination if possible
            civ.start_node = node_id
            self.space.add_agents(civ)
            self.schedule.add(civ)

    def step(self):
        # Increase water level
        self.water_level += 2.0  # e.g., water rises by 2 units per step
        
        # Update water grid
        if 'water' in self.space.layers and 'elevation' in self.space.layers:
            water_layer = self.space.layers['water']
            elev_layer = self.space.layers['elevation']
            current_water_height = self.base_water + self.water_level
            
            # This could be optimized, but ok for small rasters
            for w_cell, e_cell in zip(water_layer, elev_layer):
                if current_water_height > e_cell.elevation:
                    w_cell.depth = current_water_height - e_cell.elevation
                else:
                    w_cell.depth = 0.0

        # Step agents
        self.schedule.step()
        self.datacollector.collect(self)

