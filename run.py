import matplotlib.pyplot as plt
import geopandas as gpd
from model import EvacuationModel
import os

model = EvacuationModel()

# Run the simulation for 10 steps and save plots
os.makedirs("output", exist_ok=True)

for i in range(10):
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Plot roads
    if hasattr(model, "road_graph"):
        roads = model.space.get_agents_as_GeoDataFrame()
        roads[roads.geometry.type == 'LineString'].plot(ax=ax, color='gray', linewidth=1)
        
    # Plot safe zones
    if hasattr(model, "safe_zones"):
        safe_geom = roads[roads.geometry.type.isin(['Polygon', 'MultiPolygon'])]
        safe_geom.plot(ax=ax, color='green', alpha=0.5)

    # Plot civilians
    civilians = roads[roads.geometry.type == 'Point']
    civilians.plot(ax=ax, color='red', markersize=10)
    
    plt.title(f"Evacuation Simulation - Step {i}")
    plt.savefig(f"output/step_{i:02d}.png")
    plt.close()
    
    model.step()

print("Simulation complete. Images saved to output/")
