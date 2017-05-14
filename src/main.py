from sense_hat import SenseHat
from time import sleep
from collections import deque
# import math

GRID_SIZE = 8
MAX_PIXELS = GRID_SIZE * 3
NUM_SAMPLES = 10
DELAY = 0.1

# RGB COLOR CODES
PINK = (100, 0, 0)
RED = (220, 20, 60)
DARK_RED = (140, 0, 40)

GOLD = (255, 215, 0)
ORANGE = (255, 165, 0)
DARK_ORANGE = (255, 140, 0)

LIME_GREEN = (51, 205, 50)
GREEN = (0, 170, 0)
DARK_GREEN = (0, 100, 0)

DARK_CYAN = (0, 140, 140)
CYAN = (0, 255, 255)
BLUE = (0, 191, 255)
DARK_BLUE = (0, 0, 140)

LIGHT_PURPLE = (166, 65, 190)
PURPLE = (130, 0, 130)
DARK_PURPLE = (100, 0, 100)

BLANK = (0, 0, 0)

# VIOLET_RED = (199, 21, 133)
# WHITE = (255, 255, 255)
# ORANGE_RED = (255, 69, 0)
# TOMATO = (255, 99, 71)
# LIGHT_YELLOW = (255, 255, 102)
# YELLOW_GREEN = (195, 215, 40)
# GREEN_YELLOW = (160, 215, 40)
# BLUE_VIOLET = (138, 43, 226)
# INDIGO = (75, 0, 130)


PITCH = [PINK, RED, DARK_RED, BLANK, BLANK, DARK_PURPLE, PURPLE, LIGHT_PURPLE]
ROLL = [LIME_GREEN, GREEN, DARK_GREEN, BLANK, BLANK, DARK_ORANGE, ORANGE, GOLD]
YAW = [DARK_CYAN, CYAN, BLUE, DARK_BLUE]  # TODO replace
FLAT = [DARK_CYAN, CYAN, BLUE, DARK_BLUE]
# PITCH = [RED, DARK_RED, BLANK, BLANK, DARK_BLUE, BLUE]
# ROLL = [LIME_GREEN, DARK_GREEN, BLANK, BLANK, DARK_ORANGE, ORANGE]


