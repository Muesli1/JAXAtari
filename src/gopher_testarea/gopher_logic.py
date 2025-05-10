# https://atariage.com/2600/programming/2600_101/docs/onestep.html
# http://www.6502.org/tutorials/6502opcodes.html#DFLAG
from enum import Enum

# https://www.randomterrain.com/atari-2600-memories-tutorial-andrew-davie-25.html

from byte_util import *

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
MAX_GAME_SELECTION = 3

# Game State values

GS_DISPLAY_COPYRIGHT = 0
GS_DISPLAY_COPYRIGHT_WAIT = 1
GS_DISPLAY_COMPANY = 2
GS_DISPLAY_COMPANY_WAIT = 3
GS_RESET_PLAYER_VARIABLES = 4
GS_DISPLAY_GAME_SELECTION = 5
GS_PAUSE_GAME_STATE = 6
GS_MAIN_GAME_LOOP = 7
GS_GOPHER_STOLE_CARROT = 8
GS_DUCK_WAIT = 9
GS_INIT_GAME_FOR_ALTERNATE_PLAYER = 10
GS_ALTERNATE_PLAYERS = 11
GS_INIT_GAME_FOR_GAME_OVER = 12
GS_DISPLAY_PLAYER_NUMBER = 13
GS_PAUSE_FOR_ACTION_BUTTON = 14
GS_WAIT_FOR_NEW_GAME = 15

# Duck constants

INIT_DUCK_ANIMATION_TIMER = 32
DUCK_ANIMATION_DOWN_WING = INIT_DUCK_ANIMATION_TIMER - 8
DUCK_ANIMATION_STATIONARY_WING = DUCK_ANIMATION_DOWN_WING - 8
DUCK_ANIMATION_UP_WING = DUCK_ANIMATION_STATIONARY_WING - 8

DUCK_HORIZ_DIR_MASK = 0b10000000  # Set, if moving left
SEED_TARGET_HORIZ_POS_MASK = 0b01111111

# Gopher constants

# 0b0000 1111 = Last 4 bits mean current vertical target. See GopherTargetVertPositions (0 meaning underground)
GOPHER_VERT_TARGET_MASK = 0x0F
# If set, does not change horizontal direction (check_to_change_gopher_horizontal_direction)
# Is set, when horizontal direction change timer reaches zero
# Also set, after digging a non-underground dirt
# Also set after reaching vertical target that was non-underground
# Checked, and set when "faking out"
GOPHER_VERT_LOCKED_BIT = 0b10000000
# Sets locked bit and target index to 8. (= VERT_POS_GOPHER_ABOVE_GROUND - 13). This helps "faking out" the player
GOPHER_VERT_FAKING_TARGET_MASK = 0x88  # 0b10001000

# 0b1000 0000 = First 1 bit means current direction of gopher, 1 = left, 0 = right
GOPHER_HORIZ_DIR_MASK = 0b10000000
# If set, the tunnel target mask is currently either 0, 1 or 2
GOPHER_CARROT_TARGET_BIT = 0b00001000
# Which tunnel to target (if carrot target bit is not set)
GOPHER_TUNNEL_TARGET_MASK = 0b00000111
# Which carrot is targeted (if carrot target bit is set)
GOPHER_CARROT_STEAL_MASK = 0b00000011
# If not set, can only target tunnel 0, 1, 2, 3 - otherwise only tunnel 0, 4, 5 (see HorizontalTargetValues)
GOPHER_TARGET_RIGHT_TUNNELS_BIT = 0b00000100

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
duckAnimationTimer = ds(1, "duckAnimationTimer")
fallingSeedHorizPos = ds(1, "fallingSeedHorizPos")
heldSeedDecayingTimer = ds(1, "heldSeedDecayingTimer")

# === ATARI / TIA CONSTANTS ===

# values for REFPx:
NO_REFLECT = 0b0000
REFLECT = 0b1000

# values for SWCHB
P1_DIFF_MASK = 0b10000000
P0_DIFF_MASK = 0b01000000
SELECT_MASK = 0b00000010
RESET_MASK = 0b00000001

# SWCHA joystick bits:
MOVE_RIGHT = 0b01111111
MOVE_LEFT = 0b10111111
ACTION_MASK = 1 << 7

# === ADDITIONAL MEMORY ADDRESSES ==


__AudioValues = 0xFD0A

__StartingThemeAudioValues_00 = 0xFD0A
__StartingThemeAudioValues_01 = 0xFD29
__BonkGopherAudioValues = 0xFD43
__GopherTauntAudioValues = 0xFD4A
__StolenCarrotAudioValues = 0xFD61
__DigTunnelAudioValues = 0xFD7A
__FillTunnelAudioValues = 0xFD7E
__DuckQuackingAudioValues = 0xFD84
__GameOverThemeAudioValues_00 = 0xFD8C
__GameOverThemeAudioValues_01 = 0xFD9F

# ================ DATA TABLES ========


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

