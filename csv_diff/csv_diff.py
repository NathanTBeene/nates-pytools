import csv
import sys
import argparse
from pathlib import Path
from datetime import datetime
import difflib

#################################
###      CSV DIFFER TOOL      ###
## Created by: aten.dev        ##
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


def literal_diff(file1_lines, file2_lines, file1_path, file2_path):
  """
  Performs a line-by-line (literal) diff between two CSV files using difflib.

  Args:
    file1_lines (list): List of rows from the first CSV file.
    file2_lines (list): List of rows from the second CSV file.
    file1_path (Path): Path to the first CSV file.
    file2_path (Path): Path to the second CSV file.

  Returns:
    list: List of strings representing the unified diff output.
  """

  # Convert CSV rows to strings for difflib
  file1_strings = [','.join(row) for row in file1_lines]
  file2_strings = [','.join(row) for row in file2_lines]

  # Get file modification times
  file1_time = datetime.fromtimestamp(file1_path.stat().st_mtime).isoformat()
  file2_time = datetime.fromtimestamp(file2_path.stat().st_mtime).isoformat()

  diff = difflib.unified_diff(
    file1_strings,
    file2_strings,
    fromfile=f"a/{file1_path.name}\t{file1_time}",
    tofile=f"b/{file2_path.name}\t{file2_time}",
    lineterm='',
    n=3  # context lines
  )
  return list(diff)


def entry_diff(file1_lines, file2_lines, file1_path, file2_path):
  """
  Performs an entry-wise diff between two CSV files, returning unique and common rows with statistics.

  Args:
    file1_lines (list): List of rows from the first CSV file.
    file2_lines (list): List of rows from the second CSV file.
    file1_path (Path): Path to the first CSV file.
    file2_path (Path): Path to the second CSV file.

  Returns:
    dict: Contains lists of unique and common rows, and statistics.
  """
  file1_set = set(tuple(row) for row in file1_lines)
  file2_set = set(tuple(row) for row in file2_lines)

  only_in_file1 = file1_set - file2_set
  only_in_file2 = file2_set - file1_set
  common = file1_set & file2_set

  return {
    "file1_only": [list(row) for row in sorted(only_in_file1)],
    "file2_only": [list(row) for row in sorted(only_in_file2)],
    "common": [list(row) for row in sorted(common)],
    "stats": {
      "file1_total": len(file1_lines),
      "file2_total": len(file2_lines),
      "common_count": len(common),
      "file1_unique": len(only_in_file1),
      "file2_unique": len(only_in_file2)
    }
  }


