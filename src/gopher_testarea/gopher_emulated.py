import ctypes
from multiprocessing import Process
from pathlib import Path
from multiprocessing import Manager

import numpy as np
from numpy.typing import NDArray
from ale_py import ALEInterface, roms, Action, LoggerMode

from byte_util import compare_ram_states
from chunked_writing_util import create_array_chunk_writer, load_array_pairs

import multiprocessing

import tqdm

ram_full_name_mapping = {
    0: 'gardenDirtValues+0 / _1stGardenDirtValues / _1stGardenDirtLeftPFValues / _1stGardenDirtLeftPF0',
    1: 'gardenDirtValues+1 / _1stGardenDirtLeftPF1', 2: 'gardenDirtValues+2 / _1stGardenDirtLeftPF2',
    3: 'gardenDirtValues+3 / _1stGardenDirtRightPFValues / _1stGardenDirtRightPF0',
    4: 'gardenDirtValues+4 / _1stGardenDirtRightPF1', 5: 'gardenDirtValues+5 / _1stGardenDirtRightPF2',
    6: 'gardenDirtValues+6 / _2ndGardenDirtValues / _2ndGardenDirtLeftPFValues / _2ndGardenDirtLeftPF0',
    7: 'gardenDirtValues+7 / _2ndGardenDirtLeftPF1', 8: 'gardenDirtValues+8 / _2ndGardenDirtLeftPF2',
    9: 'gardenDirtValues+9 / _2ndGardenDirtRightPFValues / _2ndGardenDirtRightPF0',
    10: 'gardenDirtValues+10 / _2ndGardenDirtRightPF1', 11: 'gardenDirtValues+11 / _2ndGardenDirtRightPF2',
    12: 'gardenDirtValues+12 / _3rdGardenDirtValues / _3rdGardenDirtLeftPFValues / _3rdGardenDirtLeftPF0',
    13: 'gardenDirtValues+13 / _3rdGardenDirtLeftPF1', 14: 'gardenDirtValues+14 / _3rdGardenDirtLeftPF2',
    15: 'gardenDirtValues+15 / _3rdGardenDirtRightPFValues / _3rdGardenDirtRightPF0',
    16: 'gardenDirtValues+16 / _3rdGardenDirtRightPF1', 17: 'gardenDirtValues+17 / _3rdGardenDirtRightPF2',
    18: 'gardenDirtValues+18 / _4thGardenDirtValues / _4thGardenDirtLeftPFValues / _4thGardenDirtLeftPF0',
    19: 'gardenDirtValues+19 / _4thGardenDirtLeftPF1', 20: 'gardenDirtValues+20 / _4thGardenDirtLeftPF2',
    21: 'gardenDirtValues+21 / _4thGardenDirtRightPFValues / _4thGardenDirtRightPF0',
    22: 'gardenDirtValues+22 / _4thGardenDirtRightPF1', 23: 'gardenDirtValues+23 / _4thGardenDirtRightPF2',
    24: 'duckGraphicPtrs+0 / duckLeftGraphicPtrs', 25: 'duckGraphicPtrs+1',
    26: 'duckGraphicPtrs+2 / duckRightGraphicPtrs', 27: 'duckGraphicPtrs+3', 28: 'duckHorizPos',
    29: 'farmerGraphicPtrs+0', 30: 'farmerGraphicPtrs+1', 31: 'farmerHorizPos', 32: 'carrotTopGraphicPtrs+0',
    33: 'carrotTopGraphicPtrs+1', 34: 'carrotGraphicsPtrs+0', 35: 'carrotGraphicsPtrs+1',
    36: 'displayingCarrotAttributes+0 / carrotCoarsePositionValue',
    37: 'displayingCarrotAttributes+1 / carrotHorizAdjustValue', 38: 'displayingCarrotAttributes+2 / carrotNUSIZValue',
    39: 'zone00_GopherGraphicsPtrs+0', 40: 'zone00_GopherGraphicsPtrs+1', 41: 'gopherHorizPos', 42: 'gopherNUSIZValue',
    43: 'zone01_GopherGraphicsPtrs+0', 44: 'zone01_GopherGraphicsPtrs+1', 45: 'zone02_GopherGraphicsPtrs+0',
    46: 'zone02_GopherGraphicsPtrs+1', 47: 'farmerAnimationIdx',
    48: 'playerInformationValues+0 / currentPlayerInformation / currentPlayerScore', 49: 'playerInformationValues+1',
    50: 'playerInformationValues+2', 51: 'playerInformationValues+3 / initGopherChangeDirectionTimer',
    52: 'playerInformationValues+4 / carrotPattern',
    53: 'playerInformationValues+5 / reservedPlayerInformation / reservedPlayerScore', 54: 'playerInformationValues+6',
    55: 'playerInformationValues+7', 56: 'playerInformationValues+8 / reservedGopherChangeDirectionTimer',
    57: 'playerInformationValues+9 / reservedPlayerCarrotPattern', 58: 'digitGraphicPtrs+0', 59: 'digitGraphicPtrs+1',
    60: 'digitGraphicPtrs+2', 61: 'digitGraphicPtrs+3', 62: 'digitGraphicPtrs+4', 63: 'digitGraphicPtrs+5',
    64: 'digitGraphicPtrs+6', 65: 'digitGraphicPtrs+7', 66: 'digitGraphicPtrs+8', 67: 'digitGraphicPtrs+9',
    68: 'digitGraphicPtrs+10', 69: 'digitGraphicPtrs+11', 70: 'actionButtonDebounce',
    71: 'tmpMulti2 / tmpMulti8 / tmpCurrentPlayerData / tmpEndGraphicPtrIdx / tmpDigitGraphicsColorValue / tmpCharHolder / tmpShovelHorizPos / tmpShovelVertTunnelIndex / tmpGardenDirtIndex',
    72: 'tmpSixDigitDisplayLoop / tmpDigitPointerMSB / tmpGameAudioSavedY', 73: 'random+0', 74: 'random+1',
    75: 'frameCount', 76: 'gameIdleTimer', 77: 'audioIndexValues+0 / leftAudioIndexValue',
    78: 'audioIndexValues+1 / rightAudioIndexValue', 79: 'audioDurationValues+0', 80: 'audioDurationValues+1',
    81: 'audioChannelIndex', 82: 'gameState', 83: 'gameSelection', 84: 'selectDebounce / gopherHorizAnimationRate',
    85: 'gopherVertPos', 86: 'gopherReflectState', 87: 'gopherHorizMovementValues', 88: 'gopherVertMovementValues',
    89: 'gopherChangeDirectionTimer', 90: 'gopherTauntTimer', 91: 'duckAttributes', 92: 'fallingSeedVertPos',
    93: 'fallingSeedScanline', 94: 'duckAnimationRate', 95: 'fallingSeedHorizPos', 96: 'heldSeedDecayingTimer',
    97: 'unused', 98: 'unused', 99: 'unused', 100: 'unused', 101: 'unused', 102: 'unused', 103: 'unused', 104: 'unused',
    105: 'unused', 106: 'unused', 107: 'unused', 108: 'unused', 109: 'unused', 110: 'unused', 111: 'unused',
    112: 'unused', 113: 'unused', 114: 'unused', 115: 'unused', 116: 'unused', 117: 'unused', 118: 'unused',
    119: 'unused', 120: 'unused', 121: 'unused', 122: 'unused', 123: 'unused', 124: 'unused', 125: 'unused',
    126: 'unused', 127: 'unused', 128: 'unused', 129: 'unused', 130: 'unused', 131: 'unused', 132: 'unused',
    133: 'unused', 134: 'unused', 135: 'unused', 136: 'unused', 137: 'unused', 138: 'unused', 139: 'unused',
    140: 'unused', 141: 'unused', 142: 'unused', 143: 'unused', 144: 'unused', 145: 'unused', 146: 'unused',
    147: 'unused', 148: 'unused', 149: 'unused', 150: 'unused', 151: 'unused', 152: 'unused', 153: 'unused',
    154: 'unused', 155: 'unused', 156: 'unused', 157: 'unused', 158: 'unused', 159: 'unused', 160: 'unused',
    161: 'unused', 162: 'unused', 163: 'unused', 164: 'unused', 165: 'unused', 166: 'unused', 167: 'unused',
    168: 'unused', 169: 'unused', 170: 'unused', 171: 'unused', 172: 'unused', 173: 'unused', 174: 'unused',
    175: 'unused', 176: 'unused', 177: 'unused', 178: 'unused', 179: 'unused', 180: 'unused', 181: 'unused',
    182: 'unused', 183: 'unused', 184: 'unused', 185: 'unused', 186: 'unused', 187: 'unused', 188: 'unused',
    189: 'unused', 190: 'unused', 191: 'unused', 192: 'unused', 193: 'unused', 194: 'unused', 195: 'unused',
    196: 'unused', 197: 'unused', 198: 'unused', 199: 'unused', 200: 'unused', 201: 'unused', 202: 'unused',
    203: 'unused', 204: 'unused', 205: 'unused', 206: 'unused', 207: 'unused', 208: 'unused', 209: 'unused',
    210: 'unused', 211: 'unused', 212: 'unused', 213: 'unused', 214: 'unused', 215: 'unused', 216: 'unused',
    217: 'unused', 218: 'unused', 219: 'unused', 220: 'unused', 221: 'unused', 222: 'unused', 223: 'unused',
    224: 'unused', 225: 'unused', 226: 'unused', 227: 'unused', 228: 'unused', 229: 'unused', 230: 'unused',
    231: 'unused', 232: 'unused', 233: 'unused', 234: 'unused', 235: 'unused', 236: 'unused', 237: 'unused',
    238: 'unused', 239: 'unused', 240: 'unused', 241: 'unused', 242: 'unused', 243: 'unused', 244: 'unused',
    245: 'unused', 246: 'unused', 247: 'unused', 248: 'unused', 249: 'unused', 250: 'unused', 251: 'unused',
    252: 'unused', 253: 'unused', 254: 'unused', 255: 'unused'}


