from byte_util import roll_left_with_carry, adc_with_carry, exclusive_or


def test_random(carry, ram: list[int]):
    random = 0

    x = ram[random + 1]
    y = ram[random]

    ram[random], carry = roll_left_with_carry(ram[random], carry)
    ram[random + 1], carry = roll_left_with_carry(ram[random + 1], carry)

    a = ram[random]
    a, carry = adc_with_carry(a, 195, carry)
    ram[random] = a

    a = y
    a = exclusive_or(a, ram[random])
    ram[random] = a

    a = x
    a = exclusive_or(a, ram[random + 1])
    ram[random + 1] = a


def binary_permutations_up_to_length(max_length):
    """
    Generate all binary permutations up to max_length in order of increasing length.
    For each length, permutations are generated in lexicographic order.
    """
    # Start with empty list for length 0 (optional, you can remove this line if you don't want it)
    # yield []

    # For each length from 1 to max_length
    for length in range(1, max_length + 1):
        # Generate all binary permutations of current length
        for num in range(2 ** length):
            # Convert number to binary and remove '0b' prefix
            binary = bin(num)[2:]
            # Pad with leading zeros if necessary
            binary = binary.zfill(length)
            # Convert string to list of integers
            yield [int(bit) for bit in binary]


def test():
    #  101 (0b01100101)
    #  128 (0b10000000)
    # expected = [101, 128]
    expected = [128, 17]
    #
    # while True:
    #

    # max_length = 20
    # for perm in binary_permutations_up_to_length(max_length):
    #     ram = [0, 0]
    #     for i in range(len(perm)):
    #         test_random(perm[i], ram)
    #
    #     if ram == expected:
    #         print("yay", perm)

    max_length = 2000
    for u in range(max_length):
        perm = [0] * u
        ram = [0, 0]
        for i in range(len(perm)):
            test_random(perm[i], ram)

        if ram == expected:
            print("yay", u)


if __name__ == '__main__':
    test()