def generate_diff_report(diff, mode, file1_path, file2_path):
  """
  Generates a formatted report summarizing the differences between two CSV files.
  Args:
    diff (dict or list): The difference data between the two CSV files.
      - If mode is "literal", this should be a list of string differences.
      - If mode is "entry", this should be a dictionary containing:
        - "stats": dict with statistics about the comparison.
        - "file1_only": list of rows unique to file1.
        - "file2_only": list of rows unique to file2.
    mode (str): The report mode, either "literal" for line-by-line differences or "entry" for row-based comparison.
    file1_path (Path): Path object for the first CSV file.
    file2_path (Path): Path object for the second CSV file.
  Returns:
    str: A multi-line string containing the formatted diff report.
  """
  timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  report_lines = []

  # Add header
  report_lines.extend([
    "CSV Diff Report",
    f"Generated: {timestamp}",
    "Tool: CSV Differ by Nathan T. Beene",
    "=" * 60,
    f"File A: {file1_path.absolute()}",
    f"File B: {file2_path.absolute()}",
    "=" * 60,
    ""
  ])

  if mode == "literal":
    if not diff:
      report_lines.append("No differences found.")
    else:
      report_lines.extend(diff)

  elif mode == "entry":
    stats = diff.get("stats", {})

    # Add statistics section
    report_lines.extend([
      "STATISTICS:",
      f"  File A total rows: {stats.get('file1_total', 0)}",
      f"  File B total rows: {stats.get('file2_total', 0)}",
      f"  Common rows: {stats.get('common_count', 0)}",
      f"  Unique to File A: {stats.get('file1_unique', 0)}",
      f"  Unique to File B: {stats.get('file2_unique', 0)}",
      "",
      "-" * 60,
      ""
    ])

    # Rows only in File A
    if diff["file1_only"]:
      report_lines.extend([
        f"ROWS ONLY IN FILE A ({len(diff['file1_only'])} rows):",
        "-" * 40
      ])
      for i, entry in enumerate(diff["file1_only"], 1):
        report_lines.append(f"- [{i:4d}] {', '.join(str(cell) for cell in entry)}")
      report_lines.append("")

    # Rows only in File B
    if diff["file2_only"]:
      report_lines.extend([
        f"ROWS ONLY IN FILE B ({len(diff['file2_only'])} rows):",
        "-" * 40
      ])
      for i, entry in enumerate(diff["file2_only"], 1):
        report_lines.append(f"+ [{i:4d}] {', '.join(str(cell) for cell in entry)}")
      report_lines.append("")

    if not diff["file1_only"] and not diff["file2_only"]:
      report_lines.append("No differences found - files are identical.")

  return "\n".join(report_lines)

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

    # Print header
    if args.verbose:
        print("---------------------------------------------------")
        print("|               CSV Differ Tool                   |")
        print("|             by aten.dev                         |")
        print("---------------------------------------------------")
        print(f"  Mode: {args.mode}")
        print(f"    - File A: {args.file1.absolute()}")
        print(f"    - File B: {args.file2.absolute()}")
        print()
        print(f"  Output directory: {get_proper_output_path(args.output).absolute()}")
        print("--------------------------------------------------")
    else:
        print("CSV Differ Tool")
        print(f"Comparing files using {args.mode} mode")
        print()

    # Validate files
    if args.verbose:
        print("Validating file types...", end="")
    check_file_types(args.file1, args.file2)
    if args.verbose:
        print("done.")
        print()

    # Read CSV files
    if args.verbose:
        print("Reading CSV files...", end="")
    file1_lines = read_csv(args.file1)
    file2_lines = read_csv(args.file2)
    if args.verbose:
        print("done.")
        print(f"  - File A: {len(file1_lines)} rows")
        print(f"  - File B: {len(file2_lines)} rows")
        print()

    # Perform comparison
    if args.verbose:
        print("Analyzing differences...", end="")
    else:
        print("Analyzing differences...")

    if args.mode == "entry":
        diff = entry_diff(file1_lines, file2_lines, args.file1, args.file2)
    elif args.mode == "literal" or not args.mode:
        # Default to literal diff if mode is unknown
        diff = literal_diff(file1_lines, file2_lines, args.file1, args.file2)
    else:
        print(f"Error: Unknown mode {args.mode}")
        sys.exit(1)

    if args.verbose:
        print("done.")
        print("--------------------------------------------------")

    # Check for differences and provide summary
    if not diff or (args.mode == "entry" and not diff["file1_only"] and not diff["file2_only"]):
        print("Analysis complete:")
        print("  No differences found - files are identical.")
        return

    # Report findings
    if args.mode == "entry":
        stats = diff.get("stats", {})
        print("Analysis complete:")
        print(f"  Common rows: {stats.get('common_count', 0)}")
        print(f"  Unique to File A: {stats.get('file1_unique', 0)}")
        print(f"  Unique to File B: {stats.get('file2_unique', 0)}")

        if args.verbose:
            if diff["file1_only"]:
                print(f"  Examples from File A only:")
                for i, row in enumerate(diff["file1_only"][:3], 1):
                    row_text = ", ".join(str(cell) for cell in row)
                    if len(row_text) > 150:
                        row_text = row_text[:150] + "..."
                    print(f"    {i}. {row_text}")
                if len(diff["file1_only"]) > 3:
                    print(f"    ... and {len(diff['file1_only']) - 3} more")

            if diff["file2_only"]:
                print(f"  Examples from File B only:")
                for i, row in enumerate(diff["file2_only"][:3], 1):
                    row_text = ", ".join(str(cell) for cell in row)
                    if len(row_text) > 150:
                        row_text = row_text[:150] + "..."
                    print(f"    {i}. {row_text}")
                if len(diff["file2_only"]) > 3:
                    print(f"    ... and {len(diff['file2_only']) - 3} more")
    else:
        # Literal mode
        diff_count = len([line for line in diff if line.startswith('+') or line.startswith('-')])
        print(f"Analysis complete: {diff_count} lines differ")

        if args.verbose and diff:
            print("  Sample differences:")
            shown = 0
            for line in diff:
                if (line.startswith('+') or line.startswith('-')) and shown < 5:
                    print(f"    {line[:100]}{'...' if len(line) > 100 else ''}")
                    shown += 1
                if shown >= 5:
                    remaining = sum(1 for l in diff if l.startswith('+') or l.startswith('-')) - 5
                    if remaining > 0:
                        print(f"    ... and {remaining} more differences")
                    break

    if args.verbose:
        print("--------------------------------------------------")

    # Generate and save report
    if args.verbose:
        print("Generating detailed report...")

    check_output_directory(get_proper_output_path(args.output))

    if args.output:
        output_file = get_proper_output_path(args.output) / f"diff_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.diff"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(generate_diff_report(diff, args.mode, args.file1, args.file2))
        if args.verbose:
            print(f"  Report saved: {output_file.name}")
        else:
            print(f"Report saved: {output_file.name}")

    if args.count:
        if args.mode == "entry":
            stats = diff.get("stats", {})
            total_diff = stats.get('file1_unique', 0) + stats.get('file2_unique', 0)
            print(f"Total differing rows: {total_diff}")
        else:
            diff_lines = len([line for line in diff if line.startswith('+') or line.startswith('-')])
            print(f"Total differing lines: {diff_lines}")

if __name__ == "__main__":
    main()
