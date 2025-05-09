DirtMaskingBits = [
    #  PF0 bit masking values
    1 << 4, 1 << 5, 1 << 6, 1 << 7,
    # PF1 bit masking values
    1 << 7, 1 << 6, 1 << 5, 1 << 4, 1 << 3, 1 << 2, 1 << 1, 1 << 0,
    # PF2 bit masking values
    1 << 0, 1 << 1, 1 << 2, 1 << 3, 1 << 4, 1 << 5, 1 << 6, 1 << 7
]

PIXEL_BITS_PF0 = 4  # Only leftmost 4 bits used
PIXEL_BITS_PF1 = 8  # All 8 bits used
PIXEL_BITS_PF2 = 8  # All 8 bits used

# Order: left_pf0 (4 left bits), left_pf1 (8 bits), left_pf2 (8 bits)
#        right_pf0 (4 left bits), right_pf1 (8 bits), right_pf2 (8 bits, last (left) does not seem to be reachable)

LEFT_PF0_PIXEL_OFFSET = 0  # Not used in code, assumed to be zero
LEFT_PF1_PIXEL_OFFSET = LEFT_PF0_PIXEL_OFFSET + PIXEL_BITS_PF0
LEFT_PF2_PIXEL_OFFSET = LEFT_PF1_PIXEL_OFFSET + PIXEL_BITS_PF1
RIGHT_PF0_PIXEL_OFFSET = LEFT_PF2_PIXEL_OFFSET + PIXEL_BITS_PF2
RIGHT_PF1_PIXEL_OFFSET = RIGHT_PF0_PIXEL_OFFSET + PIXEL_BITS_PF0
RIGHT_PF2_PIXEL_OFFSET = RIGHT_PF1_PIXEL_OFFSET + PIXEL_BITS_PF1

offset_map = []
for i in range(PIXEL_BITS_PF0):
    offset_map.append(0)
for i in range(PIXEL_BITS_PF1):
    offset_map.append(1)
for i in range(PIXEL_BITS_PF2):
    offset_map.append(2)
for i in range(PIXEL_BITS_PF0):
    offset_map.append(3)
for i in range(PIXEL_BITS_PF1):
    offset_map.append(4)
for i in range(PIXEL_BITS_PF2):
    offset_map.append(5)

y_offset_map = [0, 6, 12, 18]


def debug_show_game_field(ram: list[int], gardenDirtValues: int,
                          determine_dirt_floor_index, gopher_target_x,
                          gopher_target_y):
    # Divide by 4
    gopher_target_x = gopher_target_x >> 2

    # Order: left_pf0 (4 left bits), left_pf1 (8 bits), left_pf2 (8 bits)
    #        right_pf0 (4 left bits), right_pf1 (8 bits), right_pf2 (8 bits, last (left) does not seem to be reachable)

    # if a >= (XMAX + 1) // 8:
    #     # Carry always 1, because compare has a >= memory
    #     a, _ = sbc_with_carry(a, (XMAX + 1) // 8, carry_flag=1)

    for y in range(4):
        y_offset = y_offset_map[y]
        for x in range(LEFT_PF0_PIXEL_OFFSET, RIGHT_PF2_PIXEL_OFFSET + PIXEL_BITS_PF2):
            byte_offset = offset_map[x]
            bit_mask = DirtMaskingBits[x % 20]

            # print(determine_dirt_floor_index(x * 4), "vs", byte_offset, x % 20)
            debug_result = determine_dirt_floor_index(x * 4)
            assert debug_result[0] == byte_offset and debug_result[1] == x % 20

            # print(f"{:08b}")
            # print(byte_offset, f"{bit_mask:08b}")

            dirt_dug = (ram[gardenDirtValues + byte_offset + y_offset] & bit_mask) != 0

            if dirt_dug:
                if gopher_target_x == x and gopher_target_y == y:
                    visual = "❌"
                elif gopher_target_y == y:
                    visual = "━"
                elif gopher_target_x == x:
                    visual = "┃"
                else:
                    visual = " "
            else:
                visual = "□"
            print(visual, end="")

        if gopher_target_y == y:
            print(" <- G", end="")
        print()

    print(" " * (gopher_target_x - 1), "┃")
    print(" " * (gopher_target_x - 1), "G")


def debug_print_dirt_masks(XMIN_GOPHER, XMAX_GOPHER, determine_dirt_floor_index, DirtMaskingBits):
    # print(LEFT_PF1_PIXEL_OFFSET, LEFT_PF2_PIXEL_OFFSET, RIGHT_PF0_PIXEL_OFFSET, RIGHT_PF1_PIXEL_OFFSET,
    #       RIGHT_PF2_PIXEL_OFFSET)

    # 4, 12, 20, 24, 32

    # XMAX_GOPHER is never reached, actually exclusive in game, because check in atari was easier
    # + 8 if dig to right
    for x in range(XMIN_GOPHER, XMAX_GOPHER + 8, 1):
        r = determine_dirt_floor_index(x)
        print(x, "->", r[0], "+ 0/6/12/18,", f"{DirtMaskingBits[r[1]]:08b}")
    pass
