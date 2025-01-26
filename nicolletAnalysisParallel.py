import os
import sys
import gpxpy
from collections import defaultdict
from gpxpy.gpx import GPXTrackPoint
from concurrent.futures import ProcessPoolExecutor

# Define intersection coordinates for Nicollet Mall
INTERSECTIONS = {
    "Grant": (44.96984457940192, -93.27782828061456),
    "Alice": (44.971087696744796, -93.2771307527152),
    "12th": (44.97206449872532, -93.2763925937118),
    "11th": (44.97302003086831, -93.2755743764374),
    "10th": (44.97400819379613, -93.27469226306776),
    "9th": (44.97498001689411, -93.27388469430696),
    "8th": (44.97593926839807, -93.2730647013333),
    "7th": (44.97690729249169, -93.27223583407618),
    "6th": (44.97787529945887, -93.27143714011615),
    "5th": (44.97878804988212, -93.27067749315873),
    "4th": (44.97979620072043, -93.26981490265726),
    "3rd": (44.98078048165179, -93.26902863259868),
}

STOP_THRESHOLD = 5  # Speed (km/h) considered as a stop


def is_on_nicollet(lat, lon):
    # Define bounding box for Nicollet Mall
    nicollet_lat_range = (44.970, 44.980)
    nicollet_lon_range = (-93.278, -93.273)
    return nicollet_lat_range[0] <= lat <= nicollet_lat_range[1] and nicollet_lon_range[0] <= lon <= nicollet_lon_range[1]


def calculate_speed(point1, point2):
    distance = point1.distance_2d(point2)  # in meters
    time_diff = (point2.time - point1.time).total_seconds()  # in seconds
    if time_diff > 0:
        return (distance / time_diff) * 3.6  # Convert m/s to km/h
    return float('inf')


def get_direction(last_intersection, current_intersection):
    return "Northbound" if INTERSECTIONS[last_intersection][0] < INTERSECTIONS[current_intersection][0] else "Southbound"


def process_single_gpx_file(file_path):
    """Process a single GPX file and return its results."""
    crossings = defaultdict(int)
    stops = defaultdict(int)

    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    last_point = None
    last_intersection = None
    direction = None

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if is_on_nicollet(point.latitude, point.longitude):
                    if last_point:
                        speed = calculate_speed(last_point, point)

                        for name, coords in INTERSECTIONS.items():
                            # Create a GPXTrackPoint for intersection coordinates
                            intersection_point = GPXTrackPoint(latitude=coords[0], longitude=coords[1])
                            distance = point.distance_2d(intersection_point)
                            if distance < 30:  # 30 meters proximity to the intersection
                                if last_intersection and name != last_intersection:
                                    direction = get_direction(last_intersection, name)
                                    crossings[f"{direction[:1].lower()}{name}"] += 1
                                    if speed < STOP_THRESHOLD:
                                        stops[f"{direction[:1].lower()}{name}"] += 1
                                last_intersection = name

                    last_point = point

    return crossings, stops


def main(directory):
    gpx_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".gpx")]
    total_trips = len(gpx_files)

    all_crossings = defaultdict(int)
    all_stops = defaultdict(int)

    with ProcessPoolExecutor() as executor:
        results = executor.map(process_single_gpx_file, gpx_files)

    for crossings, stops in results:
        for key, value in crossings.items():
            all_crossings[key] += value
        for key, value in stops.items():
            all_stops[key] += value

    with open("nicollet_analysis_parallel.txt", "w") as report:
        report.write("Nicollet Mall Analysis:\n")
        report.write(f"Total trips on Nicollet Mall: {total_trips}\n\n")

        for direction in ["Northbound", "Southbound"]:
            report.write(f"{direction} crossings\n")
            for name in INTERSECTIONS:
                key = f"{direction[:1].lower()}{name}"
                report.write(f"{name}: {all_crossings[key]}\n")
            report.write("\n")

            report.write(f"{direction} stops\n")
            for name in INTERSECTIONS:
                key = f"{direction[:1].lower()}{name}"
                encounters = all_crossings[key]
                report.write(f"{name}: {all_stops[key]}\n")
                if encounters > 0:
                    percentage = (all_stops[key] / encounters) * 100
                    report.write(f"Percentage of encounters: {percentage:.2f}%\n")
                else:
                    report.write("Percentage of encounters: 0.00%\n")
            report.write("\n")

    print("Analysis complete! Report saved as 'nicollet_analysis.txt'.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python nicolletAnalysis.py <directory containing gpx files>")
        sys.exit(1)

    gpx_directory = sys.argv[1]
    if not os.path.isdir(gpx_directory):
        print(f"Error: {gpx_directory} is not a valid directory.")
        sys.exit(1)

    main(gpx_directory)
