import mesa
import mesa_geo as mg
import matplotlib.pyplot as plt

from model import EvacuationModel
from agents import Civilian, Road, SafeZone

def agent_portrayal(agent):
    if isinstance(agent, Civilian):
        color = "blue" if getattr(agent, "in_safe_zone", False) else "red"
        return {
            "color": color,
            "radius": 2,
            "fillOpacity": 1.0,
            "weight": 1
        }
    elif isinstance(agent, SafeZone):
        return {
            "color": "green",
            "weight": 2,
            "fillOpacity": 0.4
        }
    elif isinstance(agent, Road):
        return {
            "color": "gray",
            "weight": 1
        }

def elevation_portrayal(cell):
    # Depending on how the new mesa-geo does it
    if hasattr(cell, 'depth') and cell.depth > 0:
        return {"color": "#0000FF", "opacity": 0.5} # Blue for water
    return {"color": "#CCCCCC", "opacity": 0.1} # Light gray for ground

map_element = mg.visualization.MapModule(
    agent_portrayal, [50, 50], 10, map_width=600, map_height=600
)

# Raster visualization is trickier, depends on mesa-geo API, this basic setup focuses on agents.

server = mesa.visualization.ModularServer(
    EvacuationModel,
    [map_element],
    "Flood Evacuation Simulator"
)

server.port = 8521

if __name__ == "__main__":
    server.launch()
