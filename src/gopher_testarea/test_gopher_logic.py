import numpy as np

from gopher_testarea.byte_util import compare_ram_states, byte_to_bcd_number
from gopher_testarea.debug_util import debug_show_game_field
from gopher_testarea.gopher_logic import get_intpt4_input, set_intpt4_input, set_swcha_input, get_swcha_input, \
    MOVE_RIGHT, set_swchb_input, set_intpt5_input, MOVE_LEFT, get_frame_log, get_ram, start, RESET_MASK, \
    get_swchb_input, WAIT_TIME_GAME_START, playerInformationValues, clear_frame_log, get_has_hit_new_frame, \
    set_has_hit_new_frame, vertical_blank, get_hit_new_frame_carry_status, current_ram_pointer, ram_name_area_mappings, \
    ram_name_additional_mappings, gameState, carrotPattern, set_debug_frame_number, gameSelection, GAME_SELECTION_MASK, \
    SELECT_MASK
from src.gopher_testarea.chunked_writing_util import load_array_pairs
from src.gopher_testarea.gopher_logic import gopherHorizPos, gopherReflectState, NO_REFLECT, gopherVertPos, \
    VERT_POS_GOPHER_UNDERGROUND, gardenDirtValues, determine_dirt_floor_index, ACTION_MASK

ignored_ram_states = [
    72,  # tmpSixDigitDisplayLoop - rendering
    93,  # fallingSeedScanline - rendering

    124, 125, 126, 127  # most likely stack, or Stella internals
]


def print_field(ram):
    gopher_target_x = ram[gopherHorizPos]
    facing_left = ram[gopherReflectState] == NO_REFLECT

    if not facing_left:
        gopher_target_x = gopher_target_x + 8
        assert gopher_target_x <= 255

    goper_pos_y = ram[gopherVertPos]

    # Digging underground
    if goper_pos_y == 0:
        gopher_target_y = 3
    elif goper_pos_y >= VERT_POS_GOPHER_UNDERGROUND + 14:
        gopher_target_y = 0
    elif goper_pos_y >= VERT_POS_GOPHER_UNDERGROUND + 7:
        gopher_target_y = 1
    else:
        gopher_target_y = 2

    debug_show_game_field(ram, gardenDirtValues, determine_dirt_floor_index, gopher_target_x, gopher_target_y)


def reset_action_input():
    # Reset action inputs (not console switches)
    set_swcha_input(0b11111111)  # nothing pressed
    set_intpt4_input(0b11111111)  # not pressed
    set_intpt5_input(0b11111111)  # not pressed


def reset_console_input():
    # Reset inputs
    set_swcha_input(0b11111111)  # nothing pressed
    set_swchb_input(0b11111111)  # default: pro difficulty, color, select and reset not pressed
    set_intpt4_input(0b11111111)  # not pressed
    set_intpt5_input(0b11111111)  # not pressed


def translate_action(action: int):
    valid_actions = [
        "NOOP",
        "FIRE",
        # Action(2), # UP
        "RIGHT",  # RIGHT
        "LEFT",  # LEFT
        # Action(10), # UPFIRE
        "RIGHTFIRE",  # RIGHTFIRE
        "LEFTFIRE"  # LEFTFIRE
    ]

    the_action = valid_actions[action]

    reset_action_input()

    # Set inputs
    if the_action == "NOOP":
        return
    if the_action == "FIRE" or the_action == "RIGHTFIRE" or the_action == "LEFTFIRE":
        set_intpt4_input(get_intpt4_input() & ~ACTION_MASK)
    if the_action == "RIGHT" or the_action == "RIGHTFIRE":
        set_swcha_input(get_swcha_input() & ~MOVE_RIGHT)
    if the_action == "LEFT" or the_action == "LEFTFIRE":
        set_swcha_input(get_swcha_input() & ~MOVE_LEFT)


def compare_ram_states_with_log(expected: list[int], name: str):
    ram = get_ram()
    if not compare_ram_states(ram, expected, name, ignored_ram_states, ram_full_name_mapping, exit_on_mismatch=False):

        frame_log = get_frame_log()
        if len(frame_log) > 0:
            print("= Log replay =")
            for line in frame_log:
                print(line)
        else:
            print("= No log available =")

        print()
        print_field(ram)
        print()
        print("= EXPECTED FIELD =")
        print()
        print_field(expected)
        print()

        exit(5)


