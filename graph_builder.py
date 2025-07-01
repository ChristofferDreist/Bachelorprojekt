#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
graph_builder.py

Builds a time-dependent transit graph from the **full** GTFS data:
  - GTFS_20230925/stops.txt
  - GTFS_20230925/stop_times.txt

Resulting graph includes every stop (Cityringen, buses outside Zealand, etc.),
plus transport edges and pedestrian edges within 200m.

Saves the resulting DiGraph as time_dependent_graph.gpickle.
"""

import pandas as pd
import numpy as np
import networkx as nx
import pickle
from sklearn.neighbors import BallTree
from tqdm import tqdm

GTFS_STOPS      = "Data/GTFS_20230925/stops.txt"
GTFS_STOP_TIMES = "Data/GTFS_20230925/stop_times.txt"
OUTPUT_GPICKLE  = "Outputs/time_dependent_graph.gpickle"


def parse_time_to_seconds(time_str: str) -> int:
    """
    Parse a time string 'HH:MM:SS' (possibly >24h, e.g., '25:30:00') into total seconds.
    Returns np.nan on invalid input.
    """
    try:
        parts = time_str.strip().split(":")
        if len(parts) != 3:
            return np.nan
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    except Exception:
        return np.nan


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between (lat1, lon1) and (lat2, lon2) in meters.
    """
    lat1r, lon1r, lat2r, lon2r = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1r) * np.cos(lat2r) * np.sin(dlon / 2.0) ** 2
    )
    c = 2 * np.arcsin(np.sqrt(a))
    return 6371000 * c  # Earth radius ≈ 6,371,000 m


def build_time_dependent_graph(stops_path: str, stop_times_path: str) -> nx.DiGraph:
    """
    Loads full GTFS/stops.txt + GTFS/stop_times.txt, then constructs:
      - A directed graph G where each node = stop_id, attributes: lat, lon
      - Transport edges: (u→v) with attribute 'schedule' = sorted list of (dep_sec, arr_sec, trip_id)
      - Pedestrian edges: (u→v) if stops are within 200 m, with 'weight' = walking_time_sec

    Returns:
      G (networkx.DiGraph)
    """
    # Load stops.txt
    stops_df = pd.read_csv(
        stops_path,
        dtype={"stop_id": str, "stop_lat": float, "stop_lon": float},
        usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"],
    )
    stops_df.columns = stops_df.columns.str.strip()
    # We'll only need stop_id, stop_lat, stop_lon for the graph
    stops_coords = stops_df[["stop_id", "stop_lat", "stop_lon"]].copy()

    # Load stop_times.txt (all trips)
    stop_times_df = pd.read_csv(
        stop_times_path,
        dtype={
            "trip_id": str,
            "arrival_time": str,
            "departure_time": str,
            "stop_id": str,
            "stop_sequence": int,
        },
        low_memory=False,
    )
    stop_times_df.columns = stop_times_df.columns.str.strip()

    # Parse arrival_time / departure_time into seconds
    stop_times_df["departure_sec"] = stop_times_df["departure_time"].apply(
        parse_time_to_seconds
    )
    stop_times_df["arrival_sec"] = stop_times_df["arrival_time"].apply(
        parse_time_to_seconds
    )

    # Create directed graph and add all stops as nodes (with lat, lon)
    G = nx.DiGraph()
    for _, row in tqdm(
        stops_coords.iterrows(), total=stops_coords.shape[0], desc="Adding stops as nodes"
    ):
        G.add_node(row["stop_id"], lat=row["stop_lat"], lon=row["stop_lon"])

    # Build schedule_dict: { (u,v): [ (dep_sec, arr_sec, trip_id), ... ] }
    schedule_dict: dict = {}
    grouped = stop_times_df.groupby("trip_id")
    for trip_id, group in tqdm(grouped, desc="Grouping by trip_id"):
        group_sorted = group.sort_values("stop_sequence")
        prev_row = None
        for _, row in group_sorted.iterrows():
            if prev_row is not None:
                u = prev_row["stop_id"]
                v = row["stop_id"]
                dep = prev_row["departure_sec"]
                arr = row["arrival_sec"]
                # Keep only valid segments
                if (
                    (not np.isnan(dep))
                    and (not np.isnan(arr))
                    and (arr >= dep)
                ):
                    key = (u, v)
                    schedule_dict.setdefault(key, []).append((int(dep), int(arr), trip_id))
            prev_row = row

    # Add transport edges to G, sorting their schedules by departure time
    for (u, v), events in tqdm(
        schedule_dict.items(), desc="Adding transport edges"
    ):
        events_sorted = sorted(events, key=lambda ev: ev[0])
        G.add_edge(
            u,
            v,
            schedule=events_sorted,
            edge_type="transport",
            color="blue",
        )

    # Build pedestrian (transfer) edges for stops within 200 m
    coords = np.radians(stops_coords[["stop_lat", "stop_lon"]].values)
    tree = BallTree(coords, metric="haversine")
    radius = 200.0 / 6371000.0  # 200 m in radians

    nstops = stops_coords.shape[0]
    for i in tqdm(range(nstops), desc="Adding pedestrian edges"):
        sid_i = stops_coords.iloc[i]["stop_id"]
        lat_i = stops_coords.iloc[i]["stop_lat"]
        lon_i = stops_coords.iloc[i]["stop_lon"]
        neighbors = tree.query_radius(coords[i : i + 1], r=radius)[0]
        for j in neighbors:
            if i == j:
                continue
            sid_j = stops_coords.iloc[j]["stop_id"]
            lat_j = stops_coords.iloc[j]["stop_lat"]
            lon_j = stops_coords.iloc[j]["stop_lon"]
            dist_m = haversine(lat_i, lon_i, lat_j, lon_j)
            # walking speed ≈ 1.5 m/s → time = dist_m / 1.5
            walk_time_sec = dist_m / 1.5
            G.add_edge(
                sid_i,
                sid_j,
                weight=walk_time_sec,
                edge_type="pedestrian",
                color="green",
            )

    return G


if __name__ == "__main__":
    print("Building time-dependent transport graph (FULL GTFS)...")
    G = build_time_dependent_graph(GTFS_STOPS, GTFS_STOP_TIMES)

    print(f"Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    print(f"Saving graph to '{OUTPUT_GPICKLE}' ...")
    with open(OUTPUT_GPICKLE, "wb") as f:
        pickle.dump(G, f)
    print("Done.")
