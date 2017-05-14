from sense_hat import SenseHat
from time import sleep
from collections import deque
import math

GRID_SIZE = 8
NUM_SAMPLES = 5
DELAY = 0.1

########## RGB COLOR CODES #########
VIOLET_RED = (199, 21, 133)
PINK = (100, 0, 0)
RED = (220, 20, 60)
DARK_RED = (140, 0, 40)

ORANGE_RED = (255, 69, 0)
TOMATO = (255, 99, 71)

LIGHT_YELLOW = (255, 255, 102)
GOLD = (255, 215, 0)
YELLOW_GREEN = (195, 215, 40)

ORANGE = (255, 165, 0)
DARK_ORANGE = (255, 140, 0)

LIME_GREEN = (51, 205, 50)
GREEN_YELLOW = (160, 215, 40)
GREEN = (0, 170, 0)
DARK_GREEN = (0, 100, 0)

DARK_CYAN = (0, 140, 140)
CYAN = (0, 255, 255)
BLUE = (0,191,255)
DARK_BLUE = (0, 0, 140)

BLUE_VIOLET = (138, 43, 226)
LIGHT_PURPLE = (186, 85, 211)
PURPLE = (130, 0, 130)
DARK_PURPLE = (100, 0, 100)
INDIGO = (75, 0, 130)

BLANK = (0, 0, 0)
WHITE = (255, 255, 255)

PITCH = [VIOLET_RED, RED, DARK_RED, BLANK, BLANK, DARK_PURPLE, PURPLE, LIGHT_PURPLE]
ROLL = [GREEN_YELLOW, GREEN, DARK_GREEN, BLANK, BLANK, DARK_ORANGE, ORANGE, GOLD]
YAW = [DARK_CYAN, CYAN, BLUE, DARK_BLUE]


# determine number corresponding to color index in list
def get_region(degrees, list_len):
    num_gradations = (list_len - 2) / 2

    # calculate region # based on number of visible segments
    if degrees < 90 or degrees <= 270:
        segment_size = 90 / num_gradations
        return int(degrees / segment_size)
    # only two blank segments, each 90 degrees
    elif degrees >= 90 and degrees < 180:
        return num_gradations + 1
    else:
        return num_gradations + 2


# simply divide into equal regions if all segments are visible
def get_region_all_visible(degrees, list_len):
    seg_size = 360 / list_len
    return degrees / seg_size


# pop old pixels and insert new values for left/right rotation
def shift_grid(grid, region, is_pitch):
    # shift away or left
    if (is_pitch and region <= len(PITCH) / 2) or (not is_pitch and region > (len(ROLL) + 2) / 2):
        direction = 0
    # shift towards or right
    else:
        direction = 1

    for i in range(GRID_SIZE):
        if direction == 0:
            grid[i].popleft()
            grid[i].append(ROLL[region])
        else:
            grid[i].pop()
            grid[i].appendleft(ROLL[region])

    return grid


def main():
    sense = SenseHat()
    sense.set_imu_config(False, True, True)
    sense.clear()

    grid = deque([deque([BLANK] * GRID_SIZE), deque([BLANK] * GRID_SIZE),
                  deque([BLANK] * GRID_SIZE), deque([BLANK] * GRID_SIZE),
                  deque([BLANK] * GRID_SIZE), deque([BLANK] * GRID_SIZE),
                  deque([BLANK] * GRID_SIZE), deque([BLANK] * GRID_SIZE)])

    left_ctr, right_ctr, toward_ctr, away_ctr = 0, 0, 0, 0

    while True:
        pitch_counts = [0] * len(PITCH)
        pitch_sums = [0] * len(PITCH)
        roll_counts = [0] * len(ROLL)
        roll_sums = [0] * len(ROLL)
        yaw_counts = [0] * len(YAW)
        yaw_sums = [0] * len(YAW)

        # take sample_size samples at sleep_time interval
        for i in range(NUM_SAMPLES):
            orient = sense.get_orientation()
            p, r, y = int(orient['pitch']), int(orient['roll']), int(orient['yaw'])

            # sum each value by region and tally the counts
            p_region = get_region(p, len(PITCH))
            r_region = get_region(r, len(ROLL))
            y_region = get_region_all_visible(y, len(YAW))

            pitch_counts[p_region] += 1
            pitch_sums[p_region] += p

            roll_counts[r_region] += 1
            roll_sums[r_region] += r

            yaw_counts[y_region] += 1
            yaw_sums[y_region] += y

        # get average value of highest frequency region for pitch
        pitch_count = max(pitch_counts)
        pitch_region = pitch_counts.index(pitch_count)
        pitch = pitch_sums[pitch_region] / pitch_count

        # get average value of highest frequency region for roll
        roll_count = max(roll_counts)
        roll_region = roll_counts.index(roll_count)
        roll = roll_sums[roll_region] / roll_count

        # get average value of highest frequency region for yaw
        yaw_count = max(yaw_counts)
        yaw_region = yaw_counts.index(yaw_count)
        yaw = yaw_sums[yaw_region] / yaw_count

        # determine whether pitch and roll are +10 degrees from the origin in either direction
        # and if so, which value is higher
        if pitch > 180:
            pitch = abs(pitch - 360)

        if roll > 180:
            roll = abs(roll - 360)

        # spin around y axis
        if pitch < 10 and roll < 10:
            sleep(.2)

        # tilt around z axis (left and right)
        elif pitch > roll:
            # increment pixel counter
            if pitch_region < (len(PITCH) - 2) // 2:
                left_ctr += 1
                right_ctr, toward_ctr, away_ctr = 0, 0, 0
            elif pitch_region >= (len(PITCH) - 1) // 2:
                right_ctr += 1
                left_ctr, toward_ctr, away_ctr = 0, 0, 0
            else:
                left_ctr, right_ctr, away_ctr, toward_ctr = 0, 0, 0, 0

            # if counter reaches/exceeds grid size, stop outputting color until direction changes
            if left_ctr >= GRID_SIZE or right_ctr >= GRID_SIZE:
                pitch_region = len(PITCH) // 2

            grid = shift_grid(grid, pitch_region, True)

        # tilt around x axis (toward and away)
        else:
            # increment and reset directional counters
            left_ctr, right_ctr = 0, 0

            if roll_region < (len(ROLL) - 2) // 2:
                 toward_ctr += 1
                 away_ctr = 0
            elif roll_region >= (len(ROLL) - 1) // 2:
                away_ctr += 1
                toward_ctr = 0
            else:
                away_ctr, toward_ctr = 0, 0

            # if counter reaches/exceeds grid size, stop outputting color until direction changes
            # by setting region equal to a non-visible segment
            if toward_ctr > GRID_SIZE or away_ctr > GRID_SIZE:
                roll_region = len(ROLL) // 2

            grid = shift_grid(grid, roll_region, False)

        # convert deques to a flattened list
        grid_list = []

        for row in grid:
            grid_list += list(row)

        sense.set_pixels(grid_list)


main()
