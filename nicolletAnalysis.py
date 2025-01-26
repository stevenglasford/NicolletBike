import os
import sys
import gpxpy
from collections import defaultdict
from gpxpy.gpx import GPXTrackPoint

# Define intersection coordinates for Nicollet Mall
INTERSECTIONS = {
    "Grant": (44.970425, -93.278200),
    "Alice": (44.972602, -93.277618),
    "12th": (44.973222, -93.277376),
    "11th": (44.974132, -93.276855),
    "10th": (44.975153, -93.276316),
    "9th": (44.976146, -93.275807),
    "8th": (44.976854, -93.275429),
    "7th": (44.977604, -93.275038),
    "6th": (44.978316, -93.274667),
    "5th": (44.978922, -93.274285),
    "4th": (44.979534, -93.273911),
    "3rd": (44.980054, -93.273598),
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


def process_gpx_file(file_path, crossings, stops):
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
                            # Correct creation of an intersection point
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


def main(directory):
    crossings = defaultdict(int)
    stops = defaultdict(int)

    gpx_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".gpx")]
    total_trips = 0

    for gpx_file in gpx_files:
        process_gpx_file(gpx_file, crossings, stops)
        total_trips += 1

    with open("nicollet_analysis.txt", "w") as report:
        report.write("Nicollet Mall Analysis:\n")
        report.write(f"Total trips on Nicollet Mall: {total_trips}\n\n")

        for direction in ["Northbound", "Southbound"]:
            report.write(f"{direction} crossings\n")
            for name in INTERSECTIONS:
                key = f"{direction[:1].lower()}{name}"
                report.write(f"{name}: {crossings[key]}\n")
            report.write("\n")

            report.write(f"{direction} stops\n")
            for name in INTERSECTIONS:
                key = f"{direction[:1].lower()}{name}"
                encounters = crossings[key]
                report.write(f"{name}: {stops[key]}\n")
                if encounters > 0:
                    percentage = (stops[key] / encounters) * 100
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