def print_ram(ale, name: str, do_print=True):
    if do_print:
        print("#", hash(tuple(ale.getRAM().tolist())))
        print(name, "= [" + ", ".join([str(x) for x in ale.getRAM().tolist()]) + "]")

    save_or_check(ale, "init/" + name, 0)


def save_or_check(ale, name: str, action: int):
    frame_name = f"ram_states/{name}.npy"
    action_name = f"ram_states/{name}_action.npy"

    if Path(frame_name).exists() and Path(action_name).exists():
        loaded: NDArray = np.load(frame_name)
        loaded_action: NDArray = np.load(action_name)
        assert loaded.shape == ale.getRAM().shape, f"Inconsistent RAM shape {loaded.shape} vs {ale.getRAM().shape}"

        compare_ram_states(loaded.tolist(), ale.getRAM().tolist(), name, [], ram_full_name_mapping)
        assert np.array_equal(loaded,
                              ale.getRAM()), f"Inconsistent RAM state '{name}'!\n{loaded.tolist()}\n{ale.getRAM().tolist()}"
        assert loaded_action.item() == action, f"Inconsistent action '{name}! {loaded_action.item()} vs {action}"
    else:
        np.save(frame_name, ale.getRAM())
        np.save(action_name, np.asarray(action))


# id_start inclusive, id_end exclusive
def emulate(name: str, process_idx: int, id_start: int, id_end: int, chunk_size: int, queue: multiprocessing.Queue):
    ALEInterface.setLoggerMode(LoggerMode.Warning)
    ale = ALEInterface()
    ale.setInt("frame_skip", 1)
    ale.setFloat("repeat_action_probability", -1.0)
    ale.setInt("max_num_frames_per_episode", 0)

    ale.loadROM(roms.get_rom_path("gopher"))

    ale.setDifficulty(1)  # 0 or 1
    ale.setMode(0)  # 0 or 2

    # https://github.com/Farama-Foundation/Arcade-Learning-Environment/blob/d91b1016bd1f1ec6a3ec8a9a34c87dd77011e2a6/src/ale/games/supported/Gopher.cpp
    # https://github.com/Farama-Foundation/Arcade-Learning-Environment/blob/d91b1016bd1f1ec6a3ec8a9a34c87dd77011e2a6/src/ale/environment/stella_environment.cpp#L126

    # First 60 steps of NOP
    # Then softReset => m_num_reset_steps (=4) of RESET button step
    # "reset" function in GopherSettings
    # "setMode" function in GopherSettings => 2 x soft reset => 8 steps of RESET button + 6 more steps per SELECT change
    # Another softReset => m_num_reset_steps (=4) of RESET button step
    # Emulate starting action ("getStartingActions" in GopherSettings => PLAYER_A_FIRE) for one step each

    # NOTE:
    # "pressSelect" => setting select 5 times, then do ONE step with NOP

    # => 60 of NOP + 4 of RESET + 8 of RESET + 4 of RESET + 1 of PLAYER_A_FIRE
    # => 60 of NOP + 16 of RESET + 1 of PLAYER_A_FIRE

    # Brings game to first player input state
    def reset_game():
        ale.reset_game()
        if id_start == 0:
            print_ram(ale, "expected_ram_after_init", do_print=False)
        for i in range(238):
            ale.act(0)
        if id_start == 0:
            print_ram(ale, "expected_ram_before_start", do_print=False)
        ale.act(0)
        if id_start == 0:
            print_ram(ale, "expected_ram_after_start", do_print=False)

    reset_game()

    # print(ale.getMinimalActionSet())
    # [<Action.NOOP: 0>, <Action.FIRE: 1>, <Action.UP: 2>, <Action.RIGHT: 3>,
    # <Action.LEFT: 4>, <Action.UPFIRE: 10>, <Action.RIGHTFIRE: 11>,
    # <Action.LEFTFIRE: 12>]

    # actions = list(ale.getMinimalActionSet())

    valid_actions = [
        Action(0),  # NOOP
        Action(1),  # FIRE
        # Action(2), # UP
        Action(3),  # RIGHT
        Action(4),  # LEFT
        # Action(10), # UPFIRE
        Action(11),  # RIGHTFIRE
        Action(12)  # LEFTFIRE
    ]
    for action in valid_actions:
        assert action in ale.getMinimalActionSet()

    rng = np.random.default_rng(1025 + process_idx)
    # random_actions = rng.integers(0, len(valid_actions), size=chunk_size)

    write, close_writer = create_array_chunk_writer("ram_states/runs/" + name, f"ram_{process_idx}", chunk_size)

    curr = id_start
    i = 0
    while curr < id_end:
        random_action_idx = rng.integers(0, len(valid_actions))
        action = valid_actions[random_action_idx]
        reward = ale.act(action)
        write(ale.getRAM(), np.asarray(random_action_idx))

        if ale.game_over():
            # print("Reset game after frame", i + 1)
            curr += 1
            queue.put(1)
            reset_game()

        i += 1

    close_writer()


