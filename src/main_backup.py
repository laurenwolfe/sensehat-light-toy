from sense_hat import SenseHat
from time import sleep
from collections import deque
from enum import Enum

class Color(Enum):
    L_RED = (100, 0, 0)
    RED = (209, 0, 0)
    ORANGE = (255, 102, 34)
    YELLOW = (255, 118, 33)
    GREEN = (51, 221, 0)
    BLUE = (17, 51, 204)
    INDIGO = (34, 0, 102)
    VIOLET = (51, 0, 68)
    BLANK = (0, 0, 0)
    WHITE = (255, 255, 255)


GRID_SIZE = 8
SOFT_LEFT = SOFT_TOWARD = Color.VIOLET
HARD_LEFT = HARD_TOWARD = Color.RED
SOFT_RIGHT = SOFT_AWAY = Color.BLUE
HARD_RIGHT = HARD_AWAY = Color.GREEN
BLANK = Color.BLANK
NUM_SAMPLES = 10
DELAY = 0.05


def get_quad_45(num):
    if num < 45:
        return 0
    elif num >= 45 and num < 90:
        return 1
    elif num >= 90 and num < 180:
        return 2
    elif num >= 180 and num < 270:
        return 3
    elif num >= 270 and num < 315:
        return 4
    elif num >= 315:
        return 5


def get_quad_90(num):
    if num < 90:
        return 0
    elif num >= 90 and num < 180:
        return 1
    elif num >= 180 and num < 270:
        return 2
    elif num >= 270:
        return 3


# pop old pixels and insert new values for left/right rotation
def shift_pitch(grid, quad):
    # soft left, 0 -> 45
    if quad == 0:
        for i in range(GRID_SIZE):
            grid[i].popleft()
            grid[i].append(SOFT_LEFT)
    # hard left, 45 -> 90
    elif quad == 1:
        for i in range(GRID_SIZE):
            grid[i].popleft()
            grid[i].append(HARD_LEFT)
    # hard right, 270 -> 315
    elif quad == 2:
        for i in range(GRID_SIZE):
            grid[i].pop()
            grid[i].appendright(HARD_RIGHT)
    # soft right, 315 -> 360
    elif quad == 3:
        for i in range(GRID_SIZE):
            grid[i].pop()
            grid[i].appendright(SOFT_RIGHT)
    # too far left, 90 -> 180:
    elif quad == :
        for i in range(GRID_SIZE):
            grid[i].popleft()
            grid.append(BLANK)
    # too far right, 180 -> 270:
    else:
        for i in range(GRID_SIZE):
            grid[i].pop()
            grid[i].appendright(BLANK)

    return grid


def shift_roll(grid, quad):
    # soft towards
    if quad == 1:
        grid.pop()
        grid.appendleft(deque([SOFT_TOWARD] * GRID_SIZE))
    # hard towards
    elif quad == 2:
        grid.pop()
        grid.appendleft(deque([HARD_TOWARD] * GRID_SIZE))
    # hard away
    elif quad == 3:
        grid.popleft()
        grid.append(deque([HARD_AWAY] * GRID_SIZE))
    # soft away
    elif quad == 4:
        grid.popleft()
        grid.append(deque([SOFT_AWAY] * GRID_SIZE))
    # too hard away 180 -> 270
    elif quad == 5:
        grid.popleft()
        grid.append(deque([BLANK] * GRID_SIZE))
    # too hard towards 90 -> 180
    else:
        grid.pop()
        grid.appendleft(deque([BLANK] * GRID_SIZE))

    return grid


def main():
    sense = SenseHat()
    sense.set_imu_config(False, True, True)
    sense.clear()

    grid = deque([deque([Color.BLANK] * GRID_SIZE), deque([Color.BLANK] * GRID_SIZE),
                  deque([Color.BLANK] * GRID_SIZE), deque([Color.BLANK] * GRID_SIZE),
                  deque([Color.BLANK] * GRID_SIZE), deque([Color.BLANK] * GRID_SIZE),
                  deque([Color.BLANK] * GRID_SIZE), deque([Color.BLANK] * GRID_SIZE)])

    old_pitch, old_roll, seq_left, seq_right, seq_front, seq_back = 0, 0, 0, 0, 0, 0

    while True:
        ### quadrant values for pitch and roll:
        # 1 = 0 >= val > 45
        # 2 = 45 >= val > 90
        # 0 = 90 >= val > 180
        # 5 = 180 >= val > 270
        # 3 = 270 >= val > 315
        # 4 = 315 >= val >= 360
        pitch_counts = [0] * 6
        pitch_sums = [0] * 6
        roll_counts = [0] * 6
        roll_sums = [0] * 6

        ### quadrant values for yaw:
        #
        yaw_counts = [0] * 5
        yaw_sums = [0] * 5

        # take sample_size samples at sleep_time interval
        for i in range(NUM_SAMPLES):
            sleep(DELAY)
            orient = sense.get_orientation()

            p = orient['pitch']
            r = orient['roll']
            y = orient['yaw']

            pitch_counts[get_quad_45(p)] += 1
            pitch_sums[get_quad_45(p)] += p

            roll_counts[get_quad_45(r)] += 1
            roll_sums[get_quad_45(r)] += r

            yaw_counts[get_quad_90(y)] += 1
            yaw_sums[get_quad_90(y)] += y

        # get the average value for the max quadrant of each measure
        pitch_count = max(pitch_counts)
        pitch_quad = pitch_counts.index(pitch_count)
        pitch = pitch_sums[pitch_quad] / pitch_count

        roll_count = max(roll_counts)
        roll_quad = roll_counts.index(roll_count)
        roll = roll_sums[roll_quad] / roll_count

        yaw_count = max(yaw_counts)
        yaw_quad = yaw_counts.index(yaw_count)
        yaw = yaw_sums[yaw_quad] / yaw_count

        # determine whether pitch or roll has the largest delta
        if abs(pitch - old_pitch) >= abs(roll - old_roll):
            # shift horizontal pixels
            grid = shift_pitch(grid, pitch_quad)
        else:
            # shift vertical pixels
            grid = shift_roll(grid, roll_quad)


        #####turn on y axis
        #miniusb towards
        if yaw < 90:
            color = [Color.RED] * 64
        #miniusb left
        elif yaw >= 90 and yaw < 180:
            color = [Color.GREEN] * 64
        #miniusb away
        elif yaw >= 180 and yaw < 270:
            color = [Color.INDIGO] * 64
        #miniusb right
        else:
            color = [Color.YELLOW] * 64

        old_pitch = pitch
        old_roll = roll

        sleep(.2)
        sense.set_pixels(color)
