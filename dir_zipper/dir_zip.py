import os
import zipfile
from pathlib import Path
import argparse
from tqdm import tqdm

#################################
###  DIRECTORY ZIPPER TOOL    ###
## Created by: aten.dev        ##
#################################

def parse_arguments():
    """
    Parses command-line arguments for zipping subdirectories in a parent directory.

    Arguments:
      -d, --directory (Path, optional): The parent directory containing subdirectories to zip. Defaults to current directory.
      -o, --output (Path, optional): The output directory where zip files will be saved. Defaults to the parent directory.
      -v, --verbose (bool, optional): Enable verbose output.

    Returns:
      argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Zip all subdirectories in a specified parent directory.")
    parser.add_argument('-d', '--directory', type=Path, default=Path('.'), help='Parent directory containing subdirectories to zip. Defaults to current directory.')
    parser.add_argument('-o', '--output', type=Path, default=None, help='Output directory where zip files will be saved. Defaults to the parent directory.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.')
    return parser.parse_args()


def get_subdirectories(parent_dir):
    """
    Retrieves all subdirectories in the specified parent directory.

    Args:
      parent_dir (Path): The parent directory to search for subdirectories.

    Returns:
      list: A list of Path objects representing subdirectories.
    """
    return [item for item in parent_dir.iterdir() if item.is_dir()]


def count_files_in_directory(directory):
    """
    Counts all files within a directory and its subdirectories.

    Args:
      directory (Path): The directory to count files in.

    Returns:
      list: A list of tuples containing (root, file) pairs for all files found.
    """
    all_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            all_files.append((root, file))
    return all_files


def zip_directory(directory, output_path, verbose=False):
    """
    Zips a single directory to the specified output path.

    Args:
      directory (Path): The directory to zip.
      output_path (Path): The path where the zip file will be saved.
      verbose (bool, optional): If True, displays detailed progress information.

    Returns:
      bool: True if successful, False otherwise.
    """
    try:
        all_files = count_files_in_directory(directory)

        if verbose:
            print(f"  Zipping {directory.name} ({len(all_files)} files)...")

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if verbose:
                # Verbose mode with detailed progress
                for root, file in tqdm(all_files, desc=f"  {directory.name}", unit="file", leave=False):
                    file_path = Path(root) / file
                    zipf.write(file_path, file_path.relative_to(directory))
            else:
                # Non-verbose mode without file-level progress
                for root, file in all_files:
                    file_path = Path(root) / file
                    zipf.write(file_path, file_path.relative_to(directory))

        if verbose:
            print(f"  Created: {output_path.name}")

        return True
    except Exception as e:
        print(f"  Error zipping {directory.name}: {e}")
        return False


def main():
    """
    Main entry point for the directory zipper tool.

    Parses command-line arguments, validates directories, and zips all subdirectories
    in the specified parent directory. Each subdirectory becomes a separate zip file
    in the output directory.

    Steps performed:
    - Parses arguments for directory path, output directory, and verbosity.
    - Resolves and validates parent and output directories.
    - Creates output directory if it doesn't exist.
    - Iterates through all subdirectories and zips them individually.
    - Provides progress feedback based on verbosity level.
    """
    args = parse_arguments()

    # Print header
    if args.verbose:
        print("--------------------------------------------------")
        print("|          Directory Zipper Tool                 |")
        print("|             by aten.dev                        |")
        print("--------------------------------------------------")
        print()
    else:
        print("Directory Zipper Tool")
        print()

    # Resolve paths
    parent_dir = args.directory.resolve()
    output_dir = args.output.resolve() if args.output else parent_dir

    if args.verbose:
        print(f"  Parent directory: {parent_dir}")
        print(f"  Output directory: {output_dir}")
        print("--------------------------------------------------")
        print()

    # Validate parent directory
    if not parent_dir.exists():
        print(f"Error: Parent directory '{parent_dir}' does not exist.")
        return

    if not parent_dir.is_dir():
        print(f"Error: '{parent_dir}' is not a directory.")
        return

    # Create output directory if needed
    if not output_dir.exists():
        if args.verbose:
            print(f"Creating output directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

    # Get list of all subdirectories
    if args.verbose:
        print("Scanning for subdirectories...", end="")
    subdirs = get_subdirectories(parent_dir)
    if args.verbose:
        print("done.")
        print(f"  Found {len(subdirs)} subdirectories to zip")
        print()
    else:
        print(f"Found {len(subdirs)} subdirectories to zip")
        print()

    if not subdirs:
        print("No subdirectories found.")
        return

    # Zip directories
    if args.verbose:
        print("Zipping directories...")
        print("--------------------------------------------------")

    success_count = 0
    failed_count = 0

    # Progress bar for directories
    for item in tqdm(subdirs, desc="Overall progress", unit="dir", disable=args.verbose):
        zip_filename = output_dir / f"{item.name}.zip"
        if zip_directory(item, zip_filename, verbose=args.verbose):
            success_count += 1
        else:
            failed_count += 1

    # Summary
    if args.verbose:
        print("--------------------------------------------------")
    print()
    print("Zipping complete:")
    print(f"  Successfully zipped: {success_count}")
    if failed_count > 0:
        print(f"  Failed: {failed_count}")


if __name__ == "__main__":
    main()