def get_chunk_indices(total_size, num_processors):
    """
    Generate chunk indices for parallel processing.

    Args:
        total_size (int): Total number of items to process
        num_processors (int): Number of available processors

    Returns:
        list: List of tuples (start_idx, end_idx) for each chunk
    """
    # Basic chunk size (floor division)
    chunk_size = total_size // num_processors

    # Calculate extra elements that need to be distributed
    extra_elements = total_size % num_processors

    chunks = []
    offset = 0

    for i in range(num_processors):
        start = offset
        # Add an extra element to earlier chunks if there are any extras
        extra = 1 if i < extra_elements else 0
        end = min(start + chunk_size + extra, total_size)

        # Only add chunk if there's work to do
        if end > start:
            chunks.append((start, end))

        offset = end

    return chunks


def counter_process(name: str, queue: multiprocessing.Queue, max: int):
    with tqdm.tqdm(total=max, desc=name) as pbar:
        while True:
            item = queue.get()
            if item is None:  # Sentinel value
                break

            pbar.update(1)


def run_with_multiple_processed(amount: int, name: str, file_chunk_size: int = 1_000_000):
    count_queue = Manager().Queue()
    # Start counter process
    counter = Process(target=counter_process, args=("Emulating games", count_queue, amount))
    counter.start()

    num_processes = multiprocessing.cpu_count()
    chunk_indices = get_chunk_indices(amount, num_processes)
    items = [(name, idx, i[0], i[1], file_chunk_size, count_queue) for (idx, i) in enumerate(chunk_indices)]

    with multiprocessing.Pool() as pool:
        pool.starmap(emulate, items)

    # Signal counter to finish and wait
    count_queue.put(None)  # Send sentinel value
    counter.join()


if __name__ == '__main__':
    run_with_multiple_processed(10_000, "random2")
