import sys


# Use bitwise NOT with masking to keep only 8 bits
def flip_byte(byte):
    # ~ flips all bits, then we use & 0xFF to keep only the lowest 8 bits
    return (~byte) & 0xFF


def exclusive_or(a, b):
    # return (a | b) & flip_byte(a & b)
    return a ^ b


def is_negative(byte):
    return is_msb_set(byte)


def is_positive(byte):
    return not is_msb_set(byte)


# Check if left most bit (bit 7) is set.
# Useful to check if the N flag would be set
# Also called for "is_negative"
def is_msb_set(byte):
    # Create mask with 1 in the leftmost position (2^7 = 128)
    mask = 1 << 7  # or simply use 128
    return (byte & mask) != 0


def byte_increment(byte_value):
    assert 0 <= byte_value <= 255
    if byte_value == 255:
        return 0
    return byte_value + 1


def byte_decrement(byte_value):
    assert 0 <= byte_value <= 255
    if byte_value == 0:
        return 255
    return byte_value - 1


def adc(accumulator, memory_value, carry_flag=0) -> int:
    return adc_with_carry(accumulator, memory_value, carry_flag)[0]


def adc_bcd_with_carry(accumulator, memory_value, carry_flag=0) -> tuple[int, int]:
    assert 0 <= accumulator <= 255
    assert 0 <= memory_value <= 255
    assert carry_flag in (0, 1)

    # Extract BCD digits
    acc_tens = (accumulator >> 4) & 0xF
    acc_ones = accumulator & 0xF
    mem_tens = (memory_value >> 4) & 0xF
    mem_ones = memory_value & 0xF

    # Add the ones digit
    ones_result = acc_ones + mem_ones + carry_flag

    # Handle carry from ones to tens
    if ones_result > 9:
        ones_result -= 10
        tens_carry = 1
    else:
        tens_carry = 0

    # Add the tens digit
    tens_result = acc_tens + mem_tens + tens_carry

    # Handle carry out
    if tens_result > 9:
        tens_result -= 10
        new_carry = 1
    else:
        new_carry = 0

    # Combine digits back to a byte
    result = (tens_result << 4) | ones_result

    return result, new_carry


def adc_with_carry(accumulator, memory_value, carry_flag=0) -> tuple[int, int]:
    """
    Simplified ADC that only returns the new accumulator value and overflow flag
    Carry flag should normally be set to 0 using CLC before
    """
    assert 0 <= accumulator <= 255
    assert 0 <= memory_value <= 255
    assert carry_flag in (0, 1)

    # Do the addition with carry
    result = accumulator + memory_value + carry_flag

    # Calculate carry flag
    carry_flag = 1 if result > 0xFF else 0

    # Wrap to 8 bits for the final result
    result &= 0xFF

    return result, carry_flag


def sbc(accumulator, memory_value, carry_flag=1) -> int:
    return sbc_with_carry(accumulator, memory_value, carry_flag)[0]


def sbc_with_carry(accumulator, memory_value, carry_flag=1) -> tuple[int, int]:
    """
    Simplified SBC that only returns the new accumulator value and overflow flag
    Carry flag should normally be set to 1 using SEC before
    """
    assert 0 <= accumulator <= 255
    assert 0 <= memory_value <= 255
    assert carry_flag in (0, 1)

    # For SBC: A - M - ~C
    # The NOT of carry is equivalent to (1 - carry)
    result = accumulator - memory_value - (1 - carry_flag)

    # Calculate carry flag
    # Is inverted by definition for sbc, because it should represent a borrow
    # This simplifies more complex subs with multiple bytes involved
    carry_flag = 1 if result >= 0 else 0

    # Wrap to 8 bits
    result &= 0xFF

    return result, carry_flag


def roll_left_with_carry(byte_value, carry_bit):
    """
    Rolls a byte value left, taking a carry bit from the right.
    Returns a tuple containing the rolled byte value and the new carry bit.

    Args:
        byte_value: An integer in range [0, 255]
        carry_bit: Either 0 or 1

    Returns:
        (new_byte_value, new_carry_bit): Tuple containing rolled byte value and new carry bit
    """
    # Check that inputs are in valid ranges
    if not (0 <= byte_value <= 255):
        raise ValueError("byte_value must be in range [0, 255]")
    if carry_bit not in (0, 1):
        raise ValueError("carry_bit must be either 0 or 1")

    # Extract the leftmost bit (which becomes the new carry)
    new_carry_bit = (byte_value >> 7) & 1

    # Shift the byte left by 1, wrapping around at 8 bits
    # and add the input carry bit at the rightmost position
    new_byte_value = ((byte_value << 1) & 0xFF) | carry_bit

    return (new_byte_value, new_carry_bit)


