def main(directory):
    gpx_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".gpx")]
    total_trips = 0

    all_crossings = defaultdict(int)
    all_stops = defaultdict(int)

    with ProcessPoolExecutor() as executor:
        results = executor.map(process_single_gpx_file, gpx_files)

    for result in results:
        if result:  # Only process valid results
            crossings, stops = result
            total_trips += 1
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

    print("Analysis complete! Report saved as 'nicollet_analysis_parallel.txt'.")