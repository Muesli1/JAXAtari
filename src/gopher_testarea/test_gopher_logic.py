from src.gopher_testarea.chunked_writing_util import load_array_pairs
from src.gopher_testarea.gopher_logic import reset_game, print_field, ram, gameState, translate_action, do_tick, \
    compare_ram_states_with_log, carrotPattern, get_score_number


def test_gopher_logic(name: str):
    reset_game()
    print_field(ram)

    prev_game_state = ram[gameState]

    highscore = 0

    i = 0
    for expected_ram_state, action_array in load_array_pairs("ram_states/runs/" + name, "ram"):
        action = action_array.item()

        # for i in range(20_000):
        global _debug_frame_number
        _debug_frame_number = i + 1

        # action = np.load(f"ram_states/runs/random/random_{i + 1:03}_action.npy").item()

        translate_action(action)

        do_tick()

        if ram[gameState] != prev_game_state:
            # print(f"{i + 1}:", "Advanced game state to", ram[gameState])
            prev_game_state = ram[gameState]

        # expected_ram_state = np.load(f"ram_states/runs/random/random_{i + 1:03}.npy")
        # print(f"Comparing state {i + 1}...")
        compare_ram_states_with_log(expected_ram_state.tolist(), f"State {i + 1}")

        if ram[carrotPattern] == 0:
            print("Reset game after frame", i + 1, f"(Score was {get_score_number()})")
            highscore = max(highscore, get_score_number())
            reset_game(verbose=False)

        i += 1

    # do_tick()

    print(f"DONE! All {i} frames were correct! Highscore:", highscore)


if __name__ == '__main__':
    test_gopher_logic("random2")