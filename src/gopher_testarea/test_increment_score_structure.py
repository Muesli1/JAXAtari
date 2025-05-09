import numpy as np


def increment_score(a):
    # Fall through
    increment_score_submodule()


def increment_score_submodule():
    # a, carry = adc_with_carry(a, ram[currentPlayerScore + x])

    if any_value():
        done_increment_score()
        return

    if any_value():
        check_to_decrement_gopher_direction_timer()
        return

    # Fall through
    increment_next_score_value()


def increment_next_score_value():
    if any_value():
        increment_score_submodule()
        return

    # Fall through
    done_increment_score()


def done_increment_score():
    pass


def check_to_decrement_gopher_direction_timer():
    if any_value():
        check_to_launch_duck()
        return

    if any_value():
        check_to_launch_duck()
        return

    # Fall through
    check_to_launch_duck()


def check_to_launch_duck():
    if any_value():
        check_game_selection_for_duck()
        return

    if any_value():
        increment_next_score_value()
        return

    # Fall through
    check_game_selection_for_duck()


def check_game_selection_for_duck():
    if any_value():
        increment_next_score_value()
        return

    if any_value():
        increment_next_score_value()
        return

    if any_value():
        increment_next_score_value()
        return

    if any_value():
        init_duck_horizontal_position()
        return

    # Fall through
    init_duck_horizontal_position()


def init_duck_horizontal_position():
    if any_value():
        init_duck_sprite_values()
        return

    # Fall through
    init_duck_sprite_values()


def init_duck_sprite_values():
    # Jump
    increment_next_score_value()


def any_value():
    return np.random.randint(2) == 1