# determine number corresponding to color index in list
def get_region(degrees, list_len):
    vis_segments = list_len - 2
    segment_size = 180 // vis_segments

    # calculate region # based on number of visible segments
    if degrees < 90:
        return degrees // segment_size

    # only two blank segments, each 90 degrees
    elif 90 <= degrees < 180:
        return (vis_segments // 2) + 1
    elif 180 <= degrees < 270:
        return (vis_segments // 2) + 2

    # upper region of values
    elif degrees >= 270:
        # How many segments to subtract from the top?
        degrees = abs(degrees - 360)
        return list_len - 1 - (degrees // segment_size)


# simply divide into equal regions if all segments are visible
def get_region_all_visible(degrees, list_len):
    seg_size = 360 / list_len
    return int(degrees // seg_size)


# pop old pixels and insert new values for left/right rotation
def shift_grid(grid, region, is_pitch, color_list):
    if is_pitch:
        # LEFT
        if region <= (len(color_list) - 1) // 2:
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
        if region <= (len(color_list) - 1) // 2:
            grid.pop()
            grid.appendleft(deque([color_list[region]] * GRID_SIZE))

        # TOWARD
        else:
            grid.popleft()
            grid.append(deque([color_list[region]] * GRID_SIZE))

    return grid


def overwrite_grid(sense, color_list, total_rings):
    # store the steps out from center to set pixel ring
    ctr = 0
    left = (len(color_list) - 1) // 2
    right = len(color_list) // 2

    # if total rings exceeds the 50% of the maximum number of pixels released, then get a count of blank rings,
    # up to the maximum number of displayable rings
    num_blank_rings = total_rings - MAX_PIXELS // 2
    if num_blank_rings < 0:
        num_blank_rings = 0
    elif num_blank_rings >= right:
        num_blank_rings = right

    # calculate the total number of colored rings to display by subtracting blank rings and determining whether the
    # result is valid
    num_color_rings = total_rings - num_blank_rings
    if num_color_rings < 0:
        num_color_rings = 0
    elif num_color_rings >= right:
        num_color_rings = right - num_blank_rings

    print("blank rings: {}, colored rings: {}".format(num_blank_rings, num_color_rings))

    # start index position for color list -- higher indices are "newer" and displayed in the center
    color_list_ptr = num_blank_rings + num_color_rings - 1

    # output blank rings
    for blank in range(0, num_blank_rings):
        for x in range(left, right):
            for y in range(left, right):
                sense.set_pixel(x, y, BLANK)
        ctr += 1
        left -= 1
        right += 1

    # output color rings
    for ring in range(num_blank_rings, min(num_blank_rings + num_color_rings, right)):
        for x in range(left, right):
            for y in range(left, right):
                sense.set_pixel(x, y, color_list[color_list_ptr])
        ctr += 1
        color_list_ptr -= 1
        left -= 1
        right += 1

        if color_list_ptr < 0:
            color_list_ptr = len(color_list) - 1

    sleep(DELAY)


def main():
    sense = SenseHat()
    sense.set_imu_config(False, True, True)
    sense.clear()

    grid = deque([deque([BLANK] * GRID_SIZE)] * GRID_SIZE)

    ctrs = {'left': 0, 'right': 0, 'toward': 0, 'away': 0, 'flat': 0}

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

            # sum each value by region and tally the counts
            pitch_counts[p_region] += 1
            pitch_sums[p_region] += p

            roll_counts[r_region] += 1
            roll_sums[r_region] += r

            yaw_counts[y_region] += 1
            yaw_sums[y_region] += y

        # get average value of highest frequency region for pitch
        pitch_count = max(pitch_counts)
        pitch_region = pitch_counts.index(pitch_count)
        avg_pitch = pitch_sums[pitch_region] / pitch_count

        # get average value of highest frequency region for roll
        roll_count = max(roll_counts)
        roll_region = roll_counts.index(roll_count)
        avg_roll = roll_sums[roll_region] / roll_count

        # get average value of highest frequency region for yaw
        # yaw_count = max(yaw_counts)
        # yaw_region = yaw_counts.index(yaw_count)
        # yaw = yaw_sums[yaw_region] / yaw_count

        # determine whether pitch and roll are +10 degrees from the origin in either direction
        # and if so, which value is higher
        if avg_pitch >= 180:
            avg_pitch = abs(avg_pitch - 360)

        if avg_roll >= 180:
            avg_roll = abs(avg_roll - 360)

        # spin around y axis
        if avg_pitch < 8 and avg_roll < 8:
            ctrs['flat'] += 1
            ctrs['away'], ctrs['toward'], ctrs['left'], ctrs['right'] = 0, 0, 0, 0

            overwrite_grid(sense, FLAT, ctrs['flat'])

        # tilt around z axis (left and right)
        elif avg_pitch > avg_roll:

            # increment / reset directional counters
            ctrs['away'], ctrs['toward'] = 0, 0
            if pitch_region < (len(PITCH) - 2) // 2:
                ctrs['left'] += 1
                ctrs['right'] = 0
            elif pitch_region >= (len(PITCH) - 1) // 2:
                ctrs['right'] += 1
                ctrs['left'] = 0
            else:
                ctrs['left'], ctrs['right'] = 0, 0

            # if counter reaches/exceeds grid size, stop outputting color until direction changes
            if ctrs['left'] >= MAX_PIXELS:
                pitch_region = (len(PITCH) - 1) // 2
            elif ctrs['right'] >= MAX_PIXELS:
                pitch_region = (len(PITCH)) // 2

            grid = shift_grid(grid, pitch_region, True, PITCH)

        # tilt around x axis (toward and away)
        else:
            # increment / reset directional counters
            ctrs['left'], ctrs['right'] = 0, 0
            if roll_region < (len(ROLL) - 2) // 2:
                ctrs['toward'] += 1
                ctrs['away'] = 0
            elif roll_region >= (len(ROLL) - 1) // 2:
                ctrs['away'] += 1
                ctrs['toward'] = 0
            else:
                ctrs['away'], ctrs['toward'] = 0, 0

            # if counter reaches/exceeds grid size, stop outputting color until direction changes
            # by setting region equal to a non-visible segment
            if ctrs['away'] > MAX_PIXELS:
                roll_region = len(ROLL) // 2
            elif ctrs['toward'] > MAX_PIXELS:
                roll_region = (len(ROLL) - 1) // 2

            grid = shift_grid(grid, roll_region, False, ROLL)

        # convert deques to a flattened list
        grid_list = []

        for row in grid:
            grid_list += list(row)

        sense.set_pixels(grid_list)
        sleep(.2)

main()