VERT_POS_GOPHER_TAUNTING = VERT_POS_GOPHER_ABOVE_GROUND - 1
GopherTargetVertPositions = [
    VERT_POS_GOPHER_UNDERGROUND,
    VERT_POS_GOPHER_UNDERGROUND + 7,
    VERT_POS_GOPHER_UNDERGROUND + 14,
    VERT_POS_GOPHER_ABOVE_GROUND - 13,
    VERT_POS_GOPHER_TAUNTING,  # taunting
    VERT_POS_GOPHER_ABOVE_GROUND,  # stealing
    VERT_POS_GOPHER_UNDERGROUND + 7,
    VERT_POS_GOPHER_UNDERGROUND + 14,

    VERT_POS_GOPHER_ABOVE_GROUND - 13,
    VERT_POS_GOPHER_ABOVE_GROUND,  # stealing
    VERT_POS_GOPHER_TAUNTING,  # taunting
    VERT_POS_GOPHER_UNDERGROUND + 14,
    VERT_POS_GOPHER_ABOVE_GROUND - 13,
    VERT_POS_GOPHER_ABOVE_GROUND,  # stealing
    VERT_POS_GOPHER_TAUNTING,  # taunting
    VERT_POS_GOPHER_ABOVE_GROUND  # stealing
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

frame_log: list[str] = []
_debug_frame_number = -1


def log(*message):
    global frame_log
    frame_log.append(" ".join([str(piece) for piece in message]))


has_hit_new_frame = False
hit_new_frame_carry_status: int = 0


def set_debug_frame_number(value):
    global _debug_frame_number
    _debug_frame_number = value


def get_frame_log() -> list[str]:
    return frame_log


def clear_frame_log():
    frame_log.clear()


def get_has_hit_new_frame() -> bool:
    return has_hit_new_frame


def set_has_hit_new_frame(value: bool):
    global has_hit_new_frame
    has_hit_new_frame = value


def get_hit_new_frame_carry_status() -> hit_new_frame_carry_status:
    return hit_new_frame_carry_status


def get_ram() -> list[int]:
    return ram


def get_swcha_input() -> int:
    return swcha_input


def get_swchb_input() -> int:
    return swchb_input


def get_intpt4_input() -> int:
    return intpt4_input


def get_intpt5_input() -> int:
    return intpt5_input


def set_swcha_input(value):
    global swcha_input
    swcha_input = value


def set_swchb_input(value):
    global swchb_input
    swchb_input = value


def set_intpt4_input(value):
    global intpt4_input
    intpt4_input = value


def set_intpt5_input(value):
    global intpt5_input
    intpt5_input = value


# ================================ RENDER STATE =================================

class DuckWingRenderingState(Enum):
    DISABLED = 0
    STATIONARY = 1
    DOWN = 2
    UP = 3


class DuckFaceRenderingState(Enum):
    DISABLED = 0
    FACE = 1


class FarmerRenderingState(Enum):
    SPRITE_00 = 0
    SPRITE_01 = 1
    SPRITE_02 = 2


class GopherRenderingStateZone00(Enum):
    NULL_RUNNING = 0
    NULL_SPRITE = 1
    RISING_SPRITE_MATCHING = 2
    RUNNING_00 = 3
    RUNNING_01 = 4
    TAUNT_SPRITE_00 = 5
    TAUNT_SPRITE_01 = 6


class GopherRenderingStateZone01(Enum):
    NULL_SPRITE = 0
    RISING_SPRITE = 1


class GopherRenderingStateZone02(Enum):
    NULL_SPRITE = 0
    RUNNING_00 = 1
    RUNNING_01 = 2
    RISING_SPIRE_MATCHING = 3


class DigitGraphic(Enum):
    COPYRIGHT = 0
    COMPANY = 1
    GAME_SELECTION = 2
    PLAYER_NUMBER = 3


class RenderState:

    def __init__(self):
        super().__init__()
        self.duck_wings = DuckWingRenderingState.DISABLED
        self.duck_face = DuckFaceRenderingState.DISABLED
        self.farmer = FarmerRenderingState.SPRITE_00
        self.digit_graphic = DigitGraphic.COPYRIGHT

        self.gopher_rising_px_start = 0

        self.gopher_00 = GopherRenderingStateZone00.NULL_RUNNING
        self.gopher_01 = GopherRenderingStateZone01.NULL_SPRITE
        self.gopher_02 = GopherRenderingStateZone02.RUNNING_00


render_state = RenderState()


def get_render_state() -> RenderState:
    return render_state


# ================================ GAME LOGIC =================================

def start():
    for i in range(len(ram)):
        ram[i] = 0
    update_game_state()


def update_game(carry):
    # Increment frameCount
    ram[frameCount] = byte_increment(ram[frameCount])

    if flip_byte(swcha_value()) != 0:
        # Reset game idle timer on any joystick input
        ram[gameIdleTimer] = 0

    # If idled for too long, wait for joystick input
    if ram[gameIdleTimer] >= 128:
        return

    # Increase gameIdleTimer every 256 frames
    if ram[frameCount] == 0:
        ram[gameIdleTimer] += 1

    carry = play_game_audio(carry)
    next_random(carry)

    update_duck()
    update_seed()

    if ram[gameState] == GS_MAIN_GAME_LOOP:
        # When running main game loop
        update_gopher_digging()
        update_farmer()

    check_for_reset_button_pressed()
    update_game_state()


def update_duck():
    animation_timer = ram[duckAnimationTimer]

    if animation_timer == 0:
        disable_duck()
        return

    animation_timer -= 1

    if animation_timer == 0:
        ram[duckAnimationTimer] = INIT_DUCK_ANIMATION_TIMER
        render_state.duck_wings = DuckWingRenderingState.STATIONARY
    else:
        ram[duckAnimationTimer] = animation_timer

        if animation_timer == DUCK_ANIMATION_DOWN_WING:
            render_state.duck_wings = DuckWingRenderingState.DOWN
        elif animation_timer == DUCK_ANIMATION_STATIONARY_WING:
            render_state.duck_wings = DuckWingRenderingState.STATIONARY
        elif animation_timer == DUCK_ANIMATION_UP_WING:
            render_state.duck_wings = DuckWingRenderingState.UP

    # Quack
    if ram[frameCount] & 0x1F == 0:
        set_game_audio_values(__DuckQuackingAudioValues - __AudioValues)

    if is_msb_set(ram[duckAttributes]):
        # move left
        ram[duckHorizPos] -= 1
    else:
        # move right
        ram[duckHorizPos] += 1

    if ram[duckHorizPos] < XMIN_DUCK or ram[duckHorizPos] >= XMAX_DUCK:
        disable_duck()


def disable_duck():
    render_state.duck_wings = DuckWingRenderingState.DISABLED
    render_state.duck_face = DuckFaceRenderingState.DISABLED
    ram[duckAnimationTimer] = 0


def update_seed():
    if is_msb_set(ram[fallingSeedVertPos]):
        # No seed
        return

    if ram[heldSeedDecayingTimer] != 0:
        # Seed is held by farmer
        update_seed_held_by_farmer()
        return

    # Seed reached target position, either already falling or was just moved there by the duck
    if ram[duckAttributes] & SEED_TARGET_HORIZ_POS_MASK == ram[fallingSeedHorizPos]:
        update_falling_seed()
        return

    # Seed is still moving with duck
    if is_msb_set(ram[duckAttributes]):
        # Moving left
        ram[fallingSeedHorizPos] -= 1
    else:
        # Moving right
        ram[fallingSeedHorizPos] += 1


SEED_GROUND_LEVEL = 107
# Exclusive
SEED_MAX_CATCHING_Y = 87
# Inclusive
SEED_MIN_CATCHING_Y = 83


def update_falling_seed():
    # Seed falls down
    new_seed_y = ram[fallingSeedVertPos] + 1
    ram[fallingSeedVertPos] = new_seed_y

    if new_seed_y == SEED_GROUND_LEVEL:
        # Seed reached ground
        ram[fallingSeedVertPos] = DISABLE_SEED
    elif SEED_MIN_CATCHING_Y <= new_seed_y < SEED_MAX_CATCHING_Y and \
            abs(ram[fallingSeedHorizPos] - ram[farmerHorizPos]) < 5:
        # Caught seed!
        ram[heldSeedDecayingTimer] = INIT_DECAYING_TIMER_VALUE


def update_seed_held_by_farmer():
    # Move seed with farmer
    ram[fallingSeedHorizPos] = ram[farmerHorizPos]
    ram[heldSeedDecayingTimer] -= 1

    if ram[heldSeedDecayingTimer] == 0:
        # Seed decayed
        ram[fallingSeedVertPos] = DISABLE_SEED


def update_gopher_digging():
    # "Fake out" player more often if he has a high score
    if ram[currentPlayerScore] != 0:  # score >= 10,000
        if ram[gopherVertMovementValues] & (~GOPHER_VERT_LOCKED_BIT & 0xFF) == 0:
            ram[gopherVertMovementValues] |= GOPHER_VERT_FAKING_TARGET_MASK

    if ram[gopherVertPos] == VERT_POS_GOPHER_UNDERGROUND:
        # Underground tunnel
        # If facing right, add width value to dig to right
        gopher_digging(ram[gopherHorizPos] + (8 if ram[gopherReflectState] == REFLECT else 0))
    elif ram[gopherVertPos] != VERT_POS_GOPHER_ABOVE_GROUND:
        # Moving up or down currently, dig at tunnel target mask
        gopher_digging(HorizontalTargetValues[ram[gopherHorizMovementValues] & GOPHER_TUNNEL_TARGET_MASK])


y_offset_map = [_4thGardenDirtValues - gardenDirtValues]
for y in range(1, 7):
    y_offset_map.append(_3rdGardenDirtValues - gardenDirtValues)
for y in range(7, 14):
    y_offset_map.append(_2ndGardenDirtValues - gardenDirtValues)
for y in range(14, VERT_POS_GOPHER_ABOVE_GROUND):
    y_offset_map.append(_1stGardenDirtValues - gardenDirtValues)


def gopher_digging(x_pos):
    x_byte_offset, dirt_mask_index = calculate_x_dirt_memory_offset(x_pos)
    byte_offset = x_byte_offset + y_offset_map[ram[gopherVertPos]]

    if DirtMaskingBits[dirt_mask_index] & ram[gardenDirtValues + byte_offset] != 0:
        # Dirt already removed
        return

    # Set bit for removed dirt
    ram[gardenDirtValues + byte_offset] |= DirtMaskingBits[dirt_mask_index]

    set_game_audio_values(__DigTunnelAudioValues - __AudioValues)

    if ram[gopherVertPos] != VERT_POS_GOPHER_UNDERGROUND:
        # Up or down movement, removing adjacent dirt as well
        adjacent_dirt_mask = DirtMaskingBits[dirt_mask_index + 1]

        if is_negative(adjacent_dirt_mask) or adjacent_dirt_mask == 1:
            byte_offset += 1

        # Set bit for adjacent removed dirt
        ram[gardenDirtValues + byte_offset] |= adjacent_dirt_mask

    check_to_change_gopher_horizontal_direction()


def check_to_change_gopher_horizontal_direction():
    if (ram[gopherVertMovementValues] & GOPHER_VERT_LOCKED_BIT) != 0:
        # Is locked
        return

    ram[gopherChangeDirectionTimer] -= 1

    if ram[gopherChangeDirectionTimer] == 0:
        ram[gopherVertMovementValues] |= GOPHER_VERT_LOCKED_BIT
        ram[gopherChangeDirectionTimer] = ram[initGopherChangeDirectionTimer]
    elif ram[gopherVertPos] == VERT_POS_GOPHER_UNDERGROUND:
        # Flip direction
        ram[gopherHorizMovementValues] ^= GOPHER_HORIZ_DIR_MASK
    else:
        ram[gopherVertMovementValues] = GOPHER_VERT_LOCKED_BIT


def is_single_player_game():
    return ram[gameSelection] & 1 == 0


def is_second_player_active():
    return is_msb_set(ram[gameSelection])


def is_duck_enabled():
    return ram[gameSelection] & GAME_SELECTION_MASK < 2


def update_farmer():
    if ram[farmerAnimationIdx] != 0:
        # Currently in animation
        increment_farmer_animation_index()
        return

    action_button_state = (intpt5_value() if is_second_player_active() else intpt4_value()) & ACTION_MASK

    if action_button_state == 0:
        # Action button pressed
        if ram[actionButtonDebounce] != 0:
            # Action button held down, does not count
            # There has to be at least one not pressed frame until action button can be pressed again
            return

        ram[actionButtonDebounce] = 0xFF
        increment_farmer_animation_index()
    else:
        # Action button was not pressed
        ram[actionButtonDebounce] = 0


def increment_farmer_animation_index():
    next_animation_index = ram[farmerAnimationIdx] + 1
    ram[farmerAnimationIdx] = next_animation_index

    if next_animation_index == 8:
        ram[farmerAnimationIdx] = 0
        render_state.farmer = FarmerRenderingState.SPRITE_00

        # Actual action
        farmer_action()
    else:
        if next_animation_index == 2:
            render_state.farmer = FarmerRenderingState.SPRITE_01

        if next_animation_index == 4:
            render_state.farmer = FarmerRenderingState.SPRITE_02


# Carrot plating or hole filling
def farmer_action():
    carrot_or_hole_x_position = -1

    # Get hole / carrot that farmer is closer than 6 pixels to
    # Checks from 10 (inclusive) to 0 (inclusive)
    for x in reversed(range(10 + 1)):
        if abs((ram[farmerHorizPos] - 4) - HorizontalTargetValues[x]) < 6:
            carrot_or_hole_x_position = x
            break

    if carrot_or_hole_x_position == -1:
        return

    if carrot_or_hole_x_position < 8:
        # Only index 8, 9 and 10 are carrots.
        # The rest are tunnels/holes
        fill_tunnel(carrot_or_hole_x_position)
        return

    if ram[heldSeedDecayingTimer] == 0:
        # Farmer not holding seed
        return

    # Plant carrot
    # If carrot already existed at that spot, you wasted your seed :c
    ram[carrotPattern] = (1 << (carrot_or_hole_x_position - 8)) | ram[carrotPattern]
    # Disable seed
    ram[fallingSeedVertPos] = DISABLE_SEED
    ram[heldSeedDecayingTimer] = 0


def fill_tunnel(hole_idx):
    if ram[gopherVertPos] != VERT_POS_GOPHER_UNDERGROUND:
        # Above ground or climbing up/down
        # If targeting carrot (bit set), will be 8,9,10 - otherwise [0, 7]
        gopher_target_idx = ram[gopherHorizMovementValues] & (GOPHER_CARROT_TARGET_BIT | GOPHER_TUNNEL_TARGET_MASK)

        if HorizontalTargetValues[gopher_target_idx] == HorizontalTargetValues[hole_idx]:
            # Can not fill hole that is currently used for climbing
            return

    byte_offset, fill_mask_index = calculate_x_dirt_memory_offset(HorizontalTargetValues[hole_idx])

    # Try to find y-coordinate position to fill from top (0) to bottom (3) until we hit dirt
    first_dirt_y_pos = 4
    for y_pos in range(4):
        # Check if dirt exists
        dirt_bit = ram[gardenDirtValues + byte_offset + y_pos * 6] & DirtMaskingBits[fill_mask_index]
        if dirt_bit == 0:
            first_dirt_y_pos = y_pos
            break

    # Fill ground one above last found dirt
    target_fill_y_pos = first_dirt_y_pos - 1

    if target_fill_y_pos < 0:
        # Would be above ground
        return

    fill_byte_offset = byte_offset + target_fill_y_pos * 6
    fill_in_tunnel(fill_byte_offset, fill_mask_index)

    if target_fill_y_pos == 3:
        # Bottom row, fill one to the left
        fill_in_tunnel(fill_byte_offset, fill_mask_index - 1)

    if is_msb_set(DirtMaskingBits[fill_mask_index]) or DirtMaskingBits[fill_mask_index] == 1:
        # Check if leftmost or rightmost bit is set
        # Which means that we are the edge of a mask
        fill_byte_offset += 1

    fill_mask_index += 1
    fill_in_tunnel(fill_byte_offset, fill_mask_index)

    if target_fill_y_pos == 3:
        # Bottom row, fill one to the right
        fill_in_tunnel(fill_byte_offset, fill_mask_index + 1)

    # Score increment for tunnel fill
    set_game_audio_values(__FillTunnelAudioValues - __AudioValues)

    increment_score(POINTS_FILL_TUNNEL)


def fill_in_tunnel(byte_offset, mask_index):
    ram[gardenDirtValues + byte_offset] = flip_byte(DirtMaskingBits[mask_index]) & ram[gardenDirtValues + byte_offset]


# When pressing reset => resets whole game (which you want at the very start)
def check_for_reset_button_pressed():
    if swchb_value() & RESET_MASK == 0:
        # Reset button pressed
        # Reset currently active player
        ram[gameSelection] = ram[gameSelection] & GAME_SELECTION_MASK
        # Reset player variables as next game state
        ram[gameState] = GS_RESET_PLAYER_VARIABLES


def update_game_state():
    gs = ram[gameState]

    _, carry = shift_left_with_carry(gs)
    assert carry == 0

    if gs == GS_DISPLAY_COPYRIGHT:  # 0
        display_copyright_information()
    elif gs == GS_DISPLAY_COPYRIGHT_WAIT or gs == GS_DISPLAY_COMPANY_WAIT or gs == GS_PAUSE_GAME_STATE:  # 1, 3, 6
        advance_game_state_after_frame_count_expire()
    elif gs == GS_DISPLAY_COMPANY:  # 2
        # Gets skipped usually
        display_company_information()
    elif gs == GS_RESET_PLAYER_VARIABLES:  # 4
        reset_player_variables(carry=0)
    elif gs == GS_DISPLAY_GAME_SELECTION:  # 5
        display_game_selection()
    elif gs == GS_MAIN_GAME_LOOP:  # 7
        update_main_game_loop()
    elif gs == GS_GOPHER_STOLE_CARROT:  # 8
        carrot_stolen_by_gopher()
    elif gs == GS_DUCK_WAIT:  # 9
        wait_for_duck_to_advance_game_state()
    elif gs == GS_INIT_GAME_FOR_ALTERNATE_PLAYER or gs == GS_INIT_GAME_FOR_GAME_OVER:  # 10, 12
        init_game_round_data(carry=0)
    elif gs == GS_ALTERNATE_PLAYERS:  # 11
        check_to_alternate_players()
    elif gs == GS_DISPLAY_PLAYER_NUMBER:  # 13
        display_player_number_information()
    elif gs == GS_PAUSE_FOR_ACTION_BUTTON:  # 14
        wait_for_action_button_to_start_round()
    elif gs == GS_WAIT_FOR_NEW_GAME:  # 15
        # After game over
        wait_to_start_new_game()
    else:
        assert False, "This should never be reached!"


def display_copyright_information():
    render_state.digit_graphic = DigitGraphic.COPYRIGHT
    ram[frameCount] = WAIT_TIME_DISPLAY_COPYRIGHT
    reset_player_variables(carry=1)


def reset_player_variables(carry):
    for offset in range(10):
        ram[playerInformationValues + offset] = 0

    ram[carrotPattern] = 7
    ram[reservedPlayerCarrotPattern] = 7
    ram[initGopherChangeDirectionTimer] = 15
    ram[reservedGopherChangeDirectionTimer] = 15

    # Fall through
    init_game_round_data(carry)


def init_game_round_data(carry):
    render_state.duck_wings = DuckWingRenderingState.DISABLED
    render_state.duck_face = DuckFaceRenderingState.DISABLED
    ram[fallingSeedVertPos] = DISABLE_SEED
    render_state.farmer = FarmerRenderingState.SPRITE_00
    render_state.gopher_00 = GopherRenderingStateZone00.NULL_RUNNING
    render_state.gopher_01 = GopherRenderingStateZone01.NULL_SPRITE
    render_state.gopher_02 = GopherRenderingStateZone02.RUNNING_00

    ram[farmerHorizPos] = INIT_FARMER_HORIZ_POS
    # Note: Strangely no -4 adjustment to INIT_GOPHER_HORIZ_POS
    ram[gopherHorizPos] = INIT_GOPHER_HORIZ_POS
    ram[duckHorizPos] = INIT_GOPHER_HORIZ_POS
    ram[gopherChangeDirectionTimer] = ram[initGopherChangeDirectionTimer]
    ram[gopherVertPos] = 0
    ram[gopherReflectState] = 0
    ram[heldSeedDecayingTimer] = 0
    ram[duckAnimationTimer] = 0

    init_garden_dirt_values(carry)


def init_garden_dirt_values(carry):
    for offset in range(24):
        ram[gardenDirtValues + offset] = 0

    ram[gopherTauntTimer] = 0

    # Making space for gopher init position
    ram[_4thGardenDirtRightPF2] = 0xF0
    ram[_4thGardenDirtLeftPF0] = 0xF0

    # Set gopher initial random state
    ram[gopherVertMovementValues] = ram[random] & (~GOPHER_VERT_LOCKED_BIT & 0xFF)
    # Set random horizontal direction and target random tunnel (not carrot)
    ram[gopherHorizMovementValues] = ram[random + 1] & (GOPHER_HORIZ_DIR_MASK | GOPHER_TUNNEL_TARGET_MASK)

    advance_current_game_state(carry)


def display_company_information():
    render_state.digit_graphic = DigitGraphic.COMPANY
    reset_player_variables(carry=1)


def wait_for_duck_to_advance_game_state():
    a = ram[duckAnimationTimer]

    if a != 0:
        end_of_frame(carry=0)
        return

    advance_game_state_after_frame_count_expire()


def advance_game_state_after_frame_count_expire():
    if ram[frameCount] != 255:
        end_of_frame(carry=0)
        return

    advance_current_game_state(carry=1)


def display_game_selection():
    render_state.digit_graphic = DigitGraphic.GAME_SELECTION

    if swchb_value() & SELECT_MASK != 0:
        select_button_not_pressed()
        return

    if ram[selectDebounce] != 0:
        # Already pressed select last frame
        end_of_frame(carry=0)
        return

    carry = 1 if ram[gameSelection] == MAX_GAME_SELECTION else 0
    # Only allow game modes 0, 1, 2 or 3
    ram[gameSelection] = (ram[gameSelection] + 1) % (MAX_GAME_SELECTION + 1)
    ram[selectDebounce] = 0xFF

    end_of_frame(carry)


def select_button_not_pressed():
    ram[selectDebounce] = 0

    if is_negative(intpt4_value()):
        # action button not pressed
        end_of_frame(carry=0)
        return

    # Start game
    set_game_audio_values(__StartingThemeAudioValues_00 - __AudioValues)
    set_game_audio_values(__StartingThemeAudioValues_01 - __AudioValues)

    ram[frameCount] = WAIT_TIME_GAME_START

    advance_current_game_state(carry=0)


def display_player_number_information():
    if is_single_player_game():
        advance_current_game_state(carry=0)
        return

    render_state.digit_graphic = DigitGraphic.PLAYER_NUMBER
    advance_current_game_state(1 if is_second_player_active() else 0)


def update_main_game_loop():
    update_farmer_movement()
    can_be_bonked = update_gopher_movement()

    if can_be_bonked:
        check_for_farmer_bonking_gopher()
        update_gopher_taunt_logic()
        update_gopher_animation()


def update_farmer_movement():
    joystick_values = swcha_value()

    if is_second_player_active():
        # Shift player 2 joystick values
        joystick_values = (joystick_values << 4) & 0xFF

    if (joystick_values & flip_byte(MOVE_RIGHT & MOVE_LEFT)) == flip_byte(MOVE_RIGHT & MOVE_LEFT):
        # both left and right not pressed
        pass
    elif (joystick_values & flip_byte(MOVE_RIGHT)) != 0:
        # Move farmer right
        if ram[farmerHorizPos] < XMAX_FARMER:
            ram[farmerHorizPos] += 1
    else:
        # Move farmer left
        if ram[farmerHorizPos] >= XMIN_FARMER:
            ram[farmerHorizPos] -= 1


def update_gopher_movement() -> bool:
    if ram[gopherTauntTimer] != 0:
        # Currently taunting
        return True

    # Either carrot or tunnel target
    x_target_idx = ram[gopherHorizMovementValues] & (GOPHER_CARROT_TARGET_BIT | GOPHER_TUNNEL_TARGET_MASK)
    x_target = HorizontalTargetValues[x_target_idx]

    if abs(ram[gopherHorizPos] - x_target) < 3:
        # Close to target (moving up/down, steal carrot)
        return gopher_steal_carrot_or_move_vertically(x_target_idx)

    # Otherwise move left or right
    if (ram[gopherHorizMovementValues] & GOPHER_HORIZ_DIR_MASK) != 0:
        # Move left
        ram[gopherHorizPos] -= 2
        ram[gopherReflectState] = NO_REFLECT

        if ram[gopherHorizPos] < XMIN_GOPHER:
            ram[gopherHorizPos] = XMAX_GOPHER

    else:
        # Move right
        ram[gopherHorizPos] += 2
        ram[gopherReflectState] = REFLECT

        if ram[gopherHorizPos] >= XMAX_GOPHER:
            ram[gopherHorizPos] = XMIN_GOPHER

    return True


def gopher_steal_carrot_or_move_vertically(x) -> bool:
    if ram[gopherVertPos] != VERT_POS_GOPHER_ABOVE_GROUND:
        # Move up/down
        move_gopher_vertically(x)
        return True

    target_carrot = ram[gopherHorizMovementValues] & GOPHER_CARROT_STEAL_MASK
    assert target_carrot <= 2
    target_carrot_mask = 1 << target_carrot

    # Remove carrot
    ram[carrotPattern] = ~target_carrot_mask & ram[carrotPattern]

    advance_current_game_state(carry=0)
    return False  # The ONLY time bonking is not allowed/checked for


def move_gopher_vertically(x):
    target_x = HorizontalTargetValues[x]
    if ram[gopherReflectState] == REFLECT:
        # If gopher is facing right
        target_x += 1

    # "Stick" gopher to target position
    ram[gopherHorizPos] = target_x

    # Check if reached vertical target
    y_target = GopherTargetVertPositions[ram[gopherVertMovementValues] & GOPHER_VERT_TARGET_MASK]
    if ram[gopherVertPos] == y_target:
        gopher_reached_vertical_target()
        return

    if ram[gopherVertPos] < y_target:
        ram[gopherVertPos] += 1

        if ram[gopherVertPos] == VERT_POS_GOPHER_ABOVE_GROUND:
            # Moved above ground, target carrot!
            set_gopher_carrot_target()
    else:
        # Move down
        ram[gopherVertPos] -= 1


def set_gopher_carrot_target():
    if ram[gopherHorizPos] <= XMAX // 2:
        # On left half of screen

        # Moving right, and activate carrot targeting
        ram[gopherHorizMovementValues] = GOPHER_CARROT_TARGET_BIT

        # Select leftmost carrot
        if ram[carrotPattern] & (1 << 2) != 0:
            ram[gopherHorizMovementValues] += 2
        elif ram[carrotPattern] & (1 << 1) != 0:
            ram[gopherHorizMovementValues] += 1
        else:
            ram[gopherHorizMovementValues] += 0
    else:
        # Moving left, and activating carrot targeting
        ram[gopherHorizMovementValues] = GOPHER_HORIZ_DIR_MASK | GOPHER_CARROT_TARGET_BIT

        # Select rightmost carrot
        if ram[carrotPattern] & (1 << 0) != 0:
            ram[gopherHorizMovementValues] += 0
        elif ram[carrotPattern] & (1 << 1) != 0:
            ram[gopherHorizMovementValues] += 1
        else:
            ram[gopherHorizMovementValues] += 2


def gopher_reached_vertical_target():
    if ram[gopherVertMovementValues] & GOPHER_VERT_TARGET_MASK == VERT_POS_GOPHER_UNDERGROUND:
        # Reached bottom again, now deciding new target
        set_gopher_new_target_values()
        return

    ram[gopherVertMovementValues] = GOPHER_VERT_LOCKED_BIT

    if ram[gopherVertPos] == VERT_POS_GOPHER_TAUNTING:
        ram[gopherVertPos] -= 1


def set_gopher_new_target_values():
    next_random(carry=1)
    ram[gopherVertMovementValues] = ram[random]
    # Randomly choose facing direction and tunnel to target
    ram[gopherHorizMovementValues] = ram[random + 1] & (GOPHER_HORIZ_DIR_MASK | GOPHER_TUNNEL_TARGET_MASK)
    # gopherHorizMovementValues after this => 0bR000 0RRR

    # score >= 10,000
    # or difficulty switch set
    if ram[currentPlayerScore] != 0 or \
            is_msb_set(swchb_value() if is_second_player_active() else (swchb_value() << 1)):
        smart_gopher_tunnel_targeting()
        # gopherHorizMovementValues after this => Either 0bR000 01RR or 0bX000 00XX (where at least one X = 1)

    normal_gopher_logic()


def smart_gopher_tunnel_targeting():
    if ram[farmerHorizPos] >= 80:
        ram[gopherHorizMovementValues] = ram[gopherHorizMovementValues] & flip_byte(GOPHER_TARGET_RIGHT_TUNNELS_BIT)

    # Does not allow 0 target value, not sure why (would be tunnel 0) - maybe balancing?
    if ram[farmerHorizPos] < 80 or ram[gopherHorizMovementValues] == 0:
        ram[gopherHorizMovementValues] = ram[gopherHorizMovementValues] | GOPHER_TARGET_RIGHT_TUNNELS_BIT


def normal_gopher_logic():
    if ram[gopherChangeDirectionTimer] != 0:
        ram[gopherChangeDirectionTimer] -= 1
        ram[gopherVertMovementValues] = ram[gopherVertMovementValues] & 0x7F

    if ram[gopherChangeDirectionTimer] == 0:
        ram[gopherChangeDirectionTimer] = ram[initGopherChangeDirectionTimer]
        ram[gopherVertMovementValues] |= 0x80


def check_for_farmer_bonking_gopher():
    # Farmer currently not in last half of animation (>= 4)
    # or Gopher is lower than taunting position
    # or Farmer is too far away
    if ram[farmerAnimationIdx] < 4 or ram[gopherVertPos] < VERT_POS_GOPHER_TAUNTING \
            or abs(ram[farmerHorizPos] - (ram[gopherHorizPos] + 3)) >= 6:
        return

    # Bonked!
    set_game_audio_values(__BonkGopherAudioValues - __AudioValues)
    increment_score(POINTS_BONK_GOPHER)

    # Reset gopher
    ram[gopherHorizPos] = INIT_GOPHER_HORIZ_POS - 4
    # Set random new horizontal direction, and new tunnel (does not target carrot)
    ram[gopherHorizMovementValues] = ram[random] & (GOPHER_HORIZ_DIR_MASK | GOPHER_TUNNEL_TARGET_MASK)
    ram[gopherVertMovementValues] = 0
    ram[gopherVertPos] = 0
    ram[gopherTauntTimer] = 0


def update_gopher_taunt_logic():
    if ram[gopherVertPos] == VERT_POS_GOPHER_TAUNTING:
        if ram[gopherTauntTimer] != 0:
            ram[gopherTauntTimer] -= 1
        else:
            # Taunt for 28 frames
            set_game_audio_values(__GopherTauntAudioValues - __AudioValues)
            ram[gopherTauntTimer] = 28

    if ram[gopherTauntTimer] != 0:
        set_taunting_gopher_facing_direction()


def set_taunting_gopher_facing_direction():
    if ram[farmerHorizPos] <= ram[gopherHorizPos]:
        # If not already looking left
        if (ram[gopherHorizMovementValues] & GOPHER_HORIZ_DIR_MASK) == 0:
            ram[gopherHorizMovementValues] |= GOPHER_HORIZ_DIR_MASK
            ram[gopherReflectState] = NO_REFLECT
            ram[gopherHorizPos] -= 1
    else:
        # If not already looking right
        if (ram[gopherHorizMovementValues] & GOPHER_HORIZ_DIR_MASK) != 0:
            ram[gopherHorizMovementValues] &= flip_byte(GOPHER_HORIZ_DIR_MASK)
            ram[gopherHorizPos] += 1
            ram[gopherReflectState] = REFLECT


def update_gopher_animation():
    update_gopher_01_sprite()
    update_gopher_00_sprite()
    update_gopher_02_sprite()

    if ram[gopherTauntTimer] != 0:
        animate_taunting_gopher()

    carry = animate_crawling_gopher()
    end_of_frame(carry)


def update_gopher_01_sprite():
    y_pos = ram[gopherVertPos]

    if y_pos == VERT_POS_GOPHER_ABOVE_GROUND:
        render_state.gopher_01 = GopherRenderingStateZone01.NULL_SPRITE
    elif y_pos < VERT_POS_GOPHER_UNDERGROUND + 7:
        render_state.gopher_01 = GopherRenderingStateZone01.NULL_SPRITE
    else:
        render_state.gopher_01 = GopherRenderingStateZone01.RISING_SPRITE
        render_state.gopher_rising_px_start = y_pos  # [7, 34]


def update_gopher_00_sprite():
    if ram[gopherVertPos] == VERT_POS_GOPHER_UNDERGROUND:
        render_state.gopher_00 = GopherRenderingStateZone00.NULL_SPRITE
        return

    if ram[gopherVertPos] == VERT_POS_GOPHER_ABOVE_GROUND:
        render_state.gopher_00 = GopherRenderingStateZone00.RUNNING_00
        return

    if render_state.gopher_01 == GopherRenderingStateZone01.NULL_SPRITE:
        render_state.gopher_00 = GopherRenderingStateZone00.NULL_RUNNING
    elif render_state.gopher_01 == GopherRenderingStateZone01.RISING_SPRITE:
        render_state.gopher_00 = GopherRenderingStateZone00.RISING_SPRITE_MATCHING
    else:
        raise Exception(f"Unknown GopherRenderingStateZone01: {render_state.gopher_01}")

    # TODO: Understand this sprite logic
    # ram[zone00_GopherGraphicsPtrs] = ram[zone01_GopherGraphicsPtrs] + (__NullRunningGopher - __NullSprite)
    # ram[zone00_GopherGraphicsPtrs + 1] = ram[zone01_GopherGraphicsPtrs + 1]


def update_gopher_02_sprite():
    y_pos = ram[gopherVertPos]

    if y_pos == VERT_POS_GOPHER_UNDERGROUND:
        render_state.gopher_02 = GopherRenderingStateZone02.RUNNING_00
    elif y_pos < VERT_POS_GOPHER_UNDERGROUND + 7:
        render_state.gopher_02 = GopherRenderingStateZone02.RUNNING_00
    elif y_pos >= VERT_POS_GOPHER_ABOVE_GROUND - 13:
        render_state.gopher_02 = GopherRenderingStateZone02.NULL_SPRITE
    else:
        if render_state.gopher_01 == GopherRenderingStateZone01.NULL_SPRITE:
            raise Exception("Should never be the case")
        elif render_state.gopher_01 == GopherRenderingStateZone01.RISING_SPRITE:
            render_state.gopher_02 = GopherRenderingStateZone02.RISING_SPIRE_MATCHING
        else:
            raise Exception(f"Unknown gopher_01 sprite: {render_state.gopher_01}")


def animate_taunting_gopher():
    if ram[gopherTauntTimer] < 7:
        render_state.gopher_00 = GopherRenderingStateZone00.TAUNT_SPRITE_01
    elif ram[gopherTauntTimer] < 14:
        render_state.gopher_00 = GopherRenderingStateZone00.TAUNT_SPRITE_00
    elif ram[gopherTauntTimer] < 21:
        render_state.gopher_00 = GopherRenderingStateZone00.TAUNT_SPRITE_01
    else:
        render_state.gopher_00 = GopherRenderingStateZone00.TAUNT_SPRITE_00


def animate_crawling_gopher() -> int:
    y_pos = ram[gopherVertPos]

    # No crawling
    if y_pos != VERT_POS_GOPHER_UNDERGROUND and y_pos != VERT_POS_GOPHER_ABOVE_GROUND:
        assert y_pos < VERT_POS_GOPHER_ABOVE_GROUND
        return 0

    # Skip every 4 frames
    if (ram[frameCount] & 3) == 0:
        ram[gopherHorizAnimationRate] = flip_byte(ram[gopherHorizAnimationRate])

    if ram[gopherHorizAnimationRate] == 0:
        return 1 if y_pos != VERT_POS_GOPHER_UNDERGROUND else 0

    if y_pos != VERT_POS_GOPHER_UNDERGROUND:
        render_state.gopher_00 = GopherRenderingStateZone00.RUNNING_01
    else:
        render_state.gopher_02 = GopherRenderingStateZone02.RUNNING_01

    assert y_pos >= VERT_POS_GOPHER_UNDERGROUND
    return 1


def carrot_stolen_by_gopher():
    render_state.gopher_00 = GopherRenderingStateZone00.NULL_SPRITE
    render_state.gopher_01 = GopherRenderingStateZone01.NULL_SPRITE
    render_state.gopher_02 = GopherRenderingStateZone02.NULL_SPRITE

    ram[frameCount] = WAIT_TIME_CARROT_STOLEN
    set_game_audio_values(__StolenCarrotAudioValues - __AudioValues)
    advance_current_game_state(carry=0)


def wait_for_action_button_to_start_round():
    if ram[carrotPattern] == 0:
        # No carrots left
        advance_current_game_state(carry=0)
        return

    action_button = (intpt5_value() if is_second_player_active() else intpt4_value()) & ACTION_MASK
    if action_button == 0:
        # Pressed
        ram[gameState] = GS_MAIN_GAME_LOOP

    # Jump
    end_of_frame(carry=0)


def wait_to_start_new_game():
    # AudioValues? Really not sure why this exists
    # Best guess: Wait till music finished playing, to make sure player can not accidentally skip game over screen
    # Otherwise: if action button not pressed
    if AudioValues[leftAudioIndexValue] != 0 or (intpt4_value() & ACTION_MASK) != 0:
        decrement_current_game_state()
        return

    init_player_information_values()


def init_player_information_values():
    for offset in range(10):
        ram[playerInformationValues + offset] = 0

    ram[carrotPattern] = 7
    ram[reservedPlayerCarrotPattern] = 7
    ram[initGopherChangeDirectionTimer] = 15
    ram[reservedGopherChangeDirectionTimer] = 15
    # Remove current active player bit
    ram[gameSelection] &= GAME_SELECTION_MASK
    ram[frameCount] = WAIT_TIME_GAME_START
    ram[gameState] = GS_DISPLAY_GAME_SELECTION

    set_game_audio_values(__StartingThemeAudioValues_00 - __AudioValues)
    set_game_audio_values(__StartingThemeAudioValues_01 - __AudioValues)

    init_game_round_data(carry=0)


# Alternate players every 256 frames
# To show score after game ended (all carrots are gone for both players)
def decrement_current_game_state():
    carry = 1 if ram[frameCount] >= 128 else 0
    if ram[frameCount] != 128:
        end_of_frame(carry)
        return

    if is_single_player_game():
        end_of_frame(carry)
        return

    ram[gameState] -= 1
    alternate_player_information(carry)


def check_to_alternate_players():
    if is_single_player_game():
        check_for_game_over_state()
        return

    # If other player still has carrots, alternate them
    if ram[reservedPlayerCarrotPattern] != 0:
        alternate_player_information(carry=0)
        return

    # If both players are out of carrots, game over
    check_for_game_over_state()


def check_for_game_over_state():
    if ram[carrotPattern] != 0:
        advance_current_game_state(carry=0)
        return

    set_game_audio_values(__GameOverThemeAudioValues_00 - __AudioValues)
    set_game_audio_values(__GameOverThemeAudioValues_01 - __AudioValues)

    ram[gameState] = GS_WAIT_FOR_NEW_GAME
    end_of_frame(carry=0)


def alternate_player_information(carry):
    if not is_single_player_game():
        # Toggle active player bits
        ram[gameSelection] ^= ACTIVE_PLAYER_MASK

        for offset in range(4):
            temp = ram[currentPlayerInformation + offset]
            ram[currentPlayerInformation + offset] = ram[reservedPlayerInformation + offset]
            ram[reservedPlayerInformation + offset] = temp

    advance_current_game_state(carry)


def advance_current_game_state(carry):
    ram[gameState] += 1
    end_of_frame(carry)


def end_of_frame(carry):
    global has_hit_new_frame
    has_hit_new_frame = True
    global hit_new_frame_carry_status
    hit_new_frame_carry_status = carry


def increment_score(amount):
    for score_byte_offset in reversed(range(3)):
        new_byte_value, carry = adc_bcd_with_carry(amount, ram[currentPlayerScore + score_byte_offset], carry_flag=1)
        ram[currentPlayerScore + score_byte_offset] = new_byte_value

        if carry == 0:
            # No carry, meaning no further byte will be modified
            return

        if score_byte_offset == 2:
            # Will modify next 100 digit in next iteration
            check_to_decrement_gopher_direction_timer()
            check_to_spawn_duck()

        amount = 0


def check_to_decrement_gopher_direction_timer():
    # Check if 000X00 digit in score is even (0) or odd (1)
    if (ram[currentPlayerScore + 1] & 1) != 0:
        return

    # Decrement gopher change direction timer (making game harder)
    if ram[initGopherChangeDirectionTimer] > 1:
        ram[initGopherChangeDirectionTimer] -= 1


def check_to_spawn_duck():
    # Duck not enabled
    # or still full carrots
    # or seed (with / without duck) already visible
    if not is_duck_enabled() or ram[carrotPattern] == 7 or not is_msb_set(ram[fallingSeedVertPos]):
        return

    # Get 000X00 digit in score
    score_100_digit = ram[currentPlayerScore + 1] & 0x0F

    # Spawn duck if you went from a xxx4xx score to a xxx5xx score
    # or if you went from a xxx9xx score to a xxx0xx score
    if score_100_digit != 4 and score_100_digit != 9:
        return

    # Set duck attributes to random byte
    new_attributes = ram[random]
    ram[duckAttributes] = new_attributes

    # Spawn at left or right edge of screen
    duck_spawn_x = XMAX_DUCK if is_msb_set(new_attributes) else XMIN_DUCK
    # Spawn seed with specific offset to duck
    seed_spawn_x = XMAX - 19 if is_msb_set(new_attributes) else XMIN_DUCK + 8

    ram[duckHorizPos] = duck_spawn_x
    ram[fallingSeedHorizPos] = seed_spawn_x

    seed_target_pos = new_attributes & SEED_TARGET_HORIZ_POS_MASK

    # Farmer can only move from 20 to 148, so he can reach seeds in range [16, 152]
    # Max spawned seed position is 127 (because of max activated bits are 0b0111 1111)
    # Min spawned seed position is 0, but is now modified to 20
    if seed_target_pos < 20:
        # Move target farther to the right
        # Keep direction but overwrite rest with center seed position (position 79)
        ram[duckAttributes] = (ram[duckAttributes] & DUCK_HORIZ_DIR_MASK) | ((XMAX + 1) // 2)

    # Note: This means seeds will most likely drop in the very center
    #       Otherwise, seeds are more likely to spawn on the left side than the right side

    init_duck_state()


def init_duck_state():
    ram[duckAnimationTimer] = INIT_DUCK_ANIMATION_TIMER
    render_state.duck_wings = DuckWingRenderingState.STATIONARY
    render_state.duck_face = DuckFaceRenderingState.FACE

    ram[fallingSeedVertPos] = INIT_SEED_VERT_POS
    ram[heldSeedDecayingTimer] = 0


def next_random(carry: int):
    start_random_1 = ram[random + 1]
    start_random_0 = ram[random]

    ram[random], carry = roll_left_with_carry(ram[random], carry)
    ram[random + 1], carry = roll_left_with_carry(ram[random + 1], carry)

    ram[random], carry = adc_with_carry(ram[random], 195, carry)

    ram[random] = exclusive_or(start_random_0, ram[random])
    ram[random + 1] = exclusive_or(start_random_1, ram[random + 1])


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


def calculate_x_dirt_memory_offset(x_pos):
    return offset_map[x_pos // 4], (x_pos // 4) % 20


def set_game_audio_values(audio_offset):
    # Play audio on next audio channel
    ram[audioChannelIndex] = byte_increment(ram[audioChannelIndex])
    # Audio byte 0 is usually the audio generator type, while the rest are the actual sound bytes
    ram[audioIndexValues + (ram[audioChannelIndex] & 1)] = audio_offset + 1


def play_game_audio(carry):
    return play_game_audio_channel(1, carry)


def play_game_audio_channel(audio_channel_idx, carry):
    if ram[audioDurationValues + audio_channel_idx] == 0:
        return check_to_play_next_audio_frequency(audio_channel_idx, carry)

    ram[audioDurationValues + audio_channel_idx] -= 1
    return play_next_audio_channel(audio_channel_idx, carry)


def play_next_audio_channel(audio_channel_idx, carry):
    if audio_channel_idx > 0:
        return play_game_audio_channel(audio_channel_idx - 1, carry)

    return carry


def check_to_play_next_audio_frequency(audio_channel_idx, carry):
    audio_value = AudioValues[ram[audioIndexValues + audio_channel_idx]]
    if audio_value == 0:
        # End of audio
        return play_next_audio_channel(audio_channel_idx, carry)

    a = audio_value & AUDIO_DURATION_MASK

    shift_amount = 4 if is_positive(audio_value & AUDIO_DURATION_MASK) else 3

    a = a >> (shift_amount - 1)
    # Final shift with carry
    a, carry = shift_right_with_carry(a)

    ram[audioIndexValues + audio_channel_idx] += 1
    ram[audioDurationValues + audio_channel_idx] = a

    return play_next_audio_channel(audio_channel_idx, carry)


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
    Bit 6: Port difficulty switch player 0 (0 = amateur/B, 1 = pro/A)
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
