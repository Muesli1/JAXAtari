# https://atariage.com/2600/programming/2600_101/docs/onestep.html
# http://www.6502.org/tutorials/6502opcodes.html#DFLAG
import sys

import numpy as np
from typing import Any
from chunked_writing_util import load_array_pairs

# https://www.randomterrain.com/atari-2600-memories-tutorial-andrew-davie-25.html

from byte_util import *
from debug_util import debug_show_game_field

# == Visual Constants (NTSC) ==

FPS = 60  # ~60 frames per second
VBLANK_TIME = 40
OVERSCAN_TIME = 31

# == Colors ==

BLACK = 0x00
WHITE = 0x0E
RED_ORANGE = 0x20
BRICK_RED = 0x30
RED = 0x40
BLUE = 0x80
OLIVE_GREEN = 0xB0
GREEN = 0xC0
LT_BROWN = 0xE0
BROWN = 0xF0

COLOR_PLAYER_1_SCORE = RED_ORANGE + 8
COLOR_PLAYER_2_SCORE = OLIVE_GREEN + 12

COLOR_FARMER_SHOES = BRICK_RED + 4
COLOR_FARMER_PANTS = BLUE + 8
COLOR_FARMER_SHIRT = GREEN + 6
COLOR_FARMER = RED + 8
COLOR_FARMER_HAT = LT_BROWN + 10
COLOR_GOPHER = BROWN
COLOR_CARROT_TOP = GREEN + 4
COLOR_GRASS_01 = OLIVE_GREEN + 10
COLOR_GRASS_02 = OLIVE_GREEN + 12
COLOR_GRASS_03 = OLIVE_GREEN + 14
COLOR_GARDEN_DIRT = RED_ORANGE + 12

# == Game constants ==

# Sprite height constants

H_FONT = 10
H_DUCK = 18
H_FARMER = 50
H_GRASS_KERNEL = 13
H_CARROT = 22
H_KERNEL_VERT_ADJUSTMENT = 41
H_UNDERGROUND_GOPHER = 12
H_GROUND_KERNEL_SECTION = 12
H_RISING_GOPHER = 36

# Frame horizontal constants

XMIN = 0
XMAX = 159

XMIN_GOPHER = XMIN + 3
XMAX_GOPHER = XMAX - 11
XMIN_DUCK = XMIN + 12
XMAX_DUCK = XMAX - 11
XMIN_FARMER = XMIN + 20
XMAX_FARMER = XMAX - 11

HORIZ_POS_HOLE_00 = 15
HORIZ_POS_HOLE_01 = 31
HORIZ_POS_HOLE_02 = 47
HORIZ_POS_HOLE_03 = 111
HORIZ_POS_HOLE_04 = 127
HORIZ_POS_HOLE_05 = 143

HORIZ_POS_CARROT_00 = 63
HORIZ_POS_CARROT_01 = 79
HORIZ_POS_CARROT_02 = 95

# Initial horizontal position constants

