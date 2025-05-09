import re
from pathlib import Path

from ale_py import roms


def find_byte_sequence_offsets(rom_file_path: Path, byte_sequence):
    """
    Find all occurrences of a byte sequence in a binary ROM file.

    Args:
        rom_file_path (Path): Path to the ROM (.bin) file
        byte_sequence (list or bytes): The sequence of bytes to find
            e.g., [0x3E, 0x3E, 0x07, 0x2F] or bytes([0x3E, 0x3E, 0x07, 0x2F])

    Returns:
        list: List of offsets where the byte sequence was found
    """
    # Convert input to bytes if it's a list
    if isinstance(byte_sequence, list):
        byte_sequence = bytes(byte_sequence)

    # Read the ROM file as binary
    with open(rom_file_path, 'rb') as file:
        rom_data = file.read()

    # Find all occurrences
    offsets = []
    pos = 0

    while True:
        pos = rom_data.find(byte_sequence, pos)
        if pos == -1:  # No more matches
            break
        offsets.append(pos)
        pos += 1  # Move past the current match to find the next

    return offsets


def find_single_byte_sequence(bytes: list[int], rom_name: str = "gopher") -> int:
    rom_path = roms.get_rom_path(rom_name)
    assert rom_path is not None, "Could not find ROM!"

    # Find all occurrences
    offsets = find_byte_sequence_offsets(rom_path, bytes)

    if len(offsets) != 1:
        print(f"Found {len(offsets)} occurrences of the byte sequence:")
        for offset in offsets:
            print(
                f"Offset: {offset}, 0x{offset:04X}.  Upper: 0x{(offset & 0xFF00) >> 8:02X}, Lower: 0x{offset & 0x00FF:02X}")

        assert False, "There should only be one byte sequence!"

    return offsets[0]


def parse_rhs_lhs(expression: str, separator: str, variable_map: dict[str, int]):
    lhs, rhs = [x.strip() for x in expression.split(separator, maxsplit=2)]
    return parse_assembly_byte_expression(lhs, variable_map), parse_assembly_byte_expression(rhs, variable_map)


def parse_assembly_byte_expression(expression: str, variable_map: dict[str, int]):
    assert "(" not in expression, f"Can not handle complex expression like '{expression}'"

    if expression.startswith("$"):
        # hexadecimal
        assert len(expression) == 3, f"Unexpected hexadecimal number literal: '{expression}'"
        return int(expression[1:], 16)
    elif expression.startswith("%"):
        # bit literal
        assert expression[1:].isdigit(), f"Unexpected bit number literal: '{expression}'"
        return int(expression[1:], 2)
    elif expression.isdigit():
        # decimal
        # assert expression.isdigit(), f"Unexpected decimal number literal: '{expression}'"
        return int(expression, 10)
    else:
        n_plus = expression.count("+")
        n_minus = expression.count("-")
        n_or = expression.count("|")
        n_total = n_plus + n_minus + n_or

        assert n_total <= 1, f"Can not handle complex expression like '{expression}'"

        if n_total == 0:
            if "<<" in expression:
                # shift
                lhs, rhs = parse_rhs_lhs(expression, "<<", variable_map)
                return (lhs << rhs) & 0xFF
            if ">>" in expression:
                # shift
                lhs, rhs = parse_rhs_lhs(expression, ">>", variable_map)
                return (lhs >> rhs) & 0xFF

            # Is direct variable
            variable_name = expression
            assert variable_name in variable_map, f"Missing variable '{variable_name}' definition."

            return variable_map[variable_name]

        if n_plus > 0:
            lhs, rhs = parse_rhs_lhs(expression, "+", variable_map)
            return lhs + rhs
        if n_minus > 0:
            lhs, rhs = parse_rhs_lhs(expression, "-", variable_map)
            return lhs - rhs

        assert n_or > 0, f"Unexpected expression: '{expression}'"
        lhs, rhs = parse_rhs_lhs(expression, "|", variable_map)
        return (lhs | rhs) & 0xFF


def parse_assembly(file_name):
    with open(file_name, "r") as file:
        lines: list[str] = file.readlines()

    # Clean lines: strip (to get rid of new lines and tabs), replace multiple spaces with single space,
    # remove comments, and strip again (after removing comments)
    regex = re.compile("\s+")
    lines = [regex.sub(" ", line.strip()).split(";", maxsplit=2)[0].strip() for line in lines]
    # Filter out empty lines
    lines = [line for line in lines if len(line) > 0]

    variable_map: dict[str, int] = {}

    total_byte_values: list[int] = []
    label_offsets: dict[str, int] = {}

    for line in lines:
        if line.startswith(".byte "):
            # parse byte data
            line = line[len(".byte "):]

            if "," in line:
                all_byte_expressions = [x.strip() for x in line.split(",")]
            else:
                all_byte_expressions = [line.strip()]

            all_byte_values = [parse_assembly_byte_expression(x, variable_map) for x in all_byte_expressions]

            total_byte_values.extend(all_byte_values)
        elif "=" in line:
            # parse variable declaration
            variable_name, variable_expression = [x.strip() for x in line.split("=", maxsplit=2)]
            byte_value = parse_assembly_byte_expression(variable_expression, variable_map)
            # print(f"'{variable_name}' = 0x{byte_value:02X}")
            variable_map[variable_name] = byte_value
            pass
        elif line.startswith("BOUNDARY"):
            boundary_value = int(line[len("BOUNDARY"):].strip(), 10)
            assert boundary_value == 0, "Can not handle boundary values other than zero!"
        else:
            # label
            label_name = line
            # print("Label:", label_name)
            assert label_name not in label_offsets, f"Duplicated label: '{label_name}'"
            label_offsets[label_name] = len(total_byte_values)

    return total_byte_values, label_offsets


def print_label_memory_positions(global_offset: int, label_offsets: dict[str, int], rom_memory_offset: int = 0xF000):
    for (label_name, label_offset) in label_offsets.items():
        memory_position = global_offset + label_offset

        assert 0x0000 <= memory_position <= 0x0FFF, f"Invalid memory position: 0x{memory_position:X}"
        memory_position += rom_memory_offset

        print(f"__{label_name} = 0x{memory_position:04X}")
        print(f"__{label_name}_LOW = 0x{memory_position & 0x00FF:02X}")
        print(f"__{label_name}_HIGH = 0x{(memory_position & 0xFF00) >> 8:02X}")


if __name__ == "__main__":
    byte_sequence, label_offsets = parse_assembly("memory_addresses.txt")
    offset = find_single_byte_sequence(byte_sequence)
    print_label_memory_positions(offset, label_offsets)
