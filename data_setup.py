import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.transform import from_bounds
import osmnx as ox

# Coordinates roughly for NIT Hamirpur or a hilly area in Hamirpur
CENTER = (31.7084, 76.5273)
DIST = 1000 # 1km radius

def generate_data():
    print("Downloading OSM road network...")
    # Get street network
    G = ox.graph_from_point(CENTER, dist=DIST, network_type='drive')
    
    # Reproject to projected CRS for easier distance calculations if needed, but we'll keep EPSG:4326 for simplicity
    # or EPSG:32643 (UTM zone 43N)
    
    # Convert to GeoDataFrames
    nodes, edges = ox.graph_to_gdfs(G)
    
    print("Downloading Buildings for Safe Zones...")
    try:
        # Newer osmnx
        tags = {'building': True}
        buildings = ox.features_from_point(CENTER, tags=tags, dist=DIST)
    except AttributeError:
        # Older osmnx
        tags = {'building': True}
        buildings = ox.geometries_from_point(CENTER, tags=tags, dist=DIST)

    # Filter to polygons only
    buildings = buildings[buildings.geometry.type == 'Polygon']
    
    # Pick top 5 largest buildings as safe zones
    buildings['area'] = buildings.geometry.area
    safe_zones = buildings.sort_values('area', ascending=False).head(5)
    
    # Save the data
    print("Saving Vector Data...")
    edges = edges.reset_index()
    # clean up columns containing lists which cannot be saved to GeoJSON easily
    for col in edges.columns:
        if col != 'geometry' and edges[col].apply(lambda x: isinstance(x, list)).any():
            edges[col] = edges[col].apply(lambda x: ','.join(map(str, x)) if isinstance(x, list) else x)

            
    edges.to_file('roads.geojson', driver='GeoJSON')
    print("Saving GraphML...")
    ox.save_graphml(G, 'roads.graphml')

    
    safe_zones = safe_zones.reset_index()
    for col in safe_zones.columns:
        if col != 'geometry' and safe_zones[col].apply(lambda x: isinstance(x, list)).any():
            safe_zones[col] = safe_zones[col].apply(lambda x: ','.join(map(str, x)) if isinstance(x, list) else x)
    safe_zones.to_file('safe_zones.geojson', driver='GeoJSON')
    
    print("Generating Synthetic DEM...")
    # Get bounds from the graph
    minx, miny, maxx, maxy = edges.total_bounds
    
    # Create a 100x100 raster
    width, height = 100, 100
    
    # Transform
    transform = from_bounds(minx, miny, maxx, maxy, width, height)
    
    # Create elevation values using a combination of gradients to simulate a hill
    # Let's say high elevation at (maxx, maxy) and low at (minx, miny)
    x = np.linspace(0, 1, width)
    y = np.linspace(0, 1, height)
    xv, yv = np.meshgrid(x, y)
    
    # A hill in the center right
    elevation = 500 + 200 * np.exp(-((xv - 0.8)**2 + (yv - 0.5)**2) / 0.1)
    # A slope from left to right
    elevation += 100 * xv
    # Some noise
    elevation += np.random.normal(0, 5, (height, width))
    
    elevation = np.array(elevation, dtype=np.float32)
    
    print("Saving DEM to elevation.tif")
    with rasterio.open(
        'elevation.tif',
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=elevation.dtype,
        crs='EPSG:4326',
        transform=transform,
    ) as dst:
        dst.write(elevation, 1)
        
    print("Data Generation Complete.")

if __name__ == "__main__":
    generate_data()
