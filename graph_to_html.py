import pickle
import pandas as pd
import folium


GPICKLE_PATH = "Outputs/time_dependent_graph.gpickle"
GTFS_STOPS   = "Data/GTFS_20230925/stops.txt"  # must contain stop_id, stop_name, stop_lat, stop_lon
OUTPUT_HTML  = "entire_transit_network_map.html"

def seconds_to_time(sec: int) -> str:
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


if __name__ == "__main__":
    # Load the pre-built time-dependent graph
    with open(GPICKLE_PATH, "rb") as f:
        G = pickle.load(f)

    # Read full GTFS/stops.txt
    stops_df = pd.read_csv(
        GTFS_STOPS,
        dtype={"stop_id": str},
        usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"]
    )
    stops_df.columns = stops_df.columns.str.strip()

    # Build a dictionary: stop_id → (stop_name, lat, lon)
    stop_info = {
        row["stop_id"]: (row["stop_name"], row["stop_lat"], row["stop_lon"])
        for _, row in stops_df.iterrows()
    }

    # Determine map center by averaging all node coordinates in G
    lats, lons = [], []
    for node_id, data in G.nodes(data=True):
        lat = data.get("lat")
        lon = data.get("lon")
        if (lat is not None) and (lon is not None):
            lats.append(lat)
            lons.append(lon)

    if lats and lons:
        map_center = [sum(lats) / len(lats), sum(lons) / len(lons)]
    else:
        map_center = [55.6761, 12.5683]

    # Create a Folium map
    m = folium.Map(location=map_center, zoom_start=11, control_scale=True)

    # Add each stop as a blue circle marker (using the graph’s lat/lon)
    #    and label it with the stop_name (from stops.txt).
    for node_id, data in G.nodes(data=True):
        lat = data.get("lat")
        lon = data.get("lon")
        if (lat is None) or (lon is None):
            continue

        # Look up name and coordinates in stops.txt—if missing, fallback to node_id
        stop_name, stop_lat_gtfs, stop_lon_gtfs = stop_info.get(node_id, (node_id, None, None))
        popup_html = (
            f"<b>{stop_name}</b><br>"
            f"Stop ID: {node_id}<br>"
            f"Lat: {lat:.6f}, Lon: {lon:.6f}"
        )
        folium.CircleMarker(
            location=(lat, lon),
            radius=3,
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=200),
        ).add_to(m)

    # Draw every edge (transport + pedestrian) as a PolyLine
    for u, v, edata in G.edges(data=True):
        nu, nv = G.nodes[u], G.nodes[v]
        lat_u, lon_u = nu.get("lat"), nu.get("lon")
        lat_v, lon_v = nv.get("lat"), nv.get("lon")
        if None in (lat_u, lon_u, lat_v, lon_v):
            continue

        name_u = stop_info.get(u, (u, None, None))[0]
        name_v = stop_info.get(v, (v, None, None))[0]
        popup_lines = [f"<b>{name_u} → {name_v}</b><br>"]
        popup_lines.append(f"Edge type: {edata.get('edge_type','N/A')}<br>")

        # If this is a transport edge, list each (dep to arr, trip_id)
        schedule = edata.get("schedule", [])
        if schedule:
            popup_lines.append("<b>Schedules:</b><br>")
            for dep_sec, arr_sec, trip_id in schedule:
                dep_str = seconds_to_time(dep_sec)
                arr_str = seconds_to_time(arr_sec)
                popup_lines.append(f"Trip {trip_id}: {dep_str} → {arr_str}<br>")

        popup_html = "".join(popup_lines)
        folium.PolyLine(
            locations=[(lat_u, lon_u), (lat_v, lon_v)],
            color=edata.get("color", "black"),
            weight=1,
            opacity=0.5,
            popup=folium.Popup(popup_html, max_width=300),
        ).add_to(m)

    # Save the map as HTML
    m.save(OUTPUT_HTML)
    print(f"Interactive map saved to '{OUTPUT_HTML}'")