# To match ALE stella emulated state, init sequence is:
# => 60 of NOP + 8 of RESET + x*(5 of SELECT + 1 nop) + 8 of RESET + 1 of PLAYER_A_FIRE
def reset_game(difficulty: int = 1, mode: int = 0, verbose: bool = False):
    expected_ram_after_init = np.load(f"ram_states/init/expected_ram_after_init_{difficulty}_{mode}.npy")
    expected_ram_before_start = np.load(f"ram_states/init/expected_ram_before_start_{difficulty}_{mode}.npy")
    expected_ram_after_start = np.load(f"ram_states/init/expected_ram_after_start_{difficulty}_{mode}.npy")

    reset_console_input()

    # set difficulty - in gopher actually reversed than what is usual:
    # Bit 7: Port difficulty switch player 1 (0 = amateur/B, 1 = pro/A)
    # Bit 6: Port difficulty switch player 2 (0 = amateur/B, 1 = pro/A)
    # We just set both, because ALE only supports only one player anyway
    set_swchb_input((get_swchb_input() & ~(1 << 7)) | (difficulty << 7))
    set_swchb_input((get_swchb_input() & ~(1 << 6)) | (difficulty << 6))

    def nop(frame_amount):
        for _ in range(frame_amount):
            # NOP
            do_tick()

    def reset(frame_amount):
        # press reset to go to GS_DISPLAY_GAME_SELECTION (game state 5)
        for _ in range(frame_amount):
            set_swchb_input(get_swchb_input() & ~RESET_MASK)
            do_tick()
            # release reset
            set_swchb_input(get_swchb_input() | RESET_MASK)

    def select(frame_amount):
        # press reset to go to GS_DISPLAY_GAME_SELECTION (game state 5)
        for _ in range(frame_amount):
            set_swchb_input(get_swchb_input() & ~SELECT_MASK)
            do_tick()
            # release reset
            set_swchb_input(get_swchb_input() | SELECT_MASK)

    if verbose:
        print("Starting...")
    # 1st frame (NOP)
    start()
    if verbose:
        print("Started")
    assert get_has_hit_new_frame(), "Start did not hit new_frame!"

    if verbose:
        print("Reset to game selection...")

    # Already one NOP used on start
    nop(60 - 1)

    reset(8)

    # Optional: use select button so select game mode
    while get_ram()[gameSelection] & GAME_SELECTION_MASK != mode:
        select(5)
        nop(1)

    reset(8)

    if verbose:
        print("P1 action button to start game...")
    # press left player action button
    set_intpt4_input(get_intpt4_input() & ~ACTION_MASK)
    do_tick()
    # release left player action button
    set_intpt4_input(get_intpt4_input() | ACTION_MASK)

    compare_ram_states_with_log(expected_ram_after_init, f"after_init | difficulty {difficulty}, mode {mode}")

    # compare_ram_states(ram, expected_ram_state_after_500)

    if verbose:
        print(f"Waiting for WAIT_TIME_GAME_START to run out ({255 - WAIT_TIME_GAME_START - 1} frames)...")

    # Wait till actual game starts
    for i in range(255 - WAIT_TIME_GAME_START - 1):
        do_tick()

    compare_ram_states_with_log(expected_ram_before_start, f"before_start | difficulty {difficulty}, mode {mode}")

    # Now advance to game state 7 (GS_CHECK_FARMER_MOVEMENT) - main game
    if verbose:
        print("Advance to main game")
    do_tick()

    compare_ram_states_with_log(expected_ram_after_start, f"after_start | difficulty {difficulty}, mode {mode}")


def get_score_number():
    ram = get_ram()
    top = byte_to_bcd_number(ram[playerInformationValues])
    mid = byte_to_bcd_number(ram[playerInformationValues + 1])
    low = byte_to_bcd_number(ram[playerInformationValues + 2])

    total = (top * 100 + mid) * 100 + low
    return total


def do_tick():
    clear_frame_log()
    set_has_hit_new_frame(False)
    vertical_blank(get_hit_new_frame_carry_status())
    assert get_has_hit_new_frame(), "Tick did not hit new_frame! This is a serious error!"


def create_and_print_ram_mapping():
    full_name_mapping: dict[int, str] = {}

    print("=" * 15, "RAM MAPPING", "=" * 15)
    print()
    print(current_ram_pointer, "BYTES OF RAM USED", 128 - current_ram_pointer, "BYTES FREE")
    print("RAM mapping:")
    for offset in range(current_ram_pointer):
        full_name = f"{ram_name_area_mappings[offset]}"

        additional_mappings = ram_name_additional_mappings.get(offset, [])
        if len(additional_mappings) > 0:
            full_name += " / " + " / ".join(additional_mappings)

        print(f"\t{offset:03}: {full_name}")
        full_name_mapping[offset] = full_name

    for offset in range(current_ram_pointer, 256):
        full_name_mapping[offset] = "unused"

    print()
    print("=" * 15, "RAM MAPPING", "=" * 15)
    print()

    return full_name_mapping


ram_full_name_mapping = create_and_print_ram_mapping()


def test_gopher_logic(name: str):
    ram = get_ram()

    reset_game(verbose=True)
    print_field(ram)

    prev_game_state = ram[gameState]

    highscore = 0

    num_resets = 0
    mode_table: dict[str, int] = {}

    need_reset: bool = True
    i = 0
    for expected_ram_state, info_array, new_run in load_array_pairs("ram_states/runs/" + name, "ram"):

        action = int(info_array[0])
        difficulty = int(info_array[1])
        mode = int(info_array[2])

        if new_run or need_reset:
            num_resets += 1
            table_key = f"Difficulty {difficulty} & mode {mode}"
            mode_table[table_key] = mode_table.get(table_key, 0) + 1
            reset_game(difficulty=difficulty, mode=mode)
            need_reset = False

        # for i in range(20_000):
        set_debug_frame_number(i + 1)

        # action = np.load(f"ram_states/runs/random/random_{i + 1:03}_action.npy").item()

        translate_action(action)

        do_tick()

        if ram[gameState] != prev_game_state:
            # print(f"{i + 1}:", "Advanced game state to", ram[gameState])
            prev_game_state = ram[gameState]

        # expected_ram_state = np.load(f"ram_states/runs/random/random_{i + 1:03}.npy")
        # print(f"Comparing state {i + 1}...")
        compare_ram_states_with_log(expected_ram_state.tolist(),
                                    f"State {i + 1} | difficulty {difficulty}, mode {mode}")

        if ram[carrotPattern] == 0:
            print("Game over after frame", i + 1, f"(Score was {get_score_number()})")
            need_reset = True
            highscore = max(highscore, get_score_number())

        i += 1

    print()
    print(f"DONE! All {i} frames were correct! Highscore:", highscore)
    print()
    print(f"In total reset {num_resets} times:")
    for (key, value) in mode_table.items():
        print(f"\t{key}: {value}x", )


if __name__ == '__main__':
    test_gopher_logic("human")
    test_gopher_logic("random")