def shift_right_with_carry(byte_value):
    return (byte_value >> 1), 1 if (byte_value & 0x1 != 0) else 0


def shift_left_with_carry(byte_value):
    return (byte_value << 1) & 0xFF, 1 if (byte_value & 1 << 7 != 0) else 0


# Convert byte to binary string with leading zeros
def byte_to_binary_string(byte_value):
    return f"0b{byte_value:08b}"


def byte_to_bcd_number(byte_value):
    acc_tens = (byte_value >> 4) & 0xF
    acc_ones = byte_value & 0xF
    return acc_tens * 10 + acc_ones


def bcd_number_to_byte(byte_value):
    assert 0 <= byte_value <= 99
    return ((byte_value // 10) << 4) | (byte_value % 10)


def test():
    # for x in range(256):
    #     print(byte_to_binary_string(x))
    #     result, new_carry = roll_left_with_carry(x, 1)
    #     print("=>", byte_to_binary_string(result), "&", new_carry)

    # for i in range(100):
    #     byte_value = bcd_number_to_byte(i)
    #     reverted_number = byte_to_bcd_number(byte_value)
    #     print(i, "=>", f"0x{byte_value:02X}", "=>", reverted_number)
    #
    #     assert i == reverted_number

    for i in range(100):
        byte_value = bcd_number_to_byte(i)

        for a in range(100):
            add_byte_value = bcd_number_to_byte(a)

            result, carry = adc_bcd_with_carry(byte_value, add_byte_value, 0)
            constructed_str = f"{carry}{byte_to_bcd_number(result):02}"
            constructed_number = int(constructed_str, 10)
            print(f"{i} + {a} = {constructed_str}")

            assert constructed_number == i + a


prev_ram_compare: list[int] | None = None


def compare_ram_states(current: list[int], expected: list[int],
                       info_message: str, ignored_ram_states,
                       ram_full_name_mapping,
                       show_matches: bool = False,
                       exit_on_mismatch: bool = True):
    global prev_ram_compare
    assert len(current) == len(expected), "Different ram state lengths!"

    any_mismatch = False
    for i in range(len(current)):
        if i in ignored_ram_states:
            continue

        current_value = current[i]
        expected_value = expected[i]

        if current_value != expected_value:
            any_mismatch = True

    if any_mismatch:
        print("#" * 20)

    for i in range(len(current)):
        if i in ignored_ram_states:
            continue

        current_value = current[i]
        expected_value = expected[i]

        if current_value != expected_value:
            print(
                f"RAM mismatch: {i:03} was {current_value:03} (0x{current_value:02X} = {byte_to_binary_string(current_value)}) but expected {expected_value:03} (0x{expected_value:02X} = {byte_to_binary_string(expected_value)}). name: {ram_full_name_mapping[i]}")

            if prev_ram_compare is not None:
                print(
                    f"--> prev value: {prev_ram_compare[i]:03} (0x{prev_ram_compare[i]:02X} = {byte_to_binary_string(prev_ram_compare[i])})")
            # any_mismatch = True

        elif any_mismatch and show_matches:
            print(
                f"RAM    match: {i:03} was {current_value:03} (0x{current_value:02X} = {byte_to_binary_string(current_value)}). name: {ram_full_name_mapping[i]}")

            if prev_ram_compare is not None:
                print(
                    f"--> prev value: {prev_ram_compare[i]:03} (0x{prev_ram_compare[i]:02X} = {byte_to_binary_string(prev_ram_compare[i])})")

    if any_mismatch:
        print("#" * 20)

    prev_ram_compare = current.copy()
    if any_mismatch:
        print("Failed at:", info_message)
        if exit_on_mismatch:
            sys.exit(5)
        else:
            return False

    return True


if __name__ == '__main__':
    test()
