import argparse
import pickle
import bisect
import heapq
import networkx as nx
import pandas as pd

GPICKLE_PATH  = "Outputs/time_dependent_graph.gpickle"
GTFS_STOPS    = "Data/GTFS_20230925/stops.txt"  # must contain stop_id, stop_name

def parse_time_to_seconds(t_str: str) -> int:
    """
    Convert "HH:MM:SS" (possibly >24h, e.g. "25:30:00") into total seconds.
    Returns None if format is invalid.
    """
    try:
        parts = t_str.strip().split(":")
        if len(parts) != 3:
            return None
        h, m, s = map(int, parts)
        return h * 3600 + m * 60 + s
    except Exception:
        return None


def seconds_to_hhmmss(sec) -> str:
    """
    Convert a numeric seconds‐value (int or float) to "HH:MM:SS".
    If sec is None or cannot be cast to int, returns "??:??:??".
    """
    if sec is None:
        return "??:??:??"
    try:
        total = int(sec)
    except Exception:
        return "??:??:??"
    if total < 0:
        return "??:??:??"
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def time_dependent_shortest_path_with_steps(
    G: nx.DiGraph,
    origin: str,
    destination: str,
    start_time: int,
    min_transfer_time: int = 180
):

    # Initialize arrival_times
    arrival_times = {node: float("inf") for node in G.nodes}
    arrival_times[origin] = start_time

    # Initial “start” step
    initial_step = {
        "stop_id": origin,
        "arrival_time": start_time,
        "mode": "start",
        "dep_time": None,
        "trip_id": None
    }

    # Min-heap: (current_arrival_time, node_id, steps_so_far)
    heap = [(start_time, origin, [initial_step])]

    while heap:
        current_time, node, steps = heapq.heappop(heap)
        if node == destination:
            return steps, current_time
        if current_time > arrival_times[node]:
            continue

        prev_step = steps[-1]
        prev_trip = prev_step.get("trip_id")
        prev_mode = prev_step.get("mode")

        for succ in G.successors(node):
            edata = G[node][succ]
            edge_type = edata.get("edge_type", "static")

            if edge_type == "transport":
                schedule = edata.get("schedule", [])
                if not schedule:
                    continue

                chosen_event = None

                # If arriving by transport, try to stay on same trip
                if (prev_mode == "transport") and (prev_trip is not None):
                    same_trip_list = [
                        ev for ev in schedule
                        if (ev[2] == prev_trip) and (ev[0] >= current_time)
                    ]
                    if same_trip_list:
                        chosen_event = same_trip_list[0]
                    else:
                        # No same-trip departure: enforce min_transfer_time
                        threshold = current_time + min_transfer_time
                        departures = [ev[0] for ev in schedule]
                        idx = bisect.bisect_left(departures, threshold)
                        if idx < len(schedule):
                            chosen_event = schedule[idx]
                else:
                    # Not already on a vehicle: board first departure ≥ current_time
                    departures = [ev[0] for ev in schedule]
                    idx = bisect.bisect_left(departures, current_time)
                    if idx < len(schedule):
                        chosen_event = schedule[idx]

                if not chosen_event:
                    continue

                dep_sec, arr_sec, trip_id = chosen_event
                new_time = arr_sec
                step_info = {
                    "stop_id": succ,
                    "arrival_time": new_time,
                    "mode": "transport",
                    "dep_time": dep_sec,
                    "trip_id": trip_id
                }

            elif edge_type == "pedestrian":
                weight = edata.get("weight", 0)
                new_time = current_time + weight
                step_info = {
                    "stop_id": succ,
                    "arrival_time": new_time,
                    "mode": "pedestrian",
                    "dep_time": None,
                    "trip_id": None
                }

            else:  # static or any other edge
                weight = edata.get("weight", 0)
                new_time = current_time + weight
                step_info = {
                    "stop_id": succ,
                    "arrival_time": new_time,
                    "mode": "static",
                    "dep_time": None,
                    "trip_id": None
                }

            # Relaxation
            if new_time < arrival_times[succ]:
                arrival_times[succ] = new_time
                new_steps = steps + [step_info]
                heapq.heappush(heap, (new_time, succ, new_steps))

    return None, None


