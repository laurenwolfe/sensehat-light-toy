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
BLUE = (0, 191, 255)
DARK_BLUE = (0, 0, 140)

BLUE_VIOLET = (138, 43, 226)
LIGHT_PURPLE = (186, 85, 211)
PURPLE = (130, 0, 130)
DARK_PURPLE = (100, 0, 100)
INDIGO = (75, 0, 130)

BLANK = (0, 0, 0)
WHITE = (255, 255, 255)

# PITCH = [VIOLET_RED, RED, DARK_RED, BLANK, BLANK, DARK_PURPLE, PURPLE, LIGHT_PURPLE]
# ROLL = [GREEN_YELLOW, GREEN, DARK_GREEN, BLANK, BLANK, DARK_ORANGE, ORANGE, GOLD]
PITCH = [RED, DARK_RED, BLANK, BLANK, DARK_BLUE, BLUE]
ROLL = [LIME_GREEN, DARK_GREEN, BLANK, BLANK, DARK_ORANGE, ORANGE]
YAW = [DARK_CYAN, CYAN, BLUE, DARK_BLUE]


# determine number corresponding to color index in list
def get_region(degrees, list_len):
    num_gradations = (list_len - 2) // 2

    # calculate region # based on number of visible segments
    if degrees < 90:
        segment_size = 90 / num_gradations
        return degrees // segment_size
    # only two blank segments, each 90 degrees
    elif degrees >= 270:
        # return a negative index
        degrees = abs(degrees - 360)
        segment_size = 90 / num_gradations
        return (degrees // segment_size) * -1
    elif degrees >= 90 and degrees < 180:
        return num_gradations + 1
    else:
        return num_gradations + 2


# simply divide into equal regions if all segments are visible
def get_region_all_visible(degrees, list_len):
    seg_size = 360 / list_len
    return int(degrees // seg_size)


# pop old pixels and insert new values for left/right rotation
def shift_grid(grid, region, is_pitch, color_list):
    if is_pitch:
        # LEFT
        if region < (len(color_list) - 1) // 2:
            for i in range(GRID_SIZE):
                grid[i].popleft()
                grid[i].append(color_list[region])

        # RIGHT
        else:
            for i in range(GRID_SIZE):
                grid[i].pop()
                grid[i].appendleft(color_list[region])
    else:
        # AWAY
        if region < (len(color_list) - 1) // 2:
            grid.popleft()
            grid.append(deque([color_list[region]] * GRID_SIZE))

        # TOWARD
        else:
            grid.pop()
            grid.appendleft(deque([color_list[region]] * GRID_SIZE))

    return grid


def main():
    sense = SenseHat()
    sense.set_imu_config(False, True, True)
    sense.clear()

    grid = deque([deque([BLANK] * GRID_SIZE)] * GRID_SIZE)

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

            # determine the region # by converting from degrees
            p_region = get_region(p, len(PITCH))
            r_region = get_region(r, len(ROLL))
            y_region = get_region_all_visible(y, len(YAW))

            if p_region < 0:
                p_region = len(PITCH) - p_region

            if r_region < 0:
                r_region = len(ROLL) - r_region

            # sum each value by region and tally the counts
            pitch_counts[p_region] += 1
            pitch_sums[p_region] += p

            roll_counts[r_region] += 1
            roll_sums[r_region] += r

            yaw_counts[y_region] += 1
            yaw_sums[y_region] += y

            print("pitch: {}, roll: {}".format(p, r))

        # get average value of highest frequency region for pitch
        pitch_count = max(pitch_counts)
        pitch_region = pitch_counts.index(pitch_count)
        avg_pitch = pitch_sums[pitch_region] / pitch_count

        # get average value of highest frequency region for roll
        roll_count = max(roll_counts)
        roll_region = roll_counts.index(roll_count)
        avg_roll = roll_sums[roll_region] / roll_count

        # get average value of highest frequency region for yaw
        yaw_count = max(yaw_counts)
        yaw_region = yaw_counts.index(yaw_count)
        yaw = yaw_sums[yaw_region] / yaw_count

        # determine whether pitch and roll are +10 degrees from the origin in either direction
        # and if so, which value is higher
        if avg_pitch >= 180:
            avg_pitch = abs(avg_pitch - 360)

        if avg_roll >= 180:
            avg_roll = abs(avg_roll - 360)

        # spin around y axis
        if avg_pitch < 0 and avg_roll < 0:
                sleep(.2)

        # tilt around z axis (left and right)
        elif avg_pitch > avg_roll:
            '''
            # increment / reset directional counters
            away_ctr, toward_ctr = 0, 0
            if pitch_region < (len(PITCH) - 2) // 2:
                left_ctr += 1
                right_ctr = 0
            elif pitch_region >= (len(PITCH) - 1) // 2:
                right_ctr += 1
                left_ctr = 0
            else:
                left_ctr, right_ctr = 0, 0

            # if counter reaches/exceeds grid size, stop outputting color until direction changes
            if left_ctr >= GRID_SIZE * 3 or right_ctr >= GRID_SIZE * 3:
                pitch_region = len(PITCH) // 2
            '''
            grid = shift_grid(grid, pitch_region, True, PITCH)

        # tilt around x axis (toward and away)
        else:
            '''
            # increment / reset directional counters
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
            if toward_ctr > GRID_SIZE * 3 or away_ctr > GRID_SIZE * 3:
                roll_region = len(ROLL) // 2
            '''
            grid = shift_grid(grid, roll_region, False, ROLL)

        # convert deques to a flattened list
        grid_list = []

        for row in grid:
            grid_list += list(row)

        sense.set_pixels(grid_list)


main()