INIT_FARMER_HORIZ_POS = (XMAX // 2) + 4
INIT_GOPHER_HORIZ_POS = XMAX_GOPHER - 1
INIT_SEED_VERT_POS = 8

# Game selection constants

ACTIVE_PLAYER_MASK = 0xF0
GAME_SELECTION_MASK = 0x0F

PLAYER_ONE_ACTIVE = 0 << 4
PLAYER_TWO_ACTIVE = 15 << 4

MAX_GAME_SELECTION = 3

# Game State values

GS_DISPLAY_COPYRIGHT = 0
GS_DISPLAY_COPYRIGHT_WAIT = 1
GS_DISPLAY_COMPANY = 2
GS_DISPLAY_COMPANY_WAIT = 3
GS_RESET_PLAYER_VARIABLES = 4
GS_DISPLAY_GAME_SELECTION = 5
GS_PAUSE_GAME_STATE = 6
GS_CHECK_FARMER_MOVEMENT = 7
GS_GOPHER_STOLE_CARROT = 8
GS_DUCK_WAIT = 9
GS_INIT_GAME_FOR_ALTERNATE_PLAYER = 10
GS_ALTERNATE_PLAYERS = 11
GS_INIT_GAME_FOR_GAME_OVER = 12
GS_DISPLAY_PLAYER_NUMBER = 13
GS_PAUSE_FOR_ACTION_BUTTON = 14
GS_WAIT_FOR_NEW_GAME = 15

# Carrot constants

CARROT_COARSE_POSITION_CYCLE_41 = 0
CARROT_COARSE_POSITION_CYCLE_47 = 0x80
CARROT_COARSE_POSITION_CYCLE_52 = 0x7F

# Duck constants

INIT_DUCK_ANIMATION_RATE = 32
DUCK_ANIMATION_DOWN_WING = INIT_DUCK_ANIMATION_RATE - 8
DUCK_ANIMATION_STATIONARY_WING = DUCK_ANIMATION_DOWN_WING - 8
DUCK_ANIMATION_UP_WING = DUCK_ANIMATION_STATIONARY_WING - 8

DUCK_HORIZ_DIR_MASK = 0b10000000  # Set, if moving left
SEED_TARGET_HORIZ_POS_MASK = 0b01111111
DUCK_TRAVEL_LEFT = 1 << 7
DUCK_TRAVEL_RIGHT = 0 << 7

# Gopher constants

GOPHER_TARGET_MASK = 0x0F

GOPHER_HORIZ_DIR_MASK = 0b10000000
GOPHER_TUNNEL_TARGET_MASK = 0b00000111
GOPHER_CARROT_TARGET_MASK = 0b00001000

GOPHER_TRAVEL_LEFT = 1 << 7
GOPHER_TRAVEL_RIGHT = 0 << 7
GOPHER_CARROT_TARGET = 1 << 3
GOPHER_TARGET_LEFT_TUNNELS = 0 << 2
GOPHER_TARGET_RIGHT_TUNNELS = 1 << 2

VERT_POS_GOPHER_UNDERGROUND = 0
VERT_POS_GOPHER_ABOVE_GROUND = 35

# Seed constants

INIT_DECAYING_TIMER_VALUE = 120
DISABLE_SEED = 128

# BCD Point values (subtracted by 1 because carry is set for addition)

POINTS_FILL_TUNNEL = 0x19
POINTS_BONK_GOPHER = 0x99

# Wait timer constants

WAIT_TIME_GAME_START = 16  # wait 239 frames ~ 4 seconds
WAIT_TIME_DISPLAY_COPYRIGHT = 128  # wait 127 frames ~ 2 seconds
WAIT_TIME_CARROT_STOLEN = 136  # wait 119 frames ~ 2 seconds

# Audio Value constants

END_AUDIO_TUNE = 0
AUDIO_DURATION_MASK = 0xE0
AUDIO_TONE_MASK = 0x1F

# Playfield graphic constants

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

# ================================= RAM =================================

# "Reserve" space on RAM for different variables.
current_ram_pointer = 0

ram_name_area_mappings: dict[int, str] = {}
ram_name_additional_mappings: dict[int, list[str]] = {}


def ds(amount: int, name: str):
    global current_ram_pointer
    my_offset = current_ram_pointer

    current_ram_pointer += amount

    for i in range(my_offset, my_offset + amount):
        assert i not in ram_name_area_mappings, f"Duplicated ram_name_area_mappings key {i}, should never happen!"
        ram_name_area_mappings[i] = name + ("" if amount == 1 else "+" + str(i - my_offset))

    return my_offset


def ram_name(base_offset: int, inner_offset: int, name: str):
    global ram_name_additional_mappings

    current_list = ram_name_additional_mappings.get(base_offset + inner_offset, [])
    current_list.append(name)
    ram_name_additional_mappings[base_offset + inner_offset] = current_list


gardenDirtValues = ds(24, "gardenDirtValues")
_1stGardenDirtValues = gardenDirtValues + 0
ram_name(gardenDirtValues, 0, "_1stGardenDirtValues")
_1stGardenDirtLeftPFValues = gardenDirtValues + 0
ram_name(gardenDirtValues, 0, "_1stGardenDirtLeftPFValues")
_1stGardenDirtLeftPF0 = gardenDirtValues + 0
ram_name(gardenDirtValues, 0, "_1stGardenDirtLeftPF0")
_1stGardenDirtLeftPF1 = gardenDirtValues + 1
ram_name(gardenDirtValues, 1, "_1stGardenDirtLeftPF1")
_1stGardenDirtLeftPF2 = gardenDirtValues + 2
ram_name(gardenDirtValues, 2, "_1stGardenDirtLeftPF2")
_1stGardenDirtRightPFValues = gardenDirtValues + 3
ram_name(gardenDirtValues, 3, "_1stGardenDirtRightPFValues")
_1stGardenDirtRightPF0 = gardenDirtValues + 3
ram_name(gardenDirtValues, 3, "_1stGardenDirtRightPF0")
_1stGardenDirtRightPF1 = gardenDirtValues + 4
ram_name(gardenDirtValues, 4, "_1stGardenDirtRightPF1")
_1stGardenDirtRightPF2 = gardenDirtValues + 5
ram_name(gardenDirtValues, 5, "_1stGardenDirtRightPF2")
_2ndGardenDirtValues = gardenDirtValues + 6
ram_name(gardenDirtValues, 6, "_2ndGardenDirtValues")
_2ndGardenDirtLeftPFValues = gardenDirtValues + 6
ram_name(gardenDirtValues, 6, "_2ndGardenDirtLeftPFValues")
_2ndGardenDirtLeftPF0 = gardenDirtValues + 6
ram_name(gardenDirtValues, 6, "_2ndGardenDirtLeftPF0")
_2ndGardenDirtLeftPF1 = gardenDirtValues + 7
ram_name(gardenDirtValues, 7, "_2ndGardenDirtLeftPF1")
_2ndGardenDirtLeftPF2 = gardenDirtValues + 8
ram_name(gardenDirtValues, 8, "_2ndGardenDirtLeftPF2")
_2ndGardenDirtRightPFValues = gardenDirtValues + 9
ram_name(gardenDirtValues, 9, "_2ndGardenDirtRightPFValues")
_2ndGardenDirtRightPF0 = gardenDirtValues + 9
ram_name(gardenDirtValues, 9, "_2ndGardenDirtRightPF0")
_2ndGardenDirtRightPF1 = gardenDirtValues + 10
ram_name(gardenDirtValues, 10, "_2ndGardenDirtRightPF1")
_2ndGardenDirtRightPF2 = gardenDirtValues + 11
ram_name(gardenDirtValues, 11, "_2ndGardenDirtRightPF2")
_3rdGardenDirtValues = gardenDirtValues + 12
ram_name(gardenDirtValues, 12, "_3rdGardenDirtValues")
_3rdGardenDirtLeftPFValues = gardenDirtValues + 12
ram_name(gardenDirtValues, 12, "_3rdGardenDirtLeftPFValues")
_3rdGardenDirtLeftPF0 = gardenDirtValues + 12
ram_name(gardenDirtValues, 12, "_3rdGardenDirtLeftPF0")
_3rdGardenDirtLeftPF1 = gardenDirtValues + 13
ram_name(gardenDirtValues, 13, "_3rdGardenDirtLeftPF1")
_3rdGardenDirtLeftPF2 = gardenDirtValues + 14
ram_name(gardenDirtValues, 14, "_3rdGardenDirtLeftPF2")
_3rdGardenDirtRightPFValues = gardenDirtValues + 15
ram_name(gardenDirtValues, 15, "_3rdGardenDirtRightPFValues")
_3rdGardenDirtRightPF0 = gardenDirtValues + 15
ram_name(gardenDirtValues, 15, "_3rdGardenDirtRightPF0")
_3rdGardenDirtRightPF1 = gardenDirtValues + 16
ram_name(gardenDirtValues, 16, "_3rdGardenDirtRightPF1")
_3rdGardenDirtRightPF2 = gardenDirtValues + 17
ram_name(gardenDirtValues, 17, "_3rdGardenDirtRightPF2")
_4thGardenDirtValues = gardenDirtValues + 18
ram_name(gardenDirtValues, 18, "_4thGardenDirtValues")
_4thGardenDirtLeftPFValues = gardenDirtValues + 18
ram_name(gardenDirtValues, 18, "_4thGardenDirtLeftPFValues")
_4thGardenDirtLeftPF0 = gardenDirtValues + 18
ram_name(gardenDirtValues, 18, "_4thGardenDirtLeftPF0")
_4thGardenDirtLeftPF1 = gardenDirtValues + 19
ram_name(gardenDirtValues, 19, "_4thGardenDirtLeftPF1")
_4thGardenDirtLeftPF2 = gardenDirtValues + 20
ram_name(gardenDirtValues, 20, "_4thGardenDirtLeftPF2")
_4thGardenDirtRightPFValues = gardenDirtValues + 21
ram_name(gardenDirtValues, 21, "_4thGardenDirtRightPFValues")
_4thGardenDirtRightPF0 = gardenDirtValues + 21
ram_name(gardenDirtValues, 21, "_4thGardenDirtRightPF0")
_4thGardenDirtRightPF1 = gardenDirtValues + 22
ram_name(gardenDirtValues, 22, "_4thGardenDirtRightPF1")
_4thGardenDirtRightPF2 = gardenDirtValues + 23
ram_name(gardenDirtValues, 23, "_4thGardenDirtRightPF2")

# -------------------------------------------------

duckGraphicPtrs = ds(4, "duckGraphicPtrs")
duckLeftGraphicPtrs = duckGraphicPtrs + 0
ram_name(duckGraphicPtrs, 0, "duckLeftGraphicPtrs")
duckRightGraphicPtrs = duckGraphicPtrs + 2
ram_name(duckGraphicPtrs, 2, "duckRightGraphicPtrs")
duckHorizPos = ds(1, "duckHorizPos")
farmerGraphicPtrs = ds(2, "farmerGraphicPtrs")
farmerHorizPos = ds(1, "farmerHorizPos")
carrotTopGraphicPtrs = ds(2, "carrotTopGraphicPtrs")
carrotGraphicsPtrs = ds(2, "carrotGraphicsPtrs")
displayingCarrotAttributes = ds(3, "displayingCarrotAttributes")
carrotCoarsePositionValue = displayingCarrotAttributes + 0
ram_name(displayingCarrotAttributes, 0, "carrotCoarsePositionValue")
carrotHorizAdjustValue = displayingCarrotAttributes + 1
ram_name(displayingCarrotAttributes, 1, "carrotHorizAdjustValue")
carrotNUSIZValue = displayingCarrotAttributes + 2
ram_name(displayingCarrotAttributes, 2, "carrotNUSIZValue")

# -------------------------------------------------

zone00_GopherGraphicsPtrs = ds(2, "zone00_GopherGraphicsPtrs")
gopherHorizPos = ds(1, "gopherHorizPos")
gopherNUSIZValue = ds(1, "gopherNUSIZValue")
zone01_GopherGraphicsPtrs = ds(2, "zone01_GopherGraphicsPtrs")
zone02_GopherGraphicsPtrs = ds(2, "zone02_GopherGraphicsPtrs")
farmerAnimationIdx = ds(1, "farmerAnimationIdx")

# -------------------------------------------------

playerInformationValues = ds(10, "playerInformationValues")
currentPlayerInformation = playerInformationValues + 0
ram_name(playerInformationValues, 0, "currentPlayerInformation")
# Score takes 3 bytes? + 0, + 1, + 2
currentPlayerScore = playerInformationValues + 0
ram_name(playerInformationValues, 0, "currentPlayerScore+0")
ram_name(playerInformationValues, 1, "currentPlayerScore+1")
ram_name(playerInformationValues, 2, "currentPlayerScore+2")
initGopherChangeDirectionTimer = playerInformationValues + 3
ram_name(playerInformationValues, 3, "initGopherChangeDirectionTimer")
carrotPattern = playerInformationValues + 4
ram_name(playerInformationValues, 4, "carrotPattern")
reservedPlayerInformation = playerInformationValues + 5
ram_name(playerInformationValues, 5, "reservedPlayerInformation")
# Score takes 3 bytes? + 5, + 6, + 7
reservedPlayerScore = playerInformationValues + 5
ram_name(playerInformationValues, 5, "reservedPlayerScore")
reservedGopherChangeDirectionTimer = playerInformationValues + 8
ram_name(playerInformationValues, 8, "reservedGopherChangeDirectionTimer")
reservedPlayerCarrotPattern = playerInformationValues + 9
ram_name(playerInformationValues, 9, "reservedPlayerCarrotPattern")

# -------------------------------------------------

digitGraphicPtrs = ds(12, "digitGraphicPtrs")
actionButtonDebounce = ds(1, "actionButtonDebounce")

# -------------------------------------------------

tmpMulti2 = ds(1, "tmpMulti2")
tmpMulti8 = tmpMulti2
ram_name(tmpMulti2, 0, "tmpMulti8")
tmpCurrentPlayerData = tmpMulti2
ram_name(tmpMulti2, 0, "tmpCurrentPlayerData")
tmpEndGraphicPtrIdx = tmpMulti2
ram_name(tmpMulti2, 0, "tmpEndGraphicPtrIdx")
tmpDigitGraphicsColorValue = tmpMulti2
ram_name(tmpMulti2, 0, "tmpDigitGraphicsColorValue")
tmpCharHolder = tmpMulti2
ram_name(tmpMulti2, 0, "tmpCharHolder")
tmpShovelHorizPos = tmpMulti2
ram_name(tmpMulti2, 0, "tmpShovelHorizPos")
tmpShovelVertTunnelIndex = tmpMulti2
ram_name(tmpMulti2, 0, "tmpShovelVertTunnelIndex")
tmpGardenDirtIndex = tmpMulti2
ram_name(tmpMulti2, 0, "tmpGardenDirtIndex")
tmpSixDigitDisplayLoop = ds(1, "tmpSixDigitDisplayLoop")
tmpDigitPointerMSB = tmpSixDigitDisplayLoop
ram_name(tmpSixDigitDisplayLoop, 0, "tmpDigitPointerMSB")
tmpGameAudioSavedY = tmpSixDigitDisplayLoop
ram_name(tmpSixDigitDisplayLoop, 0, "tmpGameAudioSavedY")

# -------------------------------------------------

# random takes two bytes
random = ds(2, "random")
frameCount = ds(1, "frameCount")
gameIdleTimer = ds(1, "gameIdleTimer")

# -------------------------------------------------

audioIndexValues = ds(2, "audioIndexValues")
leftAudioIndexValue = audioIndexValues
ram_name(audioIndexValues, 0, "leftAudioIndexValue")
rightAudioIndexValue = audioIndexValues + 1
ram_name(audioIndexValues, 1, "rightAudioIndexValue")

audioDurationValues = ds(2, "audioDurationValues")
audioChannelIndex = ds(1, "audioChannelIndex")
gameState = ds(1, "gameState")
gameSelection = ds(1, "gameSelection")
selectDebounce = ds(1, "selectDebounce")

# -------------------------------------------------

gopherHorizAnimationRate = selectDebounce
ram_name(selectDebounce, 0, "gopherHorizAnimationRate")
gopherVertPos = ds(1, "gopherVertPos")
gopherReflectState = ds(1, "gopherReflectState")
gopherHorizMovementValues = ds(1, "gopherHorizMovementValues")
gopherVertMovementValues = ds(1, "gopherVertMovementValues")
gopherChangeDirectionTimer = ds(1, "gopherChangeDirectionTimer")
gopherTauntTimer = ds(1, "gopherTauntTimer")
duckAttributes = ds(1, "duckAttributes")
fallingSeedVertPos = ds(1, "fallingSeedVertPos")
fallingSeedScanline = ds(1, "fallingSeedScanline")
duckAnimationRate = ds(1, "duckAnimationRate")
fallingSeedHorizPos = ds(1, "fallingSeedHorizPos")
heldSeedDecayingTimer = ds(1, "heldSeedDecayingTimer")


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

# === ATARI / TIA CONSTANTS ===

HMOVE_L7 = 0x70
HMOVE_L6 = 0x60
HMOVE_L5 = 0x50
HMOVE_L4 = 0x40
HMOVE_L3 = 0x30
HMOVE_L2 = 0x20
HMOVE_L1 = 0x10
HMOVE_0 = 0x00
HMOVE_R1 = 0xF0
HMOVE_R2 = 0xE0
HMOVE_R3 = 0xD0
HMOVE_R4 = 0xC0
HMOVE_R5 = 0xB0
HMOVE_R6 = 0xA0
HMOVE_R7 = 0x90
HMOVE_R8 = 0x80

# values for ENAMx and ENABL
DISABLE_BM = 0b00
ENABLE_BM = 0b10

# values for RESMPx
LOCK_MISSILE = 0b10
UNLOCK_MISSILE = 0b00

# values for REFPx:
NO_REFLECT = 0b0000
REFLECT = 0b1000

# values for NUSIZx:
ONE_COPY = 0b000
TWO_COPIES = 0b001
TWO_MED_COPIES = 0b010
THREE_COPIES = 0b011
TWO_WIDE_COPIES = 0b100
DOUBLE_SIZE = 0b101
THREE_MED_COPIES = 0b110
QUAD_SIZE = 0b111
MSBL_SIZE1 = 0b000000
MSBL_SIZE2 = 0b010000
MSBL_SIZE4 = 0b100000
MSBL_SIZE8 = 0b110000

# values for CTRLPF:
PF_PRIORITY = 0b100
PF_SCORE = 0b10
PF_REFLECT = 0b01
PF_NO_REFLECT = 0b00

# values for SWCHB
P1_DIFF_MASK = 0b10000000
P0_DIFF_MASK = 0b01000000
BW_MASK = 0b00001000
SELECT_MASK = 0b00000010
RESET_MASK = 0b00000001

VERTICAL_DELAY = 1

# SWCHA joystick bits:
MOVE_RIGHT = 0b01111111
MOVE_LEFT = 0b10111111
MOVE_DOWN = 0b11011111
MOVE_UP = 0b11101111
P0_JOYSTICK_MASK = 0b11110000
P1_JOYSTICK_MASK = 0b00001111
P0_NO_MOVE = P0_JOYSTICK_MASK
P1_NO_MOVE = P1_JOYSTICK_MASK
NO_MOVE = P0_NO_MOVE | P1_NO_MOVE
P0_HORIZ_MOVE = MOVE_RIGHT & MOVE_LEFT & P0_NO_MOVE
P0_VERT_MOVE = MOVE_UP & MOVE_DOWN & P0_NO_MOVE
P1_HORIZ_MOVE = ((MOVE_RIGHT & MOVE_LEFT) >> 4) & P1_NO_MOVE
P1_VERT_MOVE = ((MOVE_UP & MOVE_DOWN) >> 4) & P1_NO_MOVE

# SWCHA paddle bits:
P0_TRIGGER_PRESSED = 0b01111111
P1_TRIGGER_PRESSED = 0b10111111
P2_TRIGGER_PRESSED = 0b11110111
P3_TRIGGER_PRESSED = 0b11111011

# values for VBLANK:
DUMP_PORTS = 0b10000000
ENABLE_LATCHES = 0b01000000
DISABLE_TIA = 0b00000010
ENABLE_TIA = 0b00000000

# values for VSYNC:
START_VERT_SYNC = 0b10
STOP_VERT_SYNC = 0b00

COLUPF = 14

# MOVE_RIGHT = ~(1 << 4) & 0xFF  # confirmed
# MOVE_LEFT = ~(1 << 5) & 0xFF  # confirmed
ACTION_MASK = 1 << 7

# === ADDITIONAL MEMORY ADDRESSES ==


__PlayerNumberLiteralSprites = 0xFBBD
__PlayerNumberLiteralSprites_LOW = 0xBD
__PlayerNumberLiteralSprites_HIGH = 0xFB
__PlayerNumberLiteral_00 = 0xFBBD
__PlayerNumberLiteral_00_LOW = 0xBD
__PlayerNumberLiteral_00_HIGH = 0xFB
__PlayerNumber_01 = 0xFBC7
__PlayerNumber_01_LOW = 0xC7
__PlayerNumber_01_HIGH = 0xFB
__PlayerNumber_02 = 0xFBD1
__PlayerNumber_02_LOW = 0xD1
__PlayerNumber_02_HIGH = 0xFB
__PlayerNumber_03 = 0xFBDB
__PlayerNumber_03_LOW = 0xDB
__PlayerNumber_03_HIGH = 0xFB
__PlayerNumber_04 = 0xFBE5
__PlayerNumber_04_LOW = 0xE5
__PlayerNumber_04_HIGH = 0xFB
__HorizontalTargetValues = 0xFBEF
__HorizontalTargetValues_LOW = 0xEF
__HorizontalTargetValues_HIGH = 0xFB
__NumberFonts = 0xFC00
__NumberFonts_LOW = 0x00
__NumberFonts_HIGH = 0xFC
__zero = 0xFC00
__zero_LOW = 0x00
__zero_HIGH = 0xFC
__one = 0xFC0A
__one_LOW = 0x0A
__one_HIGH = 0xFC
__two = 0xFC14
__two_LOW = 0x14
__two_HIGH = 0xFC
__three = 0xFC1E
__three_LOW = 0x1E
__three_HIGH = 0xFC
__four = 0xFC28
__four_LOW = 0x28
__four_HIGH = 0xFC
__five = 0xFC32
__five_LOW = 0x32
__five_HIGH = 0xFC
__six = 0xFC3C
__six_LOW = 0x3C
__six_HIGH = 0xFC
__seven = 0xFC46
__seven_LOW = 0x46
__seven_HIGH = 0xFC
__eight = 0xFC50
__eight_LOW = 0x50
__eight_HIGH = 0xFC
__nine = 0xFC5A
__nine_LOW = 0x5A
__nine_HIGH = 0xFC
__USGamesLiteral = 0xFC64
__USGamesLiteral_LOW = 0x64
__USGamesLiteral_HIGH = 0xFC
__USGamesLiteral_00 = 0xFC64
__USGamesLiteral_00_LOW = 0x64
__USGamesLiteral_00_HIGH = 0xFC
__USGamesLiteral_01 = 0xFC6E
__USGamesLiteral_01_LOW = 0x6E
__USGamesLiteral_01_HIGH = 0xFC
__USGamesLiteral_02 = 0xFC78
__USGamesLiteral_02_LOW = 0x78
__USGamesLiteral_02_HIGH = 0xFC
__USGamesLiteral_03 = 0xFC82
__USGamesLiteral_03_LOW = 0x82
__USGamesLiteral_03_HIGH = 0xFC
__USGamesLiteral_04 = 0xFC8C
__USGamesLiteral_04_LOW = 0x8C
__USGamesLiteral_04_HIGH = 0xFC
__USGamesLiteral_05 = 0xFC96
__USGamesLiteral_05_LOW = 0x96
__USGamesLiteral_05_HIGH = 0xFC
__GameSelectionLiteralSprites = 0xFCA0
__GameSelectionLiteralSprites_LOW = 0xA0
__GameSelectionLiteralSprites_HIGH = 0xFC
__GameSelection_00 = 0xFCA0
__GameSelection_00_LOW = 0xA0
__GameSelection_00_HIGH = 0xFC
__GameSelection_01 = 0xFCAA
__GameSelection_01_LOW = 0xAA
__GameSelection_01_HIGH = 0xFC
__GameSelection_02 = 0xFCB4
__GameSelection_02_LOW = 0xB4
__GameSelection_02_HIGH = 0xFC
__GameSelection_03 = 0xFCBE
__GameSelection_03_LOW = 0xBE
__GameSelection_03_HIGH = 0xFC
__FarmerColorValues = 0xFCC9
__FarmerColorValues_LOW = 0xC9
__FarmerColorValues_HIGH = 0xFC
__Blank = 0xFD00
__Blank_LOW = 0x00
__Blank_HIGH = 0xFD
__AudioValues = 0xFD0A
__AudioValues_LOW = 0x0A
__AudioValues_HIGH = 0xFD
__StartingThemeAudioValues_00 = 0xFD0A
__StartingThemeAudioValues_00_LOW = 0x0A
__StartingThemeAudioValues_00_HIGH = 0xFD
__StartingThemeAudioValues_01 = 0xFD29
__StartingThemeAudioValues_01_LOW = 0x29
__StartingThemeAudioValues_01_HIGH = 0xFD
__BonkGopherAudioValues = 0xFD43
__BonkGopherAudioValues_LOW = 0x43
__BonkGopherAudioValues_HIGH = 0xFD
__GopherTauntAudioValues = 0xFD4A
__GopherTauntAudioValues_LOW = 0x4A
__GopherTauntAudioValues_HIGH = 0xFD
__StolenCarrotAudioValues = 0xFD61
__StolenCarrotAudioValues_LOW = 0x61
__StolenCarrotAudioValues_HIGH = 0xFD
__DigTunnelAudioValues = 0xFD7A
__DigTunnelAudioValues_LOW = 0x7A
__DigTunnelAudioValues_HIGH = 0xFD
__FillTunnelAudioValues = 0xFD7E
__FillTunnelAudioValues_LOW = 0x7E
__FillTunnelAudioValues_HIGH = 0xFD
__DuckQuackingAudioValues = 0xFD84
__DuckQuackingAudioValues_LOW = 0x84
__DuckQuackingAudioValues_HIGH = 0xFD
__GameOverThemeAudioValues_00 = 0xFD8C
__GameOverThemeAudioValues_00_LOW = 0x8C
__GameOverThemeAudioValues_00_HIGH = 0xFD
__GameOverThemeAudioValues_01 = 0xFD9F
__GameOverThemeAudioValues_01_LOW = 0x9F
__GameOverThemeAudioValues_01_HIGH = 0xFD
__CarrotGraphics = 0xFDB2
__CarrotGraphics_LOW = 0xB2
__CarrotGraphics_HIGH = 0xFD
__CarrotTopGraphics = 0xFDC8
__CarrotTopGraphics_LOW = 0xC8
__CarrotTopGraphics_HIGH = 0xFD
__CarrotColorValues = 0xFDD5
__CarrotColorValues_LOW = 0xD5
__CarrotColorValues_HIGH = 0xFD
__GrassColorValues = 0xFDEB
__GrassColorValues_LOW = 0xEB
__GrassColorValues_HIGH = 0xFD
__GopherTargetVertPositions = 0xFDF8
__GopherTargetVertPositions_LOW = 0xF8
__GopherTargetVertPositions_HIGH = 0xFD
__CarrotAttributeValues = 0xFE08
__CarrotAttributeValues_LOW = 0x08
__CarrotAttributeValues_HIGH = 0xFE
__FarmerSprites = 0xFE1D
__FarmerSprites_LOW = 0x1D
__FarmerSprites_HIGH = 0xFE
__FarmerSprite_00 = 0xFE1D
__FarmerSprite_00_LOW = 0x1D
__FarmerSprite_00_HIGH = 0xFE
__FarmerSprite_01 = 0xFE50
__FarmerSprite_01_LOW = 0x50
__FarmerSprite_01_HIGH = 0xFE
__FarmerSprite_02 = 0xFE83
__FarmerSprite_02_LOW = 0x83
__FarmerSprite_02_HIGH = 0xFE
__DuckWingsStationaryGraphics = 0xFEB6
__DuckWingsStationaryGraphics_LOW = 0xB6
__DuckWingsStationaryGraphics_HIGH = 0xFE
__DuckFaceGraphics = 0xFEC9
__DuckFaceGraphics_LOW = 0xC9
__DuckFaceGraphics_HIGH = 0xFE
__DuckWingsDownGraphics = 0xFEDC
__DuckWingsDownGraphics_LOW = 0xDC
__DuckWingsDownGraphics_HIGH = 0xFE
__DuckWingsUpGraphics = 0xFEEF
__DuckWingsUpGraphics_LOW = 0xEF
__DuckWingsUpGraphics_HIGH = 0xFE
__DuckColorValues = 0xFF03
__DuckColorValues_LOW = 0x03
__DuckColorValues_HIGH = 0xFF
__DuckLeftColorValues = 0xFF03
__DuckLeftColorValues_LOW = 0x03
__DuckLeftColorValues_HIGH = 0xFF
__DuckRightColorValues = 0xFF16
__DuckRightColorValues_LOW = 0x16
__DuckRightColorValues_HIGH = 0xFF
__CopyrightLiteralSprites = 0xFF28
__CopyrightLiteralSprites_LOW = 0x28
__CopyrightLiteralSprites_HIGH = 0xFF
__Copyright_00 = 0xFF28
__Copyright_00_LOW = 0x28
__Copyright_00_HIGH = 0xFF
__Copyright_01 = 0xFF32
__Copyright_01_LOW = 0x32
__Copyright_01_HIGH = 0xFF
__Copyright_02 = 0xFF3C
__Copyright_02_LOW = 0x3C
__Copyright_02_HIGH = 0xFF
__Copyright_03 = 0xFF46
__Copyright_03_LOW = 0x46
__Copyright_03_HIGH = 0xFF
__Copyright_04 = 0xFF50
__Copyright_04_LOW = 0x50
__Copyright_04_HIGH = 0xFF
__Copyright_05 = 0xFF5A
__Copyright_05_LOW = 0x5A
__Copyright_05_HIGH = 0xFF
__RisingGopherSprite = 0xFF64
__RisingGopherSprite_LOW = 0x64
__RisingGopherSprite_HIGH = 0xFF
__NullSprite = 0xFF87
__NullSprite_LOW = 0x87
__NullSprite_HIGH = 0xFF
__NullRunningGopher = 0xFF9D
__NullRunningGopher_LOW = 0x9D
__NullRunningGopher_HIGH = 0xFF
__RunningGopher_00 = 0xFFAA
__RunningGopher_00_LOW = 0xAA
__RunningGopher_00_HIGH = 0xFF
__RunningGopher_01 = 0xFFBA
__RunningGopher_01_LOW = 0xBA
__RunningGopher_01_HIGH = 0xFF
__GopherTauntSprite_00 = 0xFFCA
__GopherTauntSprite_00_LOW = 0xCA
__GopherTauntSprite_00_HIGH = 0xFF
__GopherTauntSprite_01 = 0xFFD9
__GopherTauntSprite_01_LOW = 0xD9
__GopherTauntSprite_01_HIGH = 0xFF

# ================ DATA TABLES ========

CarrotAttributeValues = [
    CARROT_COARSE_POSITION_CYCLE_52, HMOVE_L1, ONE_COPY,
    CARROT_COARSE_POSITION_CYCLE_47, HMOVE_L2, ONE_COPY,
    CARROT_COARSE_POSITION_CYCLE_47, HMOVE_L2, TWO_COPIES,
    CARROT_COARSE_POSITION_CYCLE_41, HMOVE_0, ONE_COPY,
    CARROT_COARSE_POSITION_CYCLE_41, HMOVE_0, TWO_MED_COPIES,
    CARROT_COARSE_POSITION_CYCLE_41, HMOVE_0, TWO_COPIES,
    CARROT_COARSE_POSITION_CYCLE_41, HMOVE_0, THREE_COPIES
]

HorizontalTargetValues = [
    HORIZ_POS_HOLE_00, HORIZ_POS_HOLE_01,
    HORIZ_POS_HOLE_02, HORIZ_POS_HOLE_03,
    HORIZ_POS_HOLE_04, HORIZ_POS_HOLE_05,
    HORIZ_POS_HOLE_00, HORIZ_POS_HOLE_05,
    HORIZ_POS_CARROT_02, HORIZ_POS_CARROT_01, HORIZ_POS_CARROT_00
]

DirtMaskingBits = [
    #  PF0 bit masking values
    1 << 4, 1 << 5, 1 << 6, 1 << 7,
    # PF1 bit masking values
    1 << 7, 1 << 6, 1 << 5, 1 << 4, 1 << 3, 1 << 2, 1 << 1, 1 << 0,
    # PF2 bit masking values
    1 << 0, 1 << 1, 1 << 2, 1 << 3, 1 << 4, 1 << 5, 1 << 6, 1 << 7
]

GopherTargetVertPositions = [
    VERT_POS_GOPHER_UNDERGROUND,
    VERT_POS_GOPHER_UNDERGROUND + 7,
    VERT_POS_GOPHER_UNDERGROUND + 14,
    VERT_POS_GOPHER_ABOVE_GROUND - 13,
    VERT_POS_GOPHER_ABOVE_GROUND - 1,
    VERT_POS_GOPHER_ABOVE_GROUND,
    VERT_POS_GOPHER_UNDERGROUND + 7,
    VERT_POS_GOPHER_UNDERGROUND + 14,

    VERT_POS_GOPHER_ABOVE_GROUND - 13,
    VERT_POS_GOPHER_ABOVE_GROUND,
    VERT_POS_GOPHER_ABOVE_GROUND - 1,
    VERT_POS_GOPHER_UNDERGROUND + 14,
    VERT_POS_GOPHER_ABOVE_GROUND - 13,
    VERT_POS_GOPHER_ABOVE_GROUND,
    VERT_POS_GOPHER_ABOVE_GROUND - 1,
    VERT_POS_GOPHER_ABOVE_GROUND
]

StartingThemeAudioValues_00 = [
    4,  # high pitch square wave pure tone
    6 << 4 | 15, 7 << 4 | 1, 7 << 4 | 3, 7 << 4 | 4, 7 << 4 | 3,
    7 << 4 | 1, 7 << 4 | 3, 7 << 4 | 10, 7 << 4 | 15, 7 << 4 | 13,
    7 << 4 | 10, 7 << 4 | 7, 7 << 4 | 10, 7 << 4 | 15, 28 << 3 | 26,
    6 << 4 | 15, 7 << 4 | 3, 6 << 4 | 15, 7 << 4 | 3, 7 << 4 | 1,
    7 << 4 | 4, 7 << 4 | 1, 7 << 4 | 10, 7 << 4 | 4, 7 << 4 | 2,
    7 << 4 | 1, 7 << 4 | 0, 16 << 3 | 15, 20 << 3 | 9, END_AUDIO_TUNE
]
StartingThemeAudioValues_01 = [
    12,  # lower pitch square wave sound
    7 << 4 | 1, 7 << 4 | 1, 28 << 3 | 26, 7 << 4 | 4, 7 << 4 | 4,
    7 << 4 | 1, 7 << 4 | 1, 28 << 3 | 15, 28 << 3 | 17, 7 << 4 | 1,
    7 << 4 | 4, 7 << 4 | 1, 7 << 4 | 4, 7 << 4 | 3, 7 << 4 | 7,
    7 << 4 | 3, 7 << 4 | 7, 7 << 4 | 1, 7 << 4 | 2, 7 << 4 | 3,
    7 << 4 | 6, 7 << 4 | 4, 7 << 4 | 1, 7 << 4 | 10, END_AUDIO_TUNE
]
BonkGopherAudioValues = [
    12,  # lower pitch square wave sound
    1 << 4 | 10, 1 << 4 | 2, 0 << 4 | 11, 0 << 4 | 6, 0 << 4 | 1,
    END_AUDIO_TUNE]
GopherTauntAudioValues = [
    4,  # high pitch square wave pure tone
    3 << 4 | 7, 1 << 4 | 0, 3 << 4 | 7, 1 << 4 | 0, 1 << 4 | 7,
    3 << 4 | 11, 1 << 4 | 3, 3 << 4 | 11, 1 << 4 | 4, 0 << 4 | 14,
    1 << 4 | 4, 0 << 4 | 14, 1 << 4 | 4, 3 << 4 | 7, 1 << 4 | 0,
    3 << 4 | 7, 1 << 4 | 0, 1 << 4 | 7, 1 << 4 | 11, 1 << 4 | 3,
    3 << 4 | 11, END_AUDIO_TUNE]
StolenCarrotAudioValues = [
    7,  # low and buzzy
    1 << 4 | 3, 0 << 4 | 7, 1 << 4 | 3, 0 << 4 | 7, 1 << 4 | 2,
    0 << 4 | 6, 1 << 4 | 2, 0 << 4 | 6, 1 << 4 | 1, 0 << 4 | 5,
    1 << 4 | 1, 0 << 4 | 5, 1 << 4 | 0, 0 << 4 | 4, 0 << 4 | 15,
    0 << 4 | 3, 0 << 4 | 14, 0 << 4 | 2, 0 << 4 | 13, 0 << 4 | 2,
    0 << 4 | 12, 0 << 4 | 1, 7 << 4 | 2, END_AUDIO_TUNE]
DigTunnelAudioValues = [
    8,  # white noise
    0 << 4 | 4, 0 << 4 | 3, END_AUDIO_TUNE]
FillTunnelAudioValues = [
    6,  # bass sound
    0 << 4 | 1, 0 << 4 | 4, 0 << 4 | 2, 0 << 4 | 6, END_AUDIO_TUNE
]
DuckQuackingAudioValues = [
    1,  # saw waveform
    0 << 4 | 15, 0 << 4 | 14, 2 << 4 | 13, 2 << 4 | 12, 4 << 4 | 11,
    0 << 4 | 12, END_AUDIO_TUNE]
GameOverThemeAudioValues_00 = [
    4,  # high pitch square wave pure tone
    28 << 3 | 7, 28 << 3 | 11, 28 << 3 | 17, 28 << 3 | 26, 3 << 4 | 3,
    2 << 4 | 0, 3 << 4 | 3, 2 << 4 | 0, 3 << 4 | 3, 2 << 4 | 0,
    3 << 4 | 3, 2 << 4 | 0, 7 << 4 | 4, 6 << 4 | 0, 7 << 4 | 4,
    6 << 4 | 0, 7 << 4 | 15, END_AUDIO_TUNE]
GameOverThemeAudioValues_01 = [
    4,  # high pitch square wave pure tone
    28 << 3 | 11, 28 << 3 | 17, 28 << 3 | 26, 28 << 3 | 19, 3 << 4 | 7,
    2 << 4 | 0, 3 << 4 | 7, 2 << 4 | 0, 3 << 4 | 7, 2 << 4 | 0,
    3 << 4 | 7, 2 << 4 | 0, 7 << 4 | 10, 6 << 4 | 0, 7 << 4 | 10,
    6 << 4 | 0, 7 << 4 | 3, END_AUDIO_TUNE]

AudioValues = StartingThemeAudioValues_00 + StartingThemeAudioValues_01 + \
              BonkGopherAudioValues + GopherTauntAudioValues + StolenCarrotAudioValues + DigTunnelAudioValues + \
              FillTunnelAudioValues + DuckQuackingAudioValues + GameOverThemeAudioValues_00 + GameOverThemeAudioValues_01

# ================================ GAME STATE =================================


# Input
swcha_input = 0b11111111  # nothing pressed
swchb_input = 0b11111111  # default: pro difficulty, color, select and reset not pressed
intpt4_input = 0b11111111  # not pressed
intpt5_input = 0b11111111  # not pressed

# Create 128 bytes of RAM (zero-initialized)
ram = [0] * 128


# ================================ UTILITY =================================

expected_ram_after_init = np.load("ram_states/init/expected_ram_after_init.npy")
expected_ram_before_start = np.load("ram_states/init/expected_ram_before_start.npy")
expected_ram_after_start = np.load("ram_states/init/expected_ram_after_start.npy")

ignored_ram_states = [
    72,  # tmpSixDigitDisplayLoop - rendering
    93,  # fallingSeedScanline - rendering

    124, 125, 126, 127  # most likely stack, or Stella internals
]

frame_log: list[str] = []
_debug_frame_number = -1


def log(*message):
    global frame_log

    frame_log.append(" ".join([str(piece) for piece in message]))


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


def reset_input():
    global swcha_input
    global swchb_input
    global intpt4_input
    global intpt5_input

    # Reset inputs
    swcha_input = 0b11111111  # nothing pressed
    swchb_input = 0b11111111  # default: pro difficulty, color, select and reset not pressed
    intpt4_input = 0b11111111  # not pressed
    intpt5_input = 0b11111111  # not pressed


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

    global swcha_input
    global swchb_input
    global intpt4_input

    reset_input()

    # Set inputs
    if the_action == "NOOP":
        return
    if the_action == "FIRE" or the_action == "RIGHTFIRE" or the_action == "LEFTFIRE":
        intpt4_input = intpt4_input & ~ACTION_MASK
    if the_action == "RIGHT" or the_action == "RIGHTFIRE":
        swcha_input = swcha_input & ~MOVE_RIGHT
    if the_action == "LEFT" or the_action == "LEFTFIRE":
        swcha_input = swcha_input & ~MOVE_LEFT


def compare_ram_states_with_log(expected: list[int], name: str):
    if not compare_ram_states(ram, expected, name, ignored_ram_states, ram_full_name_mapping, exit_on_mismatch=False):

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


def reset_game(verbose: bool = True):
    global intpt4_input
    global swchb_input

    reset_input()

    if verbose:
        print("Starting...")
    # 1st frame (NOP)
    start()
    if verbose:
        print("Started")
        print()
    assert has_hit_new_frame, "Start did not hit new_frame!"

    if verbose:
        print("Reset to game selection...")

    # Already one NOP used on start
    for i in range(60 - 1):
        # NOP
        do_tick()

    # press reset to go to GS_DISPLAY_GAME_SELECTION (game state 5)
    for i in range(16):
        swchb_input = swchb_input & ~RESET_MASK
        do_tick()
        # release reset
        swchb_input = swchb_input | RESET_MASK

    if verbose:
        print()

    # Optional: use select button so select game mode

    if verbose:
        print("P1 action button to start game...")
    # press left player action button
    intpt4_input = intpt4_input & ~ACTION_MASK
    do_tick()
    # release left player action button
    intpt4_input = intpt4_input | ACTION_MASK
    if verbose:
        print()

    compare_ram_states_with_log(expected_ram_after_init, "after_init")

    # compare_ram_states(ram, expected_ram_state_after_500)

    if verbose:
        print(f"Waiting for WAIT_TIME_GAME_START to run out ({255 - WAIT_TIME_GAME_START - 1} frames)...")

    # Wait till actual game starts
    for i in range(255 - WAIT_TIME_GAME_START - 1):
        do_tick()
    if verbose:
        print()

    compare_ram_states_with_log(expected_ram_before_start, "before_start")

    # Now advance to game state 7 (GS_CHECK_FARMER_MOVEMENT) - main game
    if verbose:
        print("Advance to main game")
    do_tick()
    if verbose:
        print()

    compare_ram_states_with_log(expected_ram_after_start, "after_start")


def get_score_number():
    top = byte_to_bcd_number(ram[playerInformationValues])
    mid = byte_to_bcd_number(ram[playerInformationValues + 1])
    low = byte_to_bcd_number(ram[playerInformationValues + 2])

    total = (top * 100 + mid) * 100 + low
    return total



has_hit_new_frame = False
hit_new_frame_carry_status: int = 0


def do_tick():
    frame_log.clear()
    global has_hit_new_frame
    has_hit_new_frame = False
    vertical_blank(hit_new_frame_carry_status)
    assert has_hit_new_frame, "Tick did not hit new_frame! This is a serious error!"



# ================================ GAME LOGIC =================================


def start():
    # a and x are set to 0
    # memory from 0xFF (255) to 0 are cleared (set to 0)
    # this includes the full RAM state starting at 0x80
    # VSYNC = 0 (most likely meaning the first memory address?)

    for i in range(len(ram)):
        ram[i] = 0
    # ram[0:128] = 0

    # Set stack to 0xFF via txs

    # Jump
    overscan()


def vertical_blank(carry):
    while True:
        # In assembly: Setup blank timer
        # Not needed for python

        """
        lda #STOP_VERT_SYNC
       sta WSYNC                        ; wait for next scan line
       sta VSYNC                        ; end vertical sync (D1 = 0)
       lda #VBLANK_TIME
       sta TIM64T                       ; set timer for vertical blank time
        """

        # Increment frameCount
        ram[frameCount] = byte_increment(ram[frameCount])

        # Read and flip joystick values
        joystick_values = swcha_value()
        flipped_joystick_values = flip_byte(joystick_values)

        # pressed = 0, so with flipped bytes, the result would only be 0 if no joystick (neither p1 nor p2) is pressed
        if flipped_joystick_values != 0:
            # Reset game idle timer on press
            ram[gameIdleTimer] = 0

        a = ram[gameIdleTimer]

        # print("idleTimer =", ram[gameIdleTimer], "| frameCount =", ram[frameCount])

        if is_msb_set(a):
            # Continue loop - this simulates jumping back to VerticalBlank
            continue

        if ram[frameCount] == 0:
            ram[gameIdleTimer] = byte_increment(ram[gameIdleTimer])

        carry = play_game_audio_sounds(carry)
        next_random(carry)

        a = ram[carrotPattern]

        if a != 0:
            # Jump
            determine_carrot_attribute_values(a)

            # Will also end up in animate_duck_wings after determining carrot attribute values
            return

        # NOTE: Code past this point this will never get executed, since this only happens AFTER game over

        # Load null sprites into carrot graphics
        a = __NullSprite_LOW
        ram[carrotTopGraphicPtrs] = a
        ram[carrotGraphicsPtrs] = a
        a = __NullSprite_HIGH
        ram[carrotTopGraphicPtrs + 1] = a
        ram[carrotGraphicsPtrs + 1] = a

        # Jump
        animate_duck_wings()
        return

    # Never reached


def determine_carrot_attribute_values(a):
    a = (a << 1) & 0xFF  # asl
    a = (a + ram[carrotPattern]) & 0xFF

    y = a
    y = byte_decrement(y)
    x = 3 - 1

    while True:
        a = CarrotAttributeValues[y]  # ROM
        ram[displayingCarrotAttributes + x] = a

        y = byte_decrement(y)
        x = byte_decrement(x)

        if is_msb_set(x):
            break

    # Fall through
    animate_duck_wings()


def animate_duck_wings():
    x = ram[duckAnimationRate]

    if x == 0:
        disable_duck()
        return

    x = byte_decrement(x)
    if x == 0:
        a = INIT_DUCK_ANIMATION_RATE
        ram[duckAnimationRate] = a
        a = __DuckWingsStationaryGraphics_LOW
        ram[duckLeftGraphicPtrs] = a

        check_to_play_duck_quacking()
        return
    else:
        ram[duckAnimationRate] = x

        if x == DUCK_ANIMATION_DOWN_WING:
            a = __DuckWingsDownGraphics_LOW
        elif x == DUCK_ANIMATION_STATIONARY_WING:
            a = __DuckWingsStationaryGraphics_LOW
        elif x == DUCK_ANIMATION_UP_WING:
            a = __DuckWingsUpGraphics_LOW
        else:
            check_to_play_duck_quacking()
            return

        ram[duckLeftGraphicPtrs] = a

        # Fall through
        check_to_play_duck_quacking()


def check_to_play_duck_quacking():
    a = ram[frameCount] & 0x1F
    if a != 0:
        move_duck_horizontally()
        return
    else:
        # x = <[DuckQuackingAudioValues - AudioValues]
        set_game_audio_values((__DuckQuackingAudioValues - __AudioValues) & 0xFF)

    # Fall through
    move_duck_horizontally()


def move_duck_horizontally():
    a = ram[duckAttributes]

    if is_msb_set(a):
        move_duck_left()
        return

    ram[duckHorizPos] = byte_increment(ram[duckHorizPos])
    a = ram[duckHorizPos]

    if a < XMAX_DUCK:  # BCC
        move_falling_seed()
        return

    # Fall through
    disable_duck()


def disable_duck():
    a = __NullSprite_LOW
    ram[duckLeftGraphicPtrs] = a
    ram[duckRightGraphicPtrs] = a
    a = __NullSprite_HIGH
    ram[duckLeftGraphicPtrs + 1] = a
    ram[duckRightGraphicPtrs + 1] = a

    ram[duckAnimationRate] = 0

    # Unconditional branch
    move_falling_seed()


def move_duck_left():
    ram[duckHorizPos] = byte_decrement(ram[duckHorizPos])
    a = ram[duckHorizPos]

    if a < XMIN_DUCK:
        disable_duck()
        return

    # Fall through
    move_falling_seed()


# Actually moves seed horizontally together with duck
def move_falling_seed():
    a = ram[fallingSeedVertPos]

    if is_msb_set(a):
        # No seed
        done_move_duck_horizontally()
        return

    a = ram[heldSeedDecayingTimer]
    if a != 0:
        set_farmer_holding_seed()
        return

    a = ram[duckAttributes] & SEED_TARGET_HORIZ_POS_MASK
    if a == ram[fallingSeedHorizPos]:
        dropping_seed()
        return

    # Note: !! Move left or right once, just using clever trick with branching !!

    x = ram[duckAttributes]
    if not is_msb_set(x):
        # Moving right
        ram[fallingSeedHorizPos] = byte_increment(ram[fallingSeedHorizPos])
    else:
        # Moving left
        ram[fallingSeedHorizPos] = byte_decrement(ram[fallingSeedHorizPos])

    # Jump
    done_move_duck_horizontally()


def dropping_seed():
    ram[fallingSeedVertPos] = byte_increment(ram[fallingSeedVertPos])
    a = ram[fallingSeedVertPos]

    if a == (H_DUCK + H_KERNEL_VERT_ADJUSTMENT + H_FARMER - 2):
        # Seed reached ground
        disable_falling_seed()
        return

    if a < (H_DUCK + H_KERNEL_VERT_ADJUSTMENT + 24):
        done_move_duck_horizontally()
        return

    if a >= (H_DUCK + H_KERNEL_VERT_ADJUSTMENT + 28):
        done_move_duck_horizontally()
        return

    # Seed in very specific pixel range above the ground
    a = ram[farmerHorizPos]

    # Calculate absolute difference between farmerHorizPos and fallingSeedHorizPos
    a = sbc(a, ram[fallingSeedHorizPos])
    if not is_positive(a):
        a = flip_byte(a)
        a = adc(a, 1)

    if a >= 5:
        # Did not catch seed
        done_move_duck_horizontally()
        return

    a = INIT_DECAYING_TIMER_VALUE
    ram[heldSeedDecayingTimer] = a

    # Unconditional branch
    done_move_duck_horizontally()


def set_farmer_holding_seed():
    a = ram[farmerHorizPos]
    ram[fallingSeedHorizPos] = a
    dec_result = byte_decrement(ram[heldSeedDecayingTimer])
    ram[heldSeedDecayingTimer] = dec_result

    if dec_result != 0:
        done_move_duck_horizontally()
        return

    # Fall through
    disable_falling_seed()


def disable_falling_seed():
    # Seed decayed
    a = DISABLE_SEED
    ram[fallingSeedVertPos] = a

    # Fall through
    done_move_duck_horizontally()


def done_move_duck_horizontally():
    a = ram[gameState]
    if a == GS_CHECK_FARMER_MOVEMENT:
        # Running game
        check_for_gopher_digging_tunnel()
        return

    # Jump
    done_vertical_blank()


def check_for_gopher_digging_tunnel():
    a = ram[currentPlayerScore]
    if a != 0:  # score >= 100,000 ?
        a = ram[gopherVertMovementValues] & 0x7F

        if a == 0:
            a = a | 0x88
            # Set to taunting gopher vertical value
            ram[gopherVertMovementValues] = a

    # Underground tunnel

    a = ram[gopherVertPos]
    if a == 0:
        a = ram[gopherHorizPos]
        x = ram[gopherReflectState]

        if x == 0:
            # Facing left
            determine_garden_dirt_index(a)
            return

        # Facing right, seems to add width value to dig to right
        a = adc(a, 8)

        # unconditional branch
        determine_garden_dirt_index(a)
        return

    # Upward tunnel
    if a == VERT_POS_GOPHER_ABOVE_GROUND:
        check_for_player_moving_shovel()
        return

    a = ram[gopherHorizMovementValues] & GOPHER_TUNNEL_TARGET_MASK
    x = a
    a = HorizontalTargetValues[x]  # ROM

    # Fall through
    determine_garden_dirt_index(a)


def determine_garden_dirt_index(a):
    x, y = determine_dirt_floor_index(a)
    a = x
    x = ram[gopherVertPos]

    # Digging underground
    if x == 0:
        # Dig 4th garden dirt values (lowest)
        a = adc(a, _4thGardenDirtValues - gardenDirtValues)
        gopher_digging(a, y)
        return

    # digging first garden row
    if x >= VERT_POS_GOPHER_UNDERGROUND + 14:
        # branch if gopher in first garden row (highest)
        gopher_digging(a, y)
        return

    # add offset for 2nd row (one under highest)
    a = adc(a, _2ndGardenDirtValues - gardenDirtValues)

    if x >= VERT_POS_GOPHER_UNDERGROUND + 7:
        # branch if Gopher in second garden row
        gopher_digging(a, y)
        return

    # add offset for 3rd row (one over lowest)
    a = adc(a, _3rdGardenDirtValues - _2ndGardenDirtValues)

    # Fall through
    gopher_digging(a, y)


def gopher_digging(a, y):
    # print("DIGGING", a + gardenDirtValues, "SPECIFIC", y, "mask", bin(DirtMaskingBits[y]))
    # print("Current value", bin(ram[gardenDirtValues + a]))

    x = a
    a = DirtMaskingBits[y] & ram[gardenDirtValues + x]  # ROM

    # a is either 0 = dirt is there, or 1 = dirt was dug AT the masked BIT
    # Checking if bit is not zero, by checking if whole byte is not zero
    if a != 0:
        # print("check mask", bin(DirtMaskingBits[y]))
        # print("my byte", x, "=", bin(ram[gardenDirtValues + x]))

        # Dirt exists
        check_for_player_moving_shovel()
        return

    a = ram[gardenDirtValues + x]
    a = a | DirtMaskingBits[y]
    ram[gardenDirtValues + x] = a

    # Temp ram storage
    ram[tmpGardenDirtIndex] = x

    # x = <[DigTunnelAudioValues - AudioValues]
    set_game_audio_values((__DigTunnelAudioValues - __AudioValues) & 0xFF)

    x = ram[tmpGardenDirtIndex]
    a = ram[gopherVertPos]

    # Tunneling underground
    if a == 0:
        check_to_change_gopher_horizontal_direction()
        return

    y = byte_increment(y)
    a = DirtMaskingBits[y]

    if is_negative(a) or a == 1:
        x = byte_increment(x)

    a = a | ram[gardenDirtValues + x]
    ram[gardenDirtValues + x] = a

    # Fall through
    check_to_change_gopher_horizontal_direction()


def check_to_change_gopher_horizontal_direction():
    a = ram[gopherVertMovementValues]

    if is_negative(a):
        check_for_player_moving_shovel()
        return

    dec_result = byte_decrement(ram[gopherChangeDirectionTimer])
    ram[gopherChangeDirectionTimer] = dec_result

    if dec_result == 0:
        a = ram[gopherVertMovementValues] | 0x80
        ram[gopherVertMovementValues] = a
        a = ram[initGopherChangeDirectionTimer]
        ram[gopherChangeDirectionTimer] = a

        # Unconditional branch
        check_for_player_moving_shovel()
        return

    a = ram[gopherVertPos]

    # Crawling underground
    if a != 0:
        a = 0x80
        ram[gopherVertMovementValues] = a

        # Unconditional branch
        check_for_player_moving_shovel()
        return

    # Flip direction
    a = exclusive_or(ram[gopherHorizMovementValues], GOPHER_HORIZ_DIR_MASK)
    ram[gopherHorizMovementValues] = a

    # Fall through
    check_for_player_moving_shovel()


def done_check_for_player_moving_shovel():
    # Jump
    done_vertical_blank()


def check_for_player_moving_shovel():
    a = ram[farmerAnimationIdx]
    if a != 0:
        increment_farmer_animation_index()
        return

    a = intpt4_value()
    x = ram[gameSelection]
    if not is_positive(x):
        # Switch to second player
        a = intpt5_value()

    a = a & ACTION_MASK
    if not is_positive(a):
        # Action button was not pressed
        a = 0
        ram[actionButtonDebounce] = a

        # Fall through
        done_check_for_player_moving_shovel()
        # Can return, because done_check_for_player_moving_shovel ALWAYS jumps
        return

    # Player action button pressed
    a = ram[actionButtonDebounce]
    if a != 0:
        done_check_for_player_moving_shovel()
        return

    a = 0xFF
    ram[actionButtonDebounce] = a

    # Fall through
    increment_farmer_animation_index()


def increment_farmer_animation_index():
    ram[farmerAnimationIdx] = byte_increment(ram[farmerAnimationIdx])
    a = ram[farmerAnimationIdx]

    if a == 2:
        a = __FarmerSprite_01_LOW
        ram[farmerGraphicPtrs] = a

        # Unconditional branch
        done_check_for_player_moving_shovel()
        return

    if a == 4:
        a = __FarmerSprite_02_LOW
        ram[farmerGraphicPtrs] = a

        # Unconditional branch
        done_check_for_player_moving_shovel()
        return

    if a != 8:
        done_check_for_player_moving_shovel()
        return

    a = 0
    ram[farmerAnimationIdx] = a
    a = __FarmerSprite_00_LOW
    ram[farmerGraphicPtrs] = a
    a = ram[farmerHorizPos]
    a = sbc(a, 4)
    ram[tmpShovelHorizPos] = a
    x = 10

    # Get hole / carrot that farmer is closer than 6 pixels to
    while True:
        a = ram[tmpShovelHorizPos]

        # Absolute difference between horizontal target values and tmpShovelHorizPos
        a = sbc(a, HorizontalTargetValues[x])
        if not is_positive(a):
            a = flip_byte(a)
            a = adc(a, 1)

        if a >= 6:
            x = byte_decrement(x)
            if is_positive(x):
                continue
            else:
                # Jump
                done_vertical_blank()
                return
        else:
            # Carrot planting or hole filling
            check_to_plant_carrot(x)
            return

    # Never reached


# Carrot plating or hole filling
def check_to_plant_carrot(x):
    if x < 8:
        # Only index 8, 9 and 10 are carrots.
        # The rest are tunnels/holes
        determine_to_fill_tunnel(x)
        return

    a = ram[heldSeedDecayingTimer]
    if a == 0:
        # Farmer not holding seed
        done_vertical_blank()
        return

    print("Planting carrot at", x)

    # Plant carrot
    a = 1 << 2
    if x != 10:
        if x != 9:
            a = a >> 1
        a = a >> 1

    a = a | ram[carrotPattern]
    ram[carrotPattern] = a
    a = DISABLE_SEED
    ram[fallingSeedVertPos] = a
    a = 0
    ram[heldSeedDecayingTimer] = a

    # unconditional branch
    done_vertical_blank()


def determine_to_fill_tunnel(x):
    # Temporary RAM
    ram[tmpShovelVertTunnelIndex] = x

    a = ram[gopherVertPos]

    # Not crawling underground
    if a != 0:
        a = ram[gopherHorizMovementValues] & (GOPHER_CARROT_TARGET_MASK | GOPHER_TUNNEL_TARGET_MASK)
        x = a
        # If targeting carrot, will target hole 0, 4, 5; otherwise 0, 1, 2, 3
        a = HorizontalTargetValues[x]
        x = ram[tmpShovelVertTunnelIndex]

        if a == HorizontalTargetValues[x]:
            done_vertical_blank()
            return

    a = HorizontalTargetValues[x]  # get shovel hole position
    x, y = determine_dirt_floor_index(a)

    # Try to find y-coordinate position to fill.
    # Increment by 6 until we find a tunnel
    # If none is found, x will end with a value >= 24
    while True:
        a = ram[gardenDirtValues + x] & DirtMaskingBits[y]
        if a == 0:
            # If tunnel not present
            break

        a = x
        a = adc(a, 6)
        x = a

        # Using memory pointers in RAM to calculate size of gardenDirtValues
        # Is actually always 24
        # TODO: Maybe replace this with constant?
        if a >= duckGraphicPtrs - gardenDirtValues:
            break

    a = x
    a = sbc(a, 6)

    if is_negative(a):
        done_vertical_blank()
        return

    x = a
    fill_in_tunnel(x, y)

    if x >= _4thGardenDirtValues - gardenDirtValues:
        # Filling bottom dirt row?
        y = byte_decrement(y)
        fill_in_tunnel(x, y)
        y = byte_increment(y)

    a = DirtMaskingBits[y]
    if is_negative(a) or a == 1:
        x = byte_increment(x)

    y = byte_increment(y)
    fill_in_tunnel(x, y)

    if x >= _4thGardenDirtValues - gardenDirtValues:
        # if filling bottom dirt row
        y = byte_increment(y)
        fill_in_tunnel(x, y)

    # Score increment for tunnel fill
    # x = <[FillTunnelAudioValues - AudioValues]
    set_game_audio_values((__FillTunnelAudioValues - __AudioValues) & 0xFF)

    a = POINTS_FILL_TUNNEL
    increment_score(a)

    # Fall through
    done_vertical_blank()


def done_vertical_blank():
    a = ram[gameState]

    if a < GS_PAUSE_GAME_STATE:
        check_for_reset_button_pressed()
        return

    if a == GS_WAIT_FOR_NEW_GAME:
        # After game over
        convert_bcd_to_digits()
        return

    if a >= GS_ALTERNATE_PLAYERS:
        check_for_reset_button_pressed()
        return

    # Fall through
    convert_bcd_to_digits()


def convert_bcd_to_digits():
    x = 2
    y = 8

    while True:
        a = ram[currentPlayerScore + x] & 0x0F  # lower nybbles
        # Multiply by 10
        a = a << 1
        ram[tmpMulti2] = a
        a = a << 1
        a = a << 1
        a = adc(a, ram[tmpMulti2])

        ram[digitGraphicPtrs + 2 + y] = a
        a = ram[currentPlayerScore + x] & 0xF0  # upper nybbles
        # Multiply by 10
        a = a >> 1
        ram[tmpMulti8] = a
        a = a >> 1
        a = a >> 1
        a = adc(a, ram[tmpMulti8])
        ram[digitGraphicPtrs + y] = a

        y = byte_decrement(y)
        y = byte_decrement(y)
        y = byte_decrement(y)
        y = byte_decrement(y)
        dec_result = byte_decrement(x)
        x = dec_result

        if is_positive(dec_result):
            continue

        a = __Blank_HIGH
        x = 0
        break

    while True:
        y = ram[digitGraphicPtrs + x]
        if y != 0:
            a = __NumberFonts_HIGH

        ram[digitGraphicPtrs + 1 + x] = a
        x = byte_increment(x)
        x = byte_increment(x)

        if x != 10:
            continue

        a = __NumberFonts_HIGH
        ram[digitGraphicPtrs + 11] = a
        break

    # Fall through
    check_for_reset_button_pressed()


# When pressing reset => resets whole game (which you want at the very start?)
def check_for_reset_button_pressed():
    a = swchb_value() & RESET_MASK

    if a != 0:
        # Reset not pressed
        display_kernel()
        return

    # Skip directly to GS_RESET_PLAYER_VARIABLES
    a = ram[gameSelection] & GAME_SELECTION_MASK
    ram[gameSelection] = a
    a = GS_RESET_PLAYER_VARIABLES
    ram[gameState] = a

    # Fall through?
    display_kernel()


def display_kernel():
    # No rendering for now!

    # Fall through
    overscan()


# == RENDERING OMITTED ==


def overscan():
    # Assembly sets up overscan timer, not needed for python

    # a = OVERSCAN_TIME
    # sta TIM64T

    """
    GameStateRoutineTable
   .word DisplayCopyrightInformation - 1
   .word AdvanceGameStateAfterFrameCountExpire - 1
   .word DisplayCompanyInformation - 1
   .word AdvanceGameStateAfterFrameCountExpire - 1
   .word ResetPlayerVariables - 1
   .word DisplayGameSelection - 1
   .word AdvanceGameStateAfterFrameCountExpire - 1
   .word CheckToMoveFarmerHorizontally - 1
   .word CarrotStolenByGopher - 1
   .word WaitForDuckToAdvanceGameState - 1
   .word InitGameRoundData - 1
   .word CheckToAlternatePlayers - 1
   .word InitGameRoundData - 1
   .word DisplayPlayerNumberInformation - 1
   .word WaitForActionButtonToStartRound - 1
   .word WaitToStartNewGame - 1
    """

    # Using actual function with switch, instead of raw pointer table!

    #    lda gameState                    ; get current game state
    #    asl                              ; multiply by 2
    #    tay
    #    lda GameStateRoutineTable + 1,y
    #    pha                              ; push game state routine LSB to stack
    #    lda GameStateRoutineTable,y
    #    pha                              ; push game state routine MSB to stack
    #    rts                              ; jump to game state routine

    a = ram[gameState]

    # Calculate carry for random
    _, carry = shift_left_with_carry(a)

    if a == GS_DISPLAY_COPYRIGHT:  # 0
        display_copyright_information()
    elif a == GS_DISPLAY_COPYRIGHT_WAIT or a == GS_DISPLAY_COMPANY_WAIT or a == GS_PAUSE_GAME_STATE:  # 1, 3, 6
        advance_game_state_after_frame_count_expire()
    elif a == GS_DISPLAY_COMPANY:  # 2
        # Gets skipped usually
        display_company_information()
    elif a == GS_RESET_PLAYER_VARIABLES:  # 4
        reset_player_variables(carry)
    elif a == GS_DISPLAY_GAME_SELECTION:  # 5
        display_game_selection()
    elif a == GS_CHECK_FARMER_MOVEMENT:  # 7
        check_to_move_farmer_horizontally()
    elif a == GS_GOPHER_STOLE_CARROT:  # 8
        carrot_stolen_by_gopher(carry)
    elif a == GS_DUCK_WAIT:  # 9
        wait_for_duck_to_advance_game_state(carry)
    elif a == GS_INIT_GAME_FOR_ALTERNATE_PLAYER or a == GS_INIT_GAME_FOR_GAME_OVER:  # 10, 12
        init_game_round_data(carry)
    elif a == GS_ALTERNATE_PLAYERS:  # 11
        check_to_alternate_players(carry)
    elif a == GS_DISPLAY_PLAYER_NUMBER:  # 13
        display_player_number_information(carry)
    elif a == GS_PAUSE_FOR_ACTION_BUTTON:  # 14
        wait_for_action_button_to_start_round(carry)
    elif a == GS_WAIT_FOR_NEW_GAME:  # 15
        # After game over
        wait_to_start_new_game(carry)
    else:
        # Always JUMPS!
        assert False, "This should never be reached!"


def display_copyright_information():
    a = 12
    ram[tmpEndGraphicPtrIdx] = a
    a = __CopyrightLiteralSprites_HIGH
    ram[tmpDigitPointerMSB] = a

    y = __CopyrightLiteralSprites_LOW
    _, carry = set_digit_graphic_pointers(y)
    a = WAIT_TIME_DISPLAY_COPYRIGHT
    ram[frameCount] = a

    # Fall through
    reset_player_variables(carry)


def reset_player_variables(carry):
    a = 0
    x = 9

    while True:
        ram[playerInformationValues + x] = a
        x = byte_decrement(x)

        if not is_positive(x):
            break

    a = 7
    ram[carrotPattern] = a
    ram[reservedPlayerCarrotPattern] = a
    a = 15
    ram[initGopherChangeDirectionTimer] = a
    ram[reservedGopherChangeDirectionTimer] = a

    # Fall through
    init_game_round_data(carry)


def init_game_round_data(carry):
    a = __NullSprite_LOW
    ram[duckLeftGraphicPtrs] = a
    ram[duckRightGraphicPtrs] = a
    a = __NullSprite_HIGH
    ram[duckLeftGraphicPtrs + 1] = a
    ram[duckRightGraphicPtrs + 1] = a
    a = DISABLE_SEED
    ram[fallingSeedVertPos] = a
    a = __FarmerSprite_00_LOW
    ram[farmerGraphicPtrs] = a
    a = __FarmerSprite_00_HIGH
    ram[farmerGraphicPtrs + 1] = a
    a = __CarrotTopGraphics_LOW
    ram[carrotTopGraphicPtrs] = a
    a = __CarrotTopGraphics_HIGH
    ram[carrotTopGraphicPtrs + 1] = a
    a = __CarrotGraphics_LOW
    ram[carrotGraphicsPtrs] = a
    a = __CarrotGraphics_HIGH
    ram[carrotGraphicsPtrs + 1] = a
    a = __NullRunningGopher_LOW
    ram[zone00_GopherGraphicsPtrs] = a
    a = __NullRunningGopher_HIGH
    ram[zone00_GopherGraphicsPtrs + 1] = a
    a = __NullSprite_LOW
    ram[zone01_GopherGraphicsPtrs] = a
    a = __NullSprite_HIGH
    ram[zone01_GopherGraphicsPtrs + 1] = a
    a = __RunningGopher_00_LOW
    ram[zone02_GopherGraphicsPtrs] = a
    a = __RunningGopher_00_HIGH
    ram[zone02_GopherGraphicsPtrs + 1] = a
    a = MSBL_SIZE1 | DOUBLE_SIZE
    ram[gopherNUSIZValue] = a
    a = INIT_FARMER_HORIZ_POS
    ram[farmerHorizPos] = a
    a = COLOR_GARDEN_DIRT
    ram[COLUPF] = a
    a = INIT_GOPHER_HORIZ_POS
    # Note: Strangely no -4 adjustment to INIT_GOPHER_HORIZ_POS
    ram[gopherHorizPos] = a
    ram[duckHorizPos] = a
    a = ram[initGopherChangeDirectionTimer]
    ram[gopherChangeDirectionTimer] = a
    a = 0
    ram[gopherVertPos] = a
    ram[gopherReflectState] = a
    ram[heldSeedDecayingTimer] = a
    ram[duckAnimationRate] = a

    # Fall through
    init_garden_dirt_values(carry)


def init_garden_dirt_values(carry):
    # register values set from init_game_round_data
    a = 0
    x = 23

    while True:
        ram[gardenDirtValues + x] = a
        x = byte_decrement(x)

        if not is_positive(x):
            break

    ram[gopherTauntTimer] = a

    # Most likely making space for gopher init position
    a = 0xF0
    ram[_4thGardenDirtRightPF2] = a
    ram[_4thGardenDirtLeftPF0] = a

    # Set gopher initial random state
    a = ram[random] & 0x7F
    ram[gopherVertMovementValues] = a
    a = ram[random + 1] & (GOPHER_HORIZ_DIR_MASK | GOPHER_TUNNEL_TARGET_MASK)
    ram[gopherHorizMovementValues] = a

    # Jump
    advance_current_game_state(carry)


def display_company_information():
    # Gets skipped usually
    a = 12
    ram[tmpEndGraphicPtrIdx] = a
    a = __USGamesLiteral_HIGH
    ram[tmpDigitPointerMSB] = a
    y = __USGamesLiteral_LOW
    _, carry = set_digit_graphic_pointers(y)

    # Jump
    reset_player_variables(carry)


def wait_for_duck_to_advance_game_state(carry):
    a = ram[duckAnimationRate]

    if a != 0:
        done_advance_game_state_after_frame_count_expire(carry)
        return

    # Fall through
    advance_game_state_after_frame_count_expire()


def advance_game_state_after_frame_count_expire():
    a = ram[frameCount]

    carry = a >= 255
    if a != 255:
        done_advance_game_state_after_frame_count_expire(carry)
        return

    # Jump
    advance_current_game_state(carry)


def done_advance_game_state_after_frame_count_expire(carry):
    # Jump
    new_frame(carry)


def display_game_selection():
    a = 8
    ram[tmpEndGraphicPtrIdx] = a
    a = __GameSelectionLiteralSprites_HIGH
    ram[tmpDigitPointerMSB] = a
    y = __GameSelectionLiteralSprites_LOW
    x, _ = set_digit_graphic_pointers(y)

    a = __Blank_LOW
    ram[digitGraphicPtrs + x] = a
    a = __Blank_HIGH
    ram[digitGraphicPtrs + 1 + x] = a

    a = ram[gameSelection] & GAME_SELECTION_MASK
    a = a >> 1
    ram[tmpMulti2] = a
    a = a >> 1
    a = a >> 1
    a = adc(a, ram[tmpMulti2])
    a, carry = adc_with_carry(a, 10)
    ram[digitGraphicPtrs + 10] = a
    a = __NumberFonts_HIGH
    ram[digitGraphicPtrs + 11] = a
    a = swchb_value() & SELECT_MASK

    if a != 0:
        select_button_not_pressed(carry)
        return

    # Only done when game mode is changed
    a = ram[selectDebounce]
    if a != 0:
        done_display_game_selection(carry)
        return

    ram[gameSelection] = byte_increment(ram[gameSelection])
    a = ram[gameSelection] & GAME_SELECTION_MASK

    carry = a >= MAX_GAME_SELECTION + 1
    if a >= MAX_GAME_SELECTION + 1:
        a = 0
        ram[gameSelection] = a

    a = 0xFF
    ram[selectDebounce] = a

    # Fall through
    done_display_game_selection(carry)


def done_display_game_selection(carry):
    # Jump
    new_frame(carry)


def select_button_not_pressed(carry):
    a = 0
    ram[selectDebounce] = a
    a = intpt4_value()

    if is_negative(a):
        # action button not pressed
        done_display_game_selection(carry)
        return

    # x = <[StartingThemeAudioValues_00 - AudioValues]
    set_game_audio_values((__StartingThemeAudioValues_00 - __AudioValues) & 0xFF)
    # x = <[StartingThemeAudioValues_01 - AudioValues]
    set_game_audio_values((__StartingThemeAudioValues_01 - __AudioValues) & 0xFF)

    a = WAIT_TIME_GAME_START
    ram[frameCount] = a

    # Jump
    advance_current_game_state(carry)


def display_player_number_information(carry):
    a = ram[gameSelection] & 1

    if a == 0:
        # one player game
        done_display_player_number_information(carry)
        return

    # Two player game
    a = 10
    ram[tmpEndGraphicPtrIdx] = a
    a = __PlayerNumberLiteralSprites_HIGH
    ram[tmpDigitPointerMSB] = a
    y = __PlayerNumberLiteralSprites_LOW
    set_digit_graphic_pointers(y)
    a = ram[gameSelection] & ACTIVE_PLAYER_MASK
    x = a
    a = (__one - __NumberFonts) & 0xFF  # <[one - NumberFonts]

    carry = x >= PLAYER_TWO_ACTIVE
    if x == PLAYER_TWO_ACTIVE:
        a, carry = adc_with_carry(a, H_FONT)

    ram[digitGraphicPtrs + 10] = a
    a = __NumberFonts_HIGH
    ram[digitGraphicPtrs + 11] = a

    # Fall through
    done_display_player_number_information(carry)


def done_display_player_number_information(carry):
    # Jump
    advance_current_game_state(carry)


def check_to_move_farmer_horizontally():
    a = swcha_value()
    x = ram[gameSelection]

    if not is_positive(x):
        # Shift player 2 joystick values
        a = (a << 4) & 0xFF

    x = a

    # a & b00110000 -> 1 where left and right are
    a = a & flip_byte(MOVE_RIGHT & MOVE_LEFT)
    # => b00LR0000, where R or L is 0 if pressed

    if a == flip_byte(MOVE_RIGHT & MOVE_LEFT):  # b00110000
        # both left or right not pressed
        check_to_move_gopher()
        return

    a = x
    # a & b00010000
    a = a & flip_byte(MOVE_RIGHT)
    # => b000R000 where R is 0 if pressed

    if a != 0:
        # Move farmer right
        a = ram[farmerHorizPos]
        if a >= XMAX_FARMER:
            check_to_move_gopher()
            return

        ram[farmerHorizPos] = byte_increment(ram[farmerHorizPos])
    else:
        # Move farmer left
        a = ram[farmerHorizPos]

        if a < XMIN_FARMER:
            check_to_move_gopher()
            return
        else:
            ram[farmerHorizPos] = byte_decrement(ram[farmerHorizPos])

    # unconditional branch
    check_to_move_gopher()

    # Never reached


def check_to_move_gopher():
    a = ram[gopherTauntTimer]

    if a != 0:
        # Currently taunting
        done_check_to_move_gopher()
        return

    a = ram[gopherHorizMovementValues] & (GOPHER_CARROT_TARGET_MASK | GOPHER_TUNNEL_TARGET_MASK)
    x = a

    # Either carrot or tunnel target
    a = HorizontalTargetValues[x]
    # Get absolute distance
    a = sbc(a, ram[gopherHorizPos])
    if not is_positive(a):
        a = flip_byte(a)
        a = adc(a, 1)

    if a < 3:
        # Close enough to target
        determine_to_remove_carrot(x)
        return

    a = ram[gopherHorizMovementValues]
    if is_negative(a):
        # gopher travels to left
        move_gopher_left()
        return

    ram[gopherHorizPos] = byte_increment(ram[gopherHorizPos])
    ram[gopherHorizPos] = byte_increment(ram[gopherHorizPos])
    a = REFLECT
    ram[gopherReflectState] = a
    a = ram[gopherHorizPos]

    if a >= XMAX_GOPHER:
        wrap_gopher_to_left_side()
        return

    # Fall through
    done_check_to_move_gopher()


def done_check_to_move_gopher():
    # Jump
    check_for_farmer_bonking_gopher()


def wrap_gopher_to_left_side():
    a = XMIN_GOPHER
    ram[gopherHorizPos] = a
    # Jump
    check_for_farmer_bonking_gopher()


def move_gopher_left():
    ram[gopherHorizPos] = byte_decrement(ram[gopherHorizPos])
    ram[gopherHorizPos] = byte_decrement(ram[gopherHorizPos])
    a = NO_REFLECT
    ram[gopherReflectState] = a
    a = ram[gopherHorizPos]

    if a < XMIN_GOPHER:
        wrap_gopher_to_right_side()
        return

    # Jump
    check_for_farmer_bonking_gopher()


def wrap_gopher_to_right_side():
    a = XMAX_GOPHER
    ram[gopherHorizPos] = a

    # Jump
    check_for_farmer_bonking_gopher()


def determine_to_remove_carrot(x):
    a = ram[gopherVertPos]

    if a != VERT_POS_GOPHER_ABOVE_GROUND:
        move_gopher_vertically(x)
        return

    a = ram[gopherHorizMovementValues] & 3
    x = a
    a = 0
    carry = 1

    while True:
        a, carry = roll_left_with_carry(a, carry)
        x = byte_decrement(x)

        if not is_positive(x):
            break

    # Remove carrot
    a = flip_byte(a) & ram[carrotPattern]
    ram[carrotPattern] = a

    # Jump
    advance_current_game_state(carry)


def move_gopher_vertically(x):
    y = HorizontalTargetValues[x]
    a = ram[gopherReflectState]
    if a != 0:
        # If gopher is facing right
        y = byte_increment(y)

    ram[gopherHorizPos] = y
    a = ram[gopherVertMovementValues] & GOPHER_TARGET_MASK

    x = a
    a = ram[gopherVertPos]
    if a == GopherTargetVertPositions[x]:
        # Carry used by random
        carry = 1 if a >= GopherTargetVertPositions[x] else 0
        gopher_reached_vertical_target(carry)
        return

    if a < GopherTargetVertPositions[x]:
        move_gopher_up()
        return

    # Move down
    ram[gopherVertPos] = byte_decrement(ram[gopherVertPos])

    # Fall through
    done_move_gopher_vertically()


def done_move_gopher_vertically():
    # Jump
    check_for_farmer_bonking_gopher()


def move_gopher_up():
    ram[gopherVertPos] = byte_increment(ram[gopherVertPos])
    a = ram[gopherVertPos]

    if a != VERT_POS_GOPHER_ABOVE_GROUND:
        done_move_gopher_vertically()
        return

    a = ram[gopherHorizPos]
    a = sbc(a, XMAX // 2)

    if is_negative(a):
        # On left half of screen
        determine_left_targeted_carrot()
        return

    a = (GOPHER_TRAVEL_LEFT | GOPHER_CARROT_TARGET)
    ram[gopherHorizMovementValues] = a
    a = ram[carrotPattern]

    a, carry = shift_right_with_carry(a)
    if carry:
        # right carrot present
        done_determine_targeted_carrot()
        return

    ram[gopherHorizMovementValues] = byte_increment(ram[gopherHorizMovementValues])

    a, carry = shift_right_with_carry(a)
    if carry:
        # center carrot present
        done_determine_targeted_carrot()
        return

    ram[gopherHorizMovementValues] = byte_increment(ram[gopherHorizMovementValues])

    # unconditional branch
    done_determine_targeted_carrot()


def determine_left_targeted_carrot():
    a = 10
    ram[gopherHorizMovementValues] = a
    a = ram[carrotPattern] & (1 << 2)  # left carrot value
    if a != 0:
        # left carrot
        done_determine_targeted_carrot()
        return

    ram[gopherHorizMovementValues] = byte_decrement(ram[gopherHorizMovementValues])

    a = ram[carrotPattern] & (1 << 1)  # center carrot value
    if a != 0:
        # left carrot
        done_determine_targeted_carrot()
        return

    ram[gopherHorizMovementValues] = byte_decrement(ram[gopherHorizMovementValues])

    # Fall through
    done_determine_targeted_carrot()


def done_determine_targeted_carrot():
    # Jump
    check_for_farmer_bonking_gopher()


def gopher_reached_vertical_target(carry):
    a = ram[gopherVertMovementValues] & GOPHER_TARGET_MASK

    # Targeting underground
    if a == 0:
        set_gopher_new_target_values(carry)
        return

    a = 0x80
    ram[gopherVertMovementValues] = a
    a = ram[gopherVertPos]

    if a != VERT_POS_GOPHER_ABOVE_GROUND - 1:
        check_for_farmer_bonking_gopher()
        return

    ram[gopherVertPos] = byte_decrement(ram[gopherVertPos])

    # Jump
    check_for_farmer_bonking_gopher()


def set_gopher_new_target_values(carry):
    next_random(carry)
    a = ram[random]
    ram[gopherVertMovementValues] = a
    a = ram[random + 1] & (GOPHER_HORIZ_DIR_MASK | GOPHER_TUNNEL_TARGET_MASK)
    ram[gopherHorizMovementValues] = a
    a = ram[currentPlayerScore]

    if a != 0:
        very_smart_gopher()
        return

    a = swchb_value()
    x = ram[gameSelection]

    if not is_negative(x):
        # player two active
        # move bit 6 to bit 7 (player 2 difficulty to player 1 difficulty)
        a = a << 1

    a = a & 0x80  # & 0b10000000
    # => 0bP0000000, P = 1 if pro/A mode is activated.

    if is_positive(a):
        # P = 0, meaning amateur/B mode
        smart_gopher_setting()
        return

    # Fall through
    very_smart_gopher()


def very_smart_gopher():
    a = ram[farmerHorizPos]
    if a >= 80:
        a = ram[gopherHorizMovementValues] & flip_byte(GOPHER_TARGET_RIGHT_TUNNELS)
        ram[gopherHorizMovementValues] = a

        # Not unconditional branch. Line 1648
        # Is weird, since this means both left and right half of screen
        # code is executed

        if a != 0:
            smart_gopher_setting()
            return

    # gopher targets right half of screen
    a = ram[gopherHorizMovementValues] | GOPHER_TARGET_RIGHT_TUNNELS
    ram[gopherHorizMovementValues] = a

    # Fall through
    smart_gopher_setting()


def smart_gopher_setting():
    a = ram[gopherChangeDirectionTimer]

    if a != 0:
        decrement_gopher_change_direction_timer()
        return

    # Fall through
    reset_gopher_change_direction_timer()


def reset_gopher_change_direction_timer():
    a = ram[initGopherChangeDirectionTimer]
    ram[gopherChangeDirectionTimer] = a

    a = ram[gopherVertMovementValues] | 0x80
    ram[gopherVertMovementValues] = a

    # Unconditional branch
    check_for_farmer_bonking_gopher()
    return


def decrement_gopher_change_direction_timer():
    dec_result = byte_decrement(ram[gopherChangeDirectionTimer])
    ram[gopherChangeDirectionTimer] = dec_result

    if dec_result == 0:
        reset_gopher_change_direction_timer()
        # Can return, since reset gopher_change_direction_timer already jumps unconditionally!
        return

    a = ram[gopherVertMovementValues] & 0x7F
    ram[gopherVertMovementValues] = a

    # Fall through
    check_for_farmer_bonking_gopher()


def check_for_farmer_bonking_gopher():
    a = ram[farmerAnimationIdx]
    if a < 4:
        check_to_taunt_farmer()
        return

    a = ram[gopherVertPos]
    if a < VERT_POS_GOPHER_ABOVE_GROUND - 1:
        check_to_taunt_farmer()
        return

    # get absolute distance between farmerHorizPos and gopherHorizPos + 3
    a = ram[farmerHorizPos]
    a = sbc(a, ram[gopherHorizPos])
    a = sbc(a, 3)
    if not is_positive(a):
        a = flip_byte(a)
        a = adc(a, 1)

    if a >= 6:
        check_to_taunt_farmer()
        return

    # x = <[BonkGopherAudioValues - AudioValues]
    set_game_audio_values((__BonkGopherAudioValues - __AudioValues) & 0xFF)
    a = POINTS_BONK_GOPHER
    increment_score(a)

    # Reset gopher
    a = INIT_GOPHER_HORIZ_POS - 4
    ram[gopherHorizPos] = a
    a = ram[random] & (GOPHER_HORIZ_DIR_MASK | GOPHER_TUNNEL_TARGET_MASK)
    ram[gopherHorizMovementValues] = a
    a = 0
    ram[gopherVertMovementValues] = a
    ram[gopherVertPos] = a
    ram[gopherTauntTimer] = a

    # Fall through
    check_to_taunt_farmer()


def check_to_taunt_farmer():
    a = ram[gopherVertPos]
    carry = a >= VERT_POS_GOPHER_ABOVE_GROUND
    if a == VERT_POS_GOPHER_ABOVE_GROUND:
        disable_zone01_gopher_sprite(carry)
        return

    if a != VERT_POS_GOPHER_ABOVE_GROUND - 1:
        set_zone01_gopher_graphic_values()
        return

    a = ram[gopherTauntTimer]
    if a != 0:
        decrement_gopher_taunt_timer()
        return
    # x = <[GopherTauntAudioValues - AudioValues]
    set_game_audio_values((__GopherTauntAudioValues - __AudioValues) & 0xFF)

    a = 28
    ram[gopherTauntTimer] = a

    # Unconditional branch
    set_zone01_gopher_graphic_values()


def decrement_gopher_taunt_timer():
    ram[gopherTauntTimer] = byte_decrement(ram[gopherTauntTimer])
    a = ram[gopherTauntTimer]

    if a != 0:
        set_zone01_gopher_graphic_values()
        return

    ram[gopherTauntTimer] = a

    # Fall through
    set_zone01_gopher_graphic_values()


def set_zone01_gopher_graphic_values():
    a = ram[gopherVertPos]
    carry = a >= VERT_POS_GOPHER_UNDERGROUND + 7
    if a < VERT_POS_GOPHER_UNDERGROUND + 7:
        disable_zone01_gopher_sprite(carry)
        return

    a = (__RisingGopherSprite + H_RISING_GOPHER - 1) & 0xFF
    a, carry = sbc_with_carry(a, ram[gopherVertPos])
    ram[zone01_GopherGraphicsPtrs] = a

    # Jump
    determine_gopher_nusiz_value(carry)


def disable_zone01_gopher_sprite(carry):
    a = __NullSprite_LOW
    ram[zone01_GopherGraphicsPtrs] = a

    # Fall through
    determine_gopher_nusiz_value(carry)


def determine_gopher_nusiz_value(carry):
    x = ram[gopherVertPos]
    if x == 0:
        disable_zone00_gopher_sprite(carry)
        return

    carry = x >= VERT_POS_GOPHER_ABOVE_GROUND
    if x == VERT_POS_GOPHER_ABOVE_GROUND:
        initiate_gopher_running_above_ground(carry)
        return

    a = MSBL_SIZE1 | DOUBLE_SIZE
    if x < VERT_POS_GOPHER_UNDERGROUND + 7:
        set_zone00_gopher_graphic_values(a)
        return
    a = MSBL_SIZE1 | ONE_COPY

    # Fall through
    set_zone00_gopher_graphic_values(a)


def set_zone00_gopher_graphic_values(a):
    ram[gopherNUSIZValue] = a
    a = ram[zone01_GopherGraphicsPtrs]
    # In asm using:  adc #H_CARROT ; but that makes way less sense and has the same value
    a, carry = adc_with_carry(a, __NullRunningGopher - __NullSprite)

    ram[zone00_GopherGraphicsPtrs] = a
    a = ram[zone01_GopherGraphicsPtrs + 1]
    ram[zone00_GopherGraphicsPtrs + 1] = a

    # Jump
    set_zone02_gopher_graphic_values(carry)


def disable_zone00_gopher_sprite(carry):
    a = MSBL_SIZE1 | DOUBLE_SIZE
    ram[gopherNUSIZValue] = a
    a = __NullSprite_LOW
    ram[zone00_GopherGraphicsPtrs] = a
    a = __NullSprite_HIGH
    ram[zone00_GopherGraphicsPtrs + 1] = a

    # Jump
    set_zone02_gopher_graphic_values(carry)


def initiate_gopher_running_above_ground(carry):
    a = (__RunningGopher_00 - 1) & 0xFF
    ram[zone00_GopherGraphicsPtrs] = a
    a = __RunningGopher_00_HIGH
    ram[zone00_GopherGraphicsPtrs + 1] = a
    a = MSBL_SIZE1 | DOUBLE_SIZE
    ram[gopherNUSIZValue] = a

    # Fall through
    set_zone02_gopher_graphic_values(carry)


def set_zone02_gopher_graphic_values(carry):
    a = ram[gopherVertPos]
    if a == 0:
        initiate_gopher_running_underground(carry)
        return

    carry = a >= VERT_POS_GOPHER_UNDERGROUND + 7
    if a < VERT_POS_GOPHER_UNDERGROUND + 7:
        initiate_gopher_running_underground(carry)
        return

    carry = a >= VERT_POS_GOPHER_ABOVE_GROUND - 13
    if a >= VERT_POS_GOPHER_ABOVE_GROUND - 13:
        animate_taunting_gopher_section(carry)
        return

    a = MSBL_SIZE1 | ONE_COPY
    ram[gopherNUSIZValue] = a
    a = ram[zone01_GopherGraphicsPtrs]
    a, carry = sbc_with_carry(a, H_GROUND_KERNEL_SECTION)
    ram[zone02_GopherGraphicsPtrs] = a

    # Jump
    animate_taunting_gopher_subsection(carry)


def initiate_gopher_running_underground(carry):
    a = __RunningGopher_00_LOW
    ram[zone02_GopherGraphicsPtrs] = a
    a = __RunningGopher_00_HIGH
    ram[zone02_GopherGraphicsPtrs + 1] = a
    a = MSBL_SIZE1 | DOUBLE_SIZE
    ram[gopherNUSIZValue] = a

    # Jump
    animate_taunting_gopher_subsection(carry)


def animate_taunting_gopher_section(carry):
    a = __NullSprite_LOW
    ram[zone02_GopherGraphicsPtrs] = a
    a = __NullSprite_HIGH
    ram[zone02_GopherGraphicsPtrs + 1] = a

    # Fall through
    animate_taunting_gopher_subsection(carry)


def animate_taunting_gopher_subsection(carry):
    a = ram[gopherTauntTimer]
    if a == 0:
        set_gopher_crawling_animation(carry)
        return

    if a < 7 * 3:
        check_taunting_gopher_animation_stage02(a)
        return

    # Fall through
    set_taunt_gopher_sprite00()


def set_taunt_gopher_sprite00():
    a = __GopherTauntSprite_00_LOW
    ram[zone00_GopherGraphicsPtrs] = a
    a = __GopherTauntSprite_00_HIGH
    ram[zone00_GopherGraphicsPtrs + 1] = a

    determine_taunting_gopher_facing_direction()


def check_taunting_gopher_animation_stage02(a):
    if a < 7 * 2:
        taunting_gopher_animation_stage03(a)
        return

    # Fall through
    set_taunt_gopher_sprite01()


def set_taunt_gopher_sprite01():
    a = __GopherTauntSprite_01_LOW
    ram[zone00_GopherGraphicsPtrs] = a
    a = __GopherTauntSprite_01_HIGH
    ram[zone01_GopherGraphicsPtrs + 1] = a

    determine_taunting_gopher_facing_direction()


def taunting_gopher_animation_stage03(a):
    if a < 7:
        set_taunt_gopher_sprite01()
        return
    elif a >= 7:
        set_taunt_gopher_sprite00()
        return

    # Never reached


def determine_taunting_gopher_facing_direction():
    a = ram[gopherHorizPos]
    a, carry = sbc_with_carry(a, ram[farmerHorizPos])

    if carry == 1:
        face_taunting_gopher_left(carry)
        return

    a = ram[gopherHorizMovementValues]
    if is_positive(a):
        set_gopher_crawling_animation(carry)
        return

    a = a & flip_byte(GOPHER_HORIZ_DIR_MASK)
    ram[gopherHorizMovementValues] = a
    ram[gopherHorizPos] = byte_increment(ram[gopherHorizPos])
    a = REFLECT
    ram[gopherReflectState] = a

    # Jump
    set_gopher_crawling_animation(carry)


def face_taunting_gopher_left(carry):
    a = ram[gopherHorizMovementValues]
    if is_negative(a):
        set_gopher_crawling_animation(carry)
        return

    a = a | GOPHER_TRAVEL_LEFT
    ram[gopherHorizMovementValues] = a
    a = NO_REFLECT
    ram[gopherReflectState] = a
    ram[gopherHorizPos] = byte_decrement(ram[gopherHorizPos])

    # Fall through
    set_gopher_crawling_animation(carry)


def set_gopher_crawling_animation(carry):
    x = ram[gopherVertPos]
    if x != 0:
        # calculate carry for random
        carry = 1 if x >= VERT_POS_GOPHER_ABOVE_GROUND else 0

        if x != VERT_POS_GOPHER_ABOVE_GROUND:
            new_frame(carry)
            return

    a = ram[frameCount] & 3
    if a != 0:
        skip_gopher_animation_rate_flip(x, carry)
        return

    a = ram[gopherHorizAnimationRate]
    a = flip_byte(a)
    ram[gopherHorizAnimationRate] = a

    # Fall through
    check_to_animate_crawling_gopher(a, x, carry)


def check_to_animate_crawling_gopher(a, x, carry):
    if a == 0:
        new_frame(carry)
        return

    a = __RunningGopher_01_LOW

    # Calculate carry for random
    carry = x >= VERT_POS_GOPHER_UNDERGROUND

    if x != VERT_POS_GOPHER_UNDERGROUND:
        init_above_ground_running_gopher_sprite(a, carry)
        return

    ram[zone02_GopherGraphicsPtrs] = a

    # Fall through => Jump
    new_frame(carry)


def skip_gopher_animation_rate_flip(x, carry):
    a = ram[gopherHorizAnimationRate]
    # Jump
    check_to_animate_crawling_gopher(a, x, carry)


def init_above_ground_running_gopher_sprite(a, carry):
    ram[zone00_GopherGraphicsPtrs] = a

    # Unconditional branch
    new_frame(carry)


def carrot_stolen_by_gopher(carry):
    a = __NullSprite_LOW
    ram[zone02_GopherGraphicsPtrs] = a
    ram[zone01_GopherGraphicsPtrs] = a
    ram[zone00_GopherGraphicsPtrs] = a
    a = __NullSprite_HIGH
    ram[zone02_GopherGraphicsPtrs + 1] = a
    ram[zone01_GopherGraphicsPtrs + 1] = a
    ram[zone00_GopherGraphicsPtrs + 1] = a

    a = WAIT_TIME_CARROT_STOLEN
    ram[frameCount] = a
    # x = <[StolenCarrotAudioValues - AudioValues]

    set_game_audio_values((__StolenCarrotAudioValues - __AudioValues) & 0xFF)

    # Fall through => Jump
    advance_current_game_state(carry)


def wait_for_action_button_to_start_round(carry):
    a = ram[carrotPattern]
    if a == 0:
        # No carrots left
        advance_current_game_state(carry)
        return

    a = intpt4_value()
    x = ram[gameSelection]

    if not is_positive(x):
        # Player two?
        a = intpt5_value()

    a = a & ACTION_MASK
    if is_negative(a):
        # Not pressed
        new_frame(carry)
        return

    a = GS_CHECK_FARMER_MOVEMENT
    ram[gameState] = a

    # Jump
    new_frame(carry)


def wait_to_start_new_game(carry):
    # Really not sure why this exists
    # Best guess: Wait till music finished playing, to make sure player can not accidently skip game over screen
    x = ram[leftAudioIndexValue]
    a = AudioValues[x]
    if a != 0:
        decrement_current_game_state()
        return

    a = intpt4_value()

    if is_negative(a):
        # action button not pressed
        decrement_current_game_state()
        return

    a = 0
    x = 9

    # Fall through
    init_player_information_values(a, x, carry)


def init_player_information_values(a, x, carry):
    while True:
        ram[playerInformationValues + x] = a
        x = byte_decrement(x)
        if not is_positive(x):
            break

    a = 7
    ram[carrotPattern] = a
    ram[reservedPlayerCarrotPattern] = a
    a = 15
    ram[initGopherChangeDirectionTimer] = a
    ram[reservedGopherChangeDirectionTimer] = a
    a = ram[gameSelection] & GAME_SELECTION_MASK
    ram[gameSelection] = a
    a = WAIT_TIME_GAME_START
    ram[frameCount] = a
    a = GS_DISPLAY_GAME_SELECTION
    ram[gameState] = a
    # x = <[StartingThemeAudioValues_00 - AudioValues]
    set_game_audio_values((__StartingThemeAudioValues_00 - __AudioValues) & 0xFF)
    # x = #<[StartingThemeAudioValues_01 - AudioValues]
    set_game_audio_values((__StartingThemeAudioValues_01 - __AudioValues) & 0xFF)

    # Jump
    init_game_round_data(carry)


# Alternate players every 128 frames
# To show score after game ended (all carrots are gone for both players)
def decrement_current_game_state():
    a = ram[frameCount]
    carry = a >= 128
    if a != 128:
        new_frame(carry)
        return

    a = ram[gameSelection] & 1
    if a == 0:
        # One player game
        new_frame(carry)
        return

    ram[gameState] = byte_decrement(ram[gameState])

    # Jump
    alternate_players(carry)


def check_to_alternate_players(carry):
    a = ram[gameSelection] & 1
    if a == 0:
        # one player game
        check_for_game_over_state(carry)
        return

    a = ram[reservedPlayerCarrotPattern]
    if a != 0:
        alternate_players(carry)
        return

    # Fall through
    check_for_game_over_state(carry)


def check_for_game_over_state(carry):
    a = ram[carrotPattern]
    if a != 0:
        advance_current_game_state(carry)
        return

    # x = <[GameOverThemeAudioValues_00 - AudioValues]
    set_game_audio_values((__GameOverThemeAudioValues_00 - __AudioValues) & 0xFF)
    # x = <[GameOverThemeAudioValues_01 - AudioValues]
    set_game_audio_values((__GameOverThemeAudioValues_01 - __AudioValues) & 0xFF)

    a = GS_WAIT_FOR_NEW_GAME
    ram[gameState] = a

    # Unconditional branch
    new_frame(carry)


def alternate_players(carry):
    a = ram[gameSelection] & 1
    if a == 0:
        # one player game
        advance_current_game_state(carry)
        return

    a = ram[gameSelection]
    a = exclusive_or(a, ACTIVE_PLAYER_MASK)
    ram[gameSelection] = a
    x = 4

    while True:
        a = ram[currentPlayerInformation + x]
        ram[tmpCurrentPlayerData] = a
        a = ram[reservedPlayerInformation + x]
        ram[currentPlayerInformation + x] = a
        a = ram[tmpCurrentPlayerData]
        ram[reservedPlayerInformation + a] = a

        x = byte_decrement(x)

        if not is_positive(x):
            break

    # Fall through
    advance_current_game_state(carry)


def advance_current_game_state(carry):
    ram[gameState] = byte_increment(ram[gameState])

    # Fall through
    new_frame(carry)


def new_frame(carry):
    """
    .waitTime
   lda INTIM
   bne .waitTime
   lda #START_VERT_SYNC
   sta WSYNC                        ; wait for next scan line
   sta VSYNC                        ; start vertical sync (D1 = 1)
   lda #VSYNC_TIME
   sta TIM8T
.vsyncWaitTime
   lda INTIM
   bne .vsyncWaitTime
    """

    # vertical_blank()
    global has_hit_new_frame
    has_hit_new_frame = True
    global hit_new_frame_carry_status
    hit_new_frame_carry_status = carry


# Six digit display kernel omitted
# PositionObjectHorizontally omitted


def increment_score(a):
    # print("ADD SCORE!", byte_to_bcd_number(a + 1))
    # sed
    x = 2
    carry = 1

    # Fall through
    increment_score_submodule(a, x, carry)


def increment_score_submodule(a, x, carry):
    a, carry = adc_bcd_with_carry(a, ram[currentPlayerScore + x], carry)
    ram[currentPlayerScore + x] = a

    if carry == 0:
        done_increment_score()
        return

    if x == 2:
        check_to_decrement_gopher_direction_timer(x)
        return

    # Fall through
    increment_next_score_value(x)


def increment_next_score_value(x):
    carry = 1
    a = 1 - 1
    x = byte_decrement(x)
    if is_positive(x):
        increment_score_submodule(a, x, carry)
        return

    # Fall through
    done_increment_score()


def done_increment_score():
    # cld
    # rts
    pass


def check_to_decrement_gopher_direction_timer(x):
    a = ram[currentPlayerScore + 1] & 1
    if a != 0:
        check_to_launch_duck(x)
        return

    dec_result = byte_decrement(ram[initGopherChangeDirectionTimer])
    ram[initGopherChangeDirectionTimer] = dec_result
    if dec_result != 0:
        check_to_launch_duck(x)
        return

    ram[initGopherChangeDirectionTimer] = byte_increment(ram[initGopherChangeDirectionTimer])

    # Fall through
    check_to_launch_duck(x)


def check_to_launch_duck(x):
    a = ram[currentPlayerScore + 1] & 0x0F
    if a == 4:
        check_game_selection_for_duck(x)
        return

    if a != 9:
        increment_next_score_value(x)
        return

    # Fall through
    check_game_selection_for_duck(x)


def check_game_selection_for_duck(x):
    a = ram[gameSelection] & GAME_SELECTION_MASK

    if a >= 2:
        increment_next_score_value(x)
        return

    a = ram[carrotPattern]
    if a == 7:
        increment_next_score_value(x)
        return

    a = ram[fallingSeedVertPos]
    if is_positive(a):
        increment_next_score_value(x)
        return

    a = XMIN_DUCK
    y = ram[random]
    ram[duckAttributes] = y

    # => php push - Simulated with extra register, because it seems only y is relevant
    pushed_state = y

    if is_positive(y):
        init_duck_horizontal_position(a, x, y, pushed_state)
        return

    a = XMAX_DUCK

    # Fall through
    init_duck_horizontal_position(a, x, y, pushed_state)


def init_duck_horizontal_position(a, x, y, pushed_state):
    ram[duckHorizPos] = a
    a = XMIN_DUCK + 8

    # => plp pop - Simulated with extra register, because it seems only y is relevant
    if not is_positive(pushed_state):
        a = XMAX - 19

    ram[fallingSeedHorizPos] = a
    a = y & SEED_TARGET_HORIZ_POS_MASK  # duck attributes

    if a >= (XMAX + 1) // 8:
        init_duck_sprite_values(x)
        return

    a = ram[duckAttributes] & DUCK_HORIZ_DIR_MASK
    a = a | ((XMAX + 1) // 2)
    ram[duckAttributes] = a

    # Fall through
    init_duck_sprite_values(x)


def init_duck_sprite_values(x):
    a = INIT_DUCK_ANIMATION_RATE
    ram[duckAnimationRate] = a
    a = __DuckWingsStationaryGraphics_LOW
    ram[duckLeftGraphicPtrs] = a
    a = __DuckWingsStationaryGraphics_HIGH
    ram[duckLeftGraphicPtrs + 1] = a
    a = __DuckFaceGraphics_LOW
    ram[duckRightGraphicPtrs] = a
    a = __DuckFaceGraphics_HIGH
    ram[duckRightGraphicPtrs + 1] = a
    a = INIT_SEED_VERT_POS
    ram[fallingSeedVertPos] = a
    a = 0
    ram[heldSeedDecayingTimer] = a

    # Jump
    increment_next_score_value(x)


def next_random(carry: int):
    # print("next random with carry", carry)
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

    # rts: not necessary in python
    pass


def determine_dirt_floor_index(a):
    a = a >> 2
    y = a

    if a >= (XMAX + 1) // 8:
        # Carry always 1, because compare has a >= memory
        a, _ = sbc_with_carry(a, (XMAX + 1) // 8, carry_flag=1)

    x = 0

    while True:
        if y < LEFT_PF1_PIXEL_OFFSET:
            break
        x = byte_increment(x)
        if y < LEFT_PF2_PIXEL_OFFSET:
            break
        x = byte_increment(x)
        if y < RIGHT_PF0_PIXEL_OFFSET:
            break
        x = byte_increment(x)
        if y < RIGHT_PF1_PIXEL_OFFSET:
            break
        x = byte_increment(x)
        if y < RIGHT_PF2_PIXEL_OFFSET:
            break
        x = byte_increment(x)
        break

    y = a

    # rts
    return x, y


def set_game_audio_values(x):
    # Ignoring y.
    # This will lead to an incorrect value in tmpGameAudioSavedY, but thats fine
    # No other side-effects, as far as I understand

    # ram[tmpGameAudioSavedY] = y
    ram[audioChannelIndex] = byte_increment(ram[audioChannelIndex])
    a = 1 & ram[audioChannelIndex]
    y = a
    a = AudioValues[x]
    # sta AUDC0,y
    x = byte_increment(x)
    ram[audioIndexValues + y] = x
    # y = ram[tmpGameAudioSavedY]
    pass


def play_game_audio_sounds(carry):
    x = 1
    return play_game_audio_sounds_submodule(x, carry)


def play_game_audio_sounds_submodule(x, carry):
    a = ram[audioDurationValues + x]
    if a == 0:
        return check_to_play_next_audio_frequency(x, carry)

    ram[audioDurationValues + x] = byte_decrement(ram[audioDurationValues + x])

    # Fall through
    return next_audio_channel(x, carry)


def next_audio_channel(x, carry):
    x = byte_decrement(x)
    if is_positive(x):
        return play_game_audio_sounds_submodule(x, carry)

    # rts
    return carry


def check_to_play_next_audio_frequency(x, carry):
    y = ram[audioIndexValues + x]
    a = 8
    # sta AUDV0,x
    a = AudioValues[y]
    if a == 0:
        # sta AUC0,x
        # unconditional branch
        return next_audio_channel(x, carry)

    # sta AUDF0,x
    a = a & AUDIO_DURATION_MASK
    if not is_negative(a):
        a, carry = shift_right_with_carry(a)

    a, carry = shift_right_with_carry(a)
    a, carry = shift_right_with_carry(a)
    a, carry = shift_right_with_carry(a)
    y = byte_increment(y)
    # print("set audioIndexValues +", x, "=", y)
    ram[audioIndexValues + x] = y
    # print("set audioDurationValues +", x, "=", a)
    ram[audioDurationValues + x] = a

    # Jump
    return next_audio_channel(x, carry)


def set_digit_graphic_pointers(y):
    x = 0

    # Fall through
    return set_digit_graphic_pointers_submodule(x, y)


def set_digit_graphic_pointers_submodule(x, y):
    while True:
        a = y
        ram[digitGraphicPtrs + x] = a
        a, carry = adc_with_carry(a, H_FONT)
        y = a
        a = ram[tmpDigitPointerMSB]
        ram[digitGraphicPtrs + 1 + x] = a
        x = byte_increment(x)
        x = byte_increment(x)

        carry = x >= ram[tmpEndGraphicPtrIdx]
        if x == ram[tmpEndGraphicPtrIdx]:
            break

    # rts
    return x, carry


def fill_in_tunnel(x, y):
    a = DirtMaskingBits[y]
    a = flip_byte(a) & ram[gardenDirtValues + x]
    ram[gardenDirtValues + x] = a

    # rts


def swcha_value() -> int:
    """
    Bit 7: Player 1, Up (0 = pressed, 1 = not pressed)
    Bit 6: Player 1, Down (0 = pressed, 1 = not pressed)
    Bit 5: Player 1, Left (0 = pressed, 1 = not pressed)
    Bit 4: Player 1, Right (0 = pressed, 1 = not pressed)
    Bit 3: Player 2, Up (0 = pressed, 1 = not pressed)
    Bit 2: Player 2, Down (0 = pressed, 1 = not pressed)
    Bit 1: Player 2, Left (0 = pressed, 1 = not pressed)
    Bit 0: Player 2, Right (0 = pressed, 1 = not pressed)
    """
    return swcha_input


def swchb_value() -> int:
    """
    Bit 7: Port difficulty switch player 1 (0 = amateur/B, 1 = pro/A)
    Bit 6: Port difficulty switch player 2 (0 = amateur/B, 1 = pro/A)
    Bit 5: Not used
    Bit 4: Not used
    Bit 3: Color/BW switch (0 = BW, 1 = Color) => Not used by Gopher
    Bit 2: Not used
    Bit 1: SELECT button (0 = pressed, 1 = not pressed)
    Bit 0: RESET button (0 = pressed, 1 = not pressed)
    :return:
    """

    return swchb_input


# left player action button value
def intpt4_value() -> int:
    """
    Player 1 fire button
    0x80 (bit 7 set) means the button is NOT pressed
    0x00 (bit 7 clear) means the button is pressed
    :return:
    """
    return intpt4_input


#  right player action button value
def intpt5_value() -> int:
    """
    Player 2 fire button
    0x80 (bit 7 set) means the button is NOT pressed
    0x00 (bit 7 clear) means the button is pressed
    :return:
    """
    return intpt5_input

