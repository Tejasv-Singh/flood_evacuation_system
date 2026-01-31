# Flood Evacuation & Bottleneck Simulator

A customized Mesa-Geo model predicting pedestrian evacuation dynamics during sudden terrestrial flooding. Built using OpenStreetMap (OSMnx) and raster topography arrays, this project maps out realistic urban intersections and models how citizens would pathfind towards designated Safe Zones (like high-altitude multi-story buildings) based on real elevation map rising water data.

## Features
* **Real-World Topology**: Automatically fetches vector lines/polygons (roads and buildings) from OpenStreetMap using `osmnx` for any given coordinate sequence.
* **Topographical Raster Integration**: Calculates flood rising pools dynamically leveraging GeoTiff standard elevations to map exactly which routes are inundated. 
* **Autonomous GeoAgents**: Every citizen acts as a GeoAgent pathfinding locally across the EPSG:3857 projected space toward safe polygons, simulating human routing decision matrices.
* **Headless and Interactive Viz**: Capable of generating offline Matplotlib animated frame states or live-ticking within an interactive mapping application. 

## Requirements
* `mesa` (3.x)
* `mesa-geo`
* `osmnx`, `geopandas`, `rasterio`, `networkx`, `shapely`

## Execution
Run `python data_setup.py` to bake your environment's topography into `elevation.tif` and caching the `.geojson` mapping layers. 
Execute `python run.py` to begin a headless tick of the model, processing the topological updates and validating pathfinding mechanisms frame by frame.
