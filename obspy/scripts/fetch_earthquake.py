#!/usr/bin/env python3
"""
Fetch waveforms for an earthquake event.

Usage:
    python fetch_earthquake.py --event-id us7000jk6z
    python fetch_earthquake.py --lat 37.8 --lon -122.4 --time "2023-01-01T00:00:00" --mag 4.5
    python fetch_earthquake.py --event-id us7000jk6z --stations "IU.ANMO,IU.HRV" --output data/
"""

import argparse
from pathlib import Path

from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import FDSNNoDataException
from obspy.geodetics import locations2degrees


def fetch_earthquake_waveforms(
    event_id: str = None,
    latitude: float = None,
    longitude: float = None,
    origin_time: str = None,
    magnitude: float = None,
    stations: list = None,
    networks: str = "IU,II",
    channels: str = "BHZ",
    min_radius: float = 30.0,
    max_radius: float = 90.0,
    before_p: float = 60.0,
    after_p: float = 600.0,
    output_dir: str = ".",
    client_name: str = "IRIS",
) -> list:
    """
    Fetch waveforms for an earthquake.

    Args:
        event_id: USGS event ID (e.g., 'us7000jk6z')
        latitude: Event latitude (if no event_id)
        longitude: Event longitude (if no event_id)
        origin_time: Event origin time (if no event_id)
        magnitude: Event magnitude for filename (if no event_id)
        stations: List of specific stations (e.g., ['IU.ANMO', 'IU.HRV'])
        networks: Comma-separated network codes
        channels: Comma-separated channel codes
        min_radius: Minimum distance in degrees
        max_radius: Maximum distance in degrees
        before_p: Seconds before P arrival to fetch
        after_p: Seconds after P arrival to fetch
        output_dir: Directory for output files
        client_name: FDSN client name

    Returns:
        List of output file paths
    """
    waveform_client = Client(client_name)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    output_files = []

    # Get event information
    if event_id:
        print(f"Fetching event: {event_id}")
        event_client = Client("USGS")
        cat = event_client.get_events(eventid=event_id)
        event = cat[0]
        origin = event.origins[0]
        latitude = origin.latitude
        longitude = origin.longitude
        origin_time = origin.time
        magnitude = event.magnitudes[0].mag if event.magnitudes else 0.0
        print(f"Event: M{magnitude:.1f} at {latitude:.2f}, {longitude:.2f}")
        print(f"Time: {origin_time}")
    else:
        origin_time = UTCDateTime(origin_time)
        print(f"Using provided location: {latitude:.2f}, {longitude:.2f}")
        print(f"Time: {origin_time}")

    # Get stations
    if stations:
        station_list = []
        for s in stations:
            parts = s.split(".")
            if len(parts) >= 2:
                station_list.append((parts[0], parts[1]))
            else:
                station_list.append(("*", parts[0]))
    else:
        print(f"Searching for stations {min_radius}-{max_radius} degrees away...")
        inv = waveform_client.get_stations(
            starttime=origin_time,
            endtime=origin_time + 1,
            network=networks,
            channel=channels.split(",")[0],
            latitude=latitude,
            longitude=longitude,
            minradius=min_radius,
            maxradius=max_radius,
            level="station",
        )
        station_list = [
            (net.code, sta.code)
            for net in inv
            for sta in net
        ]
        print(f"Found {len(station_list)} stations")

    # Fetch waveforms for each station
    for network, station in station_list:
        try:
            # Calculate approximate P arrival time using distance
            inv = waveform_client.get_stations(
                network=network,
                station=station,
                starttime=origin_time,
                level="station",
            )
            if not inv or not inv[0]:
                print(f"  {network}.{station}: No station metadata")
                continue

            sta_lat = inv[0][0].latitude
            sta_lon = inv[0][0].longitude
            distance_deg = locations2degrees(latitude, longitude, sta_lat, sta_lon)

            # Approximate P travel time (very rough: 10 deg ~= 100s)
            approx_p_time = origin_time + distance_deg * 10

            t1 = approx_p_time - before_p
            t2 = approx_p_time + after_p

            print(f"  Fetching {network}.{station} (dist={distance_deg:.1f} deg)...")

            st = waveform_client.get_waveforms(
                network=network,
                station=station,
                location="*",
                channel=channels,
                starttime=t1,
                endtime=t2,
            )

            if len(st) == 0:
                print(f"    No data available")
                continue

            # Save to file
            mag_str = f"M{magnitude:.1f}" if magnitude else "Munk"
            filename = f"{event_id or 'event'}_{mag_str}_{network}.{station}.mseed"
            filepath = output_path / filename
            st.write(str(filepath), format="MSEED")
            output_files.append(str(filepath))
            print(f"    Saved: {filepath}")

        except FDSNNoDataException:
            print(f"    No data available")
        except Exception as e:
            print(f"    Error: {e}")

    print(f"\nDownloaded {len(output_files)} files to {output_path}")
    return output_files


def main():
    parser = argparse.ArgumentParser(
        description="Fetch waveforms for an earthquake event"
    )

    # Event specification
    event_group = parser.add_argument_group("Event specification")
    event_group.add_argument(
        "--event-id", "-e", help="USGS event ID (e.g., us7000jk6z)"
    )
    event_group.add_argument("--lat", type=float, help="Event latitude")
    event_group.add_argument("--lon", type=float, help="Event longitude")
    event_group.add_argument("--time", "-t", help="Origin time (ISO format)")
    event_group.add_argument("--mag", type=float, help="Magnitude (for filename)")

    # Station selection
    station_group = parser.add_argument_group("Station selection")
    station_group.add_argument(
        "--stations", "-s", help="Specific stations (comma-separated, e.g., IU.ANMO,IU.HRV)"
    )
    station_group.add_argument(
        "--networks", "-n", default="IU,II", help="Network codes (default: IU,II)"
    )
    station_group.add_argument(
        "--channels", "-c", default="BHZ", help="Channel codes (default: BHZ)"
    )
    station_group.add_argument(
        "--min-radius", type=float, default=30.0, help="Min distance in degrees (default: 30)"
    )
    station_group.add_argument(
        "--max-radius", type=float, default=90.0, help="Max distance in degrees (default: 90)"
    )

    # Time window
    time_group = parser.add_argument_group("Time window")
    time_group.add_argument(
        "--before-p", type=float, default=60.0, help="Seconds before P (default: 60)"
    )
    time_group.add_argument(
        "--after-p", type=float, default=600.0, help="Seconds after P (default: 600)"
    )

    # Output
    parser.add_argument(
        "--output", "-o", default=".", help="Output directory (default: current)"
    )
    parser.add_argument(
        "--client", default="IRIS", help="FDSN client (default: IRIS)"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.event_id and not (args.lat and args.lon and args.time):
        parser.error("Either --event-id or (--lat, --lon, --time) required")

    stations = args.stations.split(",") if args.stations else None

    fetch_earthquake_waveforms(
        event_id=args.event_id,
        latitude=args.lat,
        longitude=args.lon,
        origin_time=args.time,
        magnitude=args.mag,
        stations=stations,
        networks=args.networks,
        channels=args.channels,
        min_radius=args.min_radius,
        max_radius=args.max_radius,
        before_p=args.before_p,
        after_p=args.after_p,
        output_dir=args.output,
        client_name=args.client,
    )


if __name__ == "__main__":
    main()
