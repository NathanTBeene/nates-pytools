import csv
import sys
import argparse
from pathlib import Path
from datetime import datetime
import difflib

#################################
###      CSV DIFFER TOOL      ###
## Created by: Nathan T. Beene ##
#################################

def parse_arguments():
    """
    Parses command-line arguments for comparing two CSV files and generating difference reports.

    Arguments:
      file1 (Path): Path to the first CSV file.
      file2 (Path): Path to the second CSV file.
      -o, --output (Path, optional): Directory to save the difference reports. Defaults to './diff_reports'.
      -m, --mode (str, optional): Type of difference report to generate. Choices are 'literal' for line-by-line comparison and 'entry' for entry-wise comparison. Defaults to 'summary'.
      -v, --verbose (bool, optional): Enable verbose output.
      -c, --count (bool, optional): Count the number of differing rows.

    Returns:
      argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Compare two CSV files and generate difference reports.")
    parser.add_argument("file1", type=Path, help="Path to the first CSV file.")
    parser.add_argument("file2", type=Path, help="Path to the second CSV file.")
    parser.add_argument("-o", "--output", type=Path, default=Path("./diff_reports"), help="Directory to save the difference reports.")
    parser.add_argument("-m", "--mode", choices=["literal", "entry"], default="summary", help="Type of difference report to generate. 'literal' for line-by-line, 'entry' for entry-wise comparison.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")
    parser.add_argument("-c", "--count", action="store_true", help="Count the number of differing rows.")
    return parser.parse_args()

def check_output_directory(output_path):
    """
    Checks if the specified output directory exists, and prompts the user to create it if it does not.
    If the user declines to create the directory, the program exits.

    Args:
      output_path (Path): The path to the output directory.

    Raises:
      SystemExit: If the output directory does not exist and the user chooses not to create it.
    """
    if not output_path.exists():
        choice = input(f"Output directory {output_path} does not exist. Create it? (y/n): ")
        if choice.lower() == 'y':
          output_path.mkdir(parents=True, exist_ok=True)
        else:
          print("Output directory creation declined. Exiting.")
          sys.exit(1)

def get_proper_output_path(base_path):
    """
    Returns an absolute output path based on the given base_path.

    If base_path is already absolute, it is returned as-is.
    Otherwise, the current working directory is joined with base_path to form an absolute path.

    Args:
      base_path (Path): The base path to be checked and converted if necessary.

    Returns:
      Path: An absolute path for output.
    """
    if base_path.is_absolute():
        return base_path
    else:
        return Path.cwd() / base_path

def read_csv(file_path):
    """
    Reads a CSV file and returns its contents as a list of rows.

    Args:
      file_path (str): The path to the CSV file to be read.

    Returns:
      list: A list of rows, where each row is represented as a list of strings.

    Raises:
      FileNotFoundError: If the specified file does not exist.
      UnicodeDecodeError: If the file cannot be decoded using UTF-8 encoding.
    """
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        return list(csv.reader(csvfile))
  
def literal_diff(file1_lines, file2_lines):
    """
    Compares two lists of lines and returns their unified diff.

    Args:
      file1_lines (list of str): Lines from the first file.
      file2_lines (list of str): Lines from the second file.

    Returns:
      list of str: The unified diff between the two lists of lines, formatted as strings.
    """
    d = difflib.unified_diff(
        file1_lines,
        file2_lines,
        fromfile='file1',
        tofile='file2',
        lineterm=''
    )
    return list(d)


def entry_diff(file1_lines, file2_lines):
    """
    Compares two lists of entries and returns a report of differences.
    Args:
      file1_lines (list): List of entries from the first file.
      file2_lines (list): List of entries from the second file.
    Returns:
      dict: A dictionary with two keys:
        - "file1_only": Entries present only in file1_lines.
        - "file2_only": Entries present only in file2_lines.
    """
    diff_report = {
        "file1_only": [],
        "file2_only": []
    }
    for entry in file1_lines:
        if entry not in file2_lines:
            diff_report["file1_only"].append(entry)

    for entry in file2_lines:
        if entry not in file1_lines:
            diff_report["file2_only"].append(entry)

    return diff_report


def generate_diff_report(diff, mode):
    """
    Generates a formatted difference report between two CSV files based on the specified mode.

    Args:
      diff (list or dict): The differences between two CSV files. If mode is "literal", this should be a list of strings.
        If mode is "entry", this should be a dictionary with keys "file1_only" and "file2_only", each containing lists of entries.
      mode (str): The report mode. Can be "literal" to output raw diff lines, or "entry" to output entries unique to each file.

    Returns:
      str: A string containing the formatted difference report.
    """
    report_lines = []
    if mode == "literal":
        report_lines.extend(diff)
    elif mode == "entry":
        report_lines.append("Entries only in file 1:")
        for entry in diff["file1_only"]:
            report_lines.append(','.join(entry))
        report_lines.append("\nEntries only in file 2:")
        for entry in diff["file2_only"]:
            report_lines.append(','.join(entry))
    return '\n'.join(report_lines)

def check_file_types(file1, file2):
    """
    Checks if the provided files have matching file types and are CSV files.

    Args:
      file1 (Path): The first file to check.
      file2 (Path): The second file to check.

    Raises:
      SystemExit: If the file types do not match or if either file is not a CSV file.
    """
    if file1.suffix != file2.suffix:
        print(f"Error: File types do not match ({file1.suffix} vs {file2.suffix})")
        sys.exit(1)
    if file1.suffix.lower() != ".csv":
        print(f"Error: Unsupported file type {file1.suffix}. Only .csv files are supported.")
        sys.exit(1)


def main():
    """
    Main entry point for the CSV differ tool.
    Parses command-line arguments, validates input files and output directory, reads CSV files,
    computes differences based on the selected mode ('literal' or 'entry'), and generates a
    difference report. Optionally prints verbose output and counts differing rows.
    Steps performed:
    - Parses arguments for file paths, output directory, mode, verbosity, and count option.
    - Validates file types and output directory.
    - Reads CSV files into memory.
    - Computes differences using either literal or entry-wise comparison.
    - Generates and saves a difference report if requested.
    - Prints summary information based on verbosity and count options.
    Exits with an error if an unknown mode is specified.
    """
    args = parse_arguments()
    if args.verbose:
        print(f"Comparing {args.file1} and {args.file2}")
    if args.count:
        print("Counting differing rows...")
    if args.mode == "literal":
        print("Generating literal difference report...")
    elif args.mode == "entry":
        print("Generating entry-wise difference report...")
    
    check_file_types(args.file1, args.file2)
    check_output_directory(get_proper_output_path(args.output))

    file1_lines = read_csv(args.file1)
    file2_lines = read_csv(args.file2)

    if args.mode == "entry":
        diff = entry_diff(file1_lines, file2_lines)
    elif args.mode == "literal" or not args.mode:
        # Default to literal diff if mode is unknown
        diff = literal_diff(file1_lines, file2_lines)
    else:
        print(f"Error: Unknown mode {args.mode}")
        sys.exit(1)

    if not diff or (args.mode == "entry" and not diff["file1_only"] and not diff["file2_only"]):
        print("No differences found.")
        return

    if args.verbose:
        print("Difference report generated.")

    if args.output:
        output_file = get_proper_output_path(args.output) / f"diff_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(generate_diff_report(diff, args.mode))
        if args.verbose:
            print(f"Difference report saved to {output_file}")

    if args.count:
        print(f"Total differing rows: {len(diff)}")

if __name__ == "__main__":
    main()