def main():
    parser = argparse.ArgumentParser(
        description="Find earliest-arrival path between two GTFS stops."
    )
    parser.add_argument(
        "--origin",
        required=True,
        help="Origin stop_id (string)"
    )
    parser.add_argument(
        "--destination",
        required=True,
        help="Destination stop_id (string)"
    )
    parser.add_argument(
        "--start-time",
        required=True,
        help="Departure time in HH:MM:SS format"
    )
    parser.add_argument(
        "--transfer-time",
        type=int,
        default=180,
        help="Minimum transfer penalty in seconds (default=180)"
    )
    args = parser.parse_args()

    origin = args.origin
    destination = args.destination
    start_sec = parse_time_to_seconds(args.start_time)
    if start_sec is None:
        print("Error: --start-time must be HH:MM:SS")
        return

    # Load the graph
    with open(GPICKLE_PATH, "rb") as f:
        G = pickle.load(f)

    # Load full GTFS/stops.txt so we can look up stop_name
    stops_df = pd.read_csv(
        GTFS_STOPS,
        dtype={"stop_id": str},
        usecols=["stop_id", "stop_name"]
    )
    stops_df.columns = stops_df.columns.str.strip()
    stop_name_dict = stops_df.set_index("stop_id")["stop_name"].to_dict()

    # Print header
    orig_name = stop_name_dict.get(origin, origin)
    dest_name = stop_name_dict.get(destination, destination)
    print(
        f"Routing from '{orig_name}' ({origin}) to '{dest_name}' ({destination}), "
        f"departing at {seconds_to_hhmmss(start_sec)} with transfer penalty={args.transfer_time}s\n"
    )

    # Compute the path
    steps, final_arrival = time_dependent_shortest_path_with_steps(
        G,
        origin,
        destination,
        start_sec,
        min_transfer_time=args.transfer_time
    )

    if steps is None:
        print("No feasible path found.")
        return

    # Print itinerary
    prev_step = steps[0]
    prev_id   = prev_step["stop_id"]
    prev_name = stop_name_dict.get(prev_id, prev_id)
    prev_arr  = seconds_to_hhmmss(prev_step["arrival_time"])
    print(f"- Start at {prev_name} (ID={prev_id}) at {prev_arr}")

    for step in steps[1:]:
        curr_id   = step["stop_id"]
        curr_name = stop_name_dict.get(curr_id, curr_id)
        arr_str   = seconds_to_hhmmss(step.get("arrival_time"))

        if step["mode"] == "transport":
            dep_str = seconds_to_hhmmss(step.get("dep_time"))
            trip_id = step.get("trip_id", "")
            prev_name = stop_name_dict.get(prev_step["stop_id"], prev_step["stop_id"])
            print(
                f"  • At {prev_name} (ID={prev_step['stop_id']}), "
                f"take Trip {trip_id} departing {dep_str} → {curr_name} (ID={curr_id}), "
                f"arrive {arr_str}"
            )

        elif step["mode"] == "pedestrian":
            prev_name = stop_name_dict.get(prev_step["stop_id"], prev_step["stop_id"])
            print(
                f"  • Walk from {prev_name} (ID={prev_step['stop_id']}) → {curr_name} (ID={curr_id}), "
                f"arrive {arr_str}"
            )

        else:  # static or other
            prev_name = stop_name_dict.get(prev_step["stop_id"], prev_step["stop_id"])
            print(
                f"  • Move from {prev_name} (ID={prev_step['stop_id']}) → {curr_name} (ID={curr_id}), "
                f"arrive {arr_str}"
            )

        prev_step = step

    final_str = seconds_to_hhmmss(final_arrival)
    print(f"\nFinal arrival at {dest_name} (ID={destination}): {final_str}")


if __name__ == "__main__":
    main()
