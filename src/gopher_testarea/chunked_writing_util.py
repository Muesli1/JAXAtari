import os
import re

import numpy as np
from typing import Tuple, Callable, Generator, List
from numpy.typing import NDArray
import glob


def create_array_chunk_writer(
        output_dir: str,
        file_prefix: str,
        chunk_size: int,
        initial_file_count: int = 0
) -> Tuple[Callable[[NDArray, NDArray], None], Callable[[], None]]:
    """
    Creates functions to efficiently write pairs of arrays to chunked npz files.

    Args:
        output_dir: Directory to save the chunked npz files
        file_prefix: Prefix for the saved files
        chunk_size: Number of array pairs to store in a single file

    Returns:
        A tuple containing:
        - A function to add a new pair of arrays
        - A function to finalize and save any remaining arrays
    """
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    first_arrays: List[NDArray] = []
    second_arrays: List[NDArray] = []
    file_count = initial_file_count

    def add_array_pair(first_array: NDArray, second_array: NDArray) -> None:
        """Add a new pair of arrays to the current chunk."""
        nonlocal first_arrays, second_arrays, file_count

        first_arrays.append(first_array)
        second_arrays.append(second_array)

        # If we've reached the chunk size, save the file
        if len(first_arrays) >= chunk_size:
            _save_chunk()

    def _save_chunk() -> None:
        """Internal function to save the current chunk."""
        nonlocal first_arrays, second_arrays, file_count

        if len(first_arrays) > 0:
            # Stack arrays and save them
            stacked_first = np.stack(first_arrays, axis=0)
            stacked_second = np.stack(second_arrays, axis=0)

            # Save as npz file
            filename = os.path.join(output_dir, f"{file_prefix}_{file_count}.npz")
            np.savez(filename, first=stacked_first, second=stacked_second)

            # Reset arrays and increment file count
            first_arrays = []
            second_arrays = []
            file_count += 1

    def finalize() -> None:
        """Save any remaining arrays and clean up."""
        _save_chunk()

    return add_array_pair, finalize


def sort_by_numbers(filename):
    # Extract major and minor numbers from filename
    match = re.search(r'_(\d+)_(\d+)\.npz$', filename)
    if match:
        major = int(match.group(1))
        minor = int(match.group(2))
        return (major, minor)
    return (0, 0)  # fallback for files that don't match pattern


def get_next_free_run_id(
        input_dir: str,
        file_prefix: str
):
    pattern = os.path.join(input_dir, f"{file_prefix}_*.npz")

    def get_run_id(filename):
        return sort_by_numbers(filename)[0]

    files = glob.glob(pattern)
    if len(files) == 0:
        return 0

    return max([get_run_id(x) for x in files]) + 1


def load_array_pairs(
        input_dir: str,
        file_prefix: str
) -> Generator[Tuple[NDArray, NDArray, bool], None, None]:
    """
    Generator that loads and yields pairs of arrays from chunked npz files.

    Args:
        input_dir: Directory containing the chunked npz files
        file_prefix: Prefix of the files to load

    Yields:
        Tuples containing (first_array, second_array, new_run) triples
    """
    # Find all matching files
    pattern = os.path.join(input_dir, f"{file_prefix}_*.npz")
    files = sorted(glob.glob(pattern), key=sort_by_numbers)

    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")

    current_run_id = -1

    # Process each file
    for file_path in files:
        run_id = sort_by_numbers(file_path)[0]

        # Load the npz file
        with np.load(file_path) as data:
            first_arrays = data['first']
            second_arrays = data['second']

            # Yield each pair of arrays
            for i in range(len(first_arrays)):
                yield first_arrays[i], second_arrays[i], run_id != current_run_id
                current_run_id = run_id
