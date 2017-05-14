from sense_hat import SenseHat
from time import sleep
from collections import deque
from random import randint

# import math

GRID_SIZE = 8
MAX_PIXELS = GRID_SIZE * 3
NUM_SAMPLES = 5
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

VIOLET_RED = (199, 21, 133)
WHITE = (255, 255, 255)
ORANGE_RED = (255, 69, 0)
TOMATO = (255, 99, 71)
LIGHT_YELLOW = (255, 255, 102)
YELLOW_GREEN = (195, 215, 40)
GREEN_YELLOW = (160, 215, 40)
BLUE_VIOLET = (138, 43, 226)
INDIGO = (75, 0, 130)

PITCH = [PINK, RED, DARK_RED, BLANK, BLANK, DARK_PURPLE, PURPLE, LIGHT_PURPLE]
ROLL = [LIME_GREEN, GREEN, DARK_GREEN, BLANK, BLANK, DARK_ORANGE, ORANGE, GOLD]
YAW = [DARK_CYAN, CYAN, BLUE, DARK_BLUE]  # TODO replace
# FLAT = [DARK_CYAN, CYAN, BLUE, DARK_BLUE]
FLAT = [WHITE, INDIGO, TOMATO, CYAN, VIOLET_RED]


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


def overwrite_grid(grid, sense, color_list, total_rings):
    # store the steps out from center to set pixel ring
    left = (GRID_SIZE - 1) // 2
    right = GRID_SIZE // 2
    rings = deque([None] * (GRID_SIZE // 2))

    # while i < count
    # if count < MAX
    # - append new color to front of rings list
    # else:
    # - append blank
    # for el in rings:
    # if not None: overwrite pixels in grid corresponding to position:
    # - 3, 4; 2, 5; 1,6; 0, 7
    # push pixels to board

    color_idx = randint(0, len(color_list) - 1)

    tmp_left = left
    tmp_right = right

    for i in range(total_rings):
        # Haven't exceeded max pixel flow, add another color ring
        if i < MAX_PIXELS:
            rings.pop()
            rings.appendleft(color_list[color_idx])
            color_idx -= 1

            # wrap the list index if we reach 0
            if color_idx < 0:
                color_idx = len(color_list) - 1
        # Wipe rings away with blanks once max is acheived
        else:
            rings.pop()
            rings.appendleft(BLANK)

        idx = 0

        for el in rings:
            print("tmp_left: {}, tmp_right: {}, idx: {}".format(tmp_left, tmp_right, idx))
            if el is not None:
                edge = int(tmp_left + idx)
                grid[tmp_left][edge] = el
                grid[tmp_right][edge] = el
                grid[edge][tmp_left] = el
                grid[edge][tmp_right] = el

                print("({},{}), ({},{}), ({},{}), ({},{}),".
                      format(tmp_left, edge, tmp_right, edge, edge, tmp_left, edge, tmp_right))
            else:
                print("rings is None at index {}".format(idx))
            idx += 1
            tmp_left -= 1
            tmp_right += 1

            if tmp_left < 0:
                tmp_left = left
            if tmp_right >= GRID_SIZE:
                tmp_right = right

        print("exited grid insertion loop.")
        grid_list = []

        for row in grid:
            grid_list += list(row)

        sense.set_pixels(grid_list)
        sleep(.5)


    '''
    # if total rings exceeds the 50% of the maximum number of pixels released, then get a count of blank rings,
    # up to the maximum number of displayable rings
    num_blank_rings = total_rings - MAX_PIXELS

    if num_blank_rings > 0:
        num_color_rings = (total_rings % right) + 1
    elif num_blank_rings >= right:
        num_blank_rings = right
        num_color_rings = 0
    else:
        # calculate the total number of colored rings to display by subtracting blank rings and determining whether the
        # result is valid
        num_color_rings = total_rings % right
        num_blank_rings = right - num_color_rings

    # start index position for color list -- higher indices are "newer" and displayed in the center
    color_list_ptr = total_rings % len(color_list)

#    tmp_left = (GRID_SIZE - 1) // 2
#    tmp_right = GRID_SIZE // 2

    # output color rings
    for total in range(total_rings):
        for i in range(0, num_color_rings):
            while i < MAX_PIXELS:
                for step in range(right - left + 1):
                    grid[left][left + step] = color_list[color_list_ptr]
                    grid[right][left + step] = color_list[color_list_ptr]
                    grid[left + step][left] = color_list[color_list_ptr]
                    grid[left + step][right] = color_list[color_list_ptr]
                color_list_ptr -= 1
                left -= 1
                right += 1



    
    # output blank rings
    for i in range(0, num_blank_rings):
        for x in range(left - i, right + i + 1):
            for y in range(left - i, right + i + 1):
                print("blank - i: {}, x: {}, y: {}".format(i, x, y))
                grid[x][y] = BLANK

        if tmp_left < 0:
            tmp_left = left
        if tmp_right >= GRID_SIZE:
            tmp_right = right
        if color_list_ptr < 0:
            color_list_ptr = len(color_list) - 1

        idx = i % left

        if tmp_left < 0 or tmp_right >= GRID_SIZE:
            print("color overflowing")
            print("color overflowing")
            print("color overflowing")
        

        print("bounds - idx: {}, tmp_left: {}, tmp_right: {}, limit: {}".
              format(idx, tmp_left, tmp_right, num_color_rings))

        grid[(idx + tmp_left)][tmp_left] = color_list[color_list_ptr]
        grid[(idx + tmp_left)][tmp_right] = color_list[color_list_ptr]
        grid[tmp_left][(tmp_right - idx)] = color_list[color_list_ptr]
        grid[tmp_right][(tmp_left + idx)] = color_list[color_list_ptr]


        color_list_ptr -= 1
        tmp_left -= 1
        tmp_right += 1

        # output blank rings
     tmp_left = left
     tmp_right = right


    for i in range(0, min(num_blank_rings, right)):
        if tmp_left < 0 or tmp_right >= GRID_SIZE:
            print("blank overflowing")
            print("blank overflowing")
            print("blank overflowing")

        idx = i % left

        grid[idx + tmp_left][tmp_left] = BLANK
        grid[idx + tmp_left][tmp_right] = BLANK
        grid[tmp_left][tmp_left + idx] = BLANK
        grid[tmp_right][tmp_right - idx] = BLANK

        print("blank - i: {}, tmp_left: {}, tmp_right: {}, tmp_left + i: {}, tmp_right - i: {}".
              format(idx, tmp_left, tmp_right, tmp_left + idx, tmp_right - idx))

        tmp_left -= 1
        tmp_right += 1
        '''


def manage_flat_ctrs(ctrs, grid, sense):
    ctrs['flat'] += 1
    ctrs['away'], ctrs['toward'], ctrs['left'], ctrs['right'] = 0, 0, 0, 0

    overwrite_grid(grid, sense, FLAT, ctrs['flat'])


def manage_pitch_ctrs(ctrs, pitch_region, grid):
    # increment / reset directional counters
    ctrs['away'], ctrs['toward'], ctrs['flat'] = 0, 0, 0
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

    shift_grid(grid, pitch_region, True, PITCH)


def manage_roll_ctrs(ctrs, roll_region, grid):
    # reset counters of all other types -- roll is dominant sensor input
    ctrs['left'], ctrs['right'], ctrs['flat'] = 0, 0, 0

    # region count for tilting towards
    if roll_region < (len(ROLL) - 2) // 2:
        ctrs['toward'] += 1
        ctrs['away'] = 0
    # region count for tilting away
    elif roll_region >= (len(ROLL) - 1) // 2:
        ctrs['away'] += 1
        ctrs['toward'] = 0
    # in the blank zone between 90 -> 270, reset counters
    else:
        ctrs['away'], ctrs['toward'], = 0, 0

    # if counter reaches/exceeds maximum # of sequential pixels for a given direction, stop outputting
    # until direction changes by setting region equal to a non-visible segment.
    # the pixels fall off the screen in a downward direction.
    if ctrs['away'] > MAX_PIXELS:
        roll_region = len(ROLL) // 2
    elif ctrs['toward'] > MAX_PIXELS:
        roll_region = (len(ROLL) - 1) // 2

    shift_grid(grid, roll_region, False, ROLL)


def sample_sensor_output(sense):
    data = {}
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

        sleep(DELAY)

    # get average value of highest frequency region for pitch
    pitch_count = max(pitch_counts)
    data['pitch_region'] = pitch_counts.index(pitch_count)
    data['avg_pitch'] = pitch_sums[data['pitch_region']] / pitch_count

    # get average value of highest frequency region for roll
    roll_count = max(roll_counts)
    data['roll_region'] = roll_counts.index(roll_count)
    data['avg_roll'] = roll_sums[data['roll_region']] / roll_count

    # get average value of highest frequency region for yaw
    yaw_count = max(yaw_counts)
    data['yaw_region'] = yaw_counts.index(yaw_count)
    data['avg_yaw'] = yaw_sums[data['yaw_region']] / yaw_count

    return data


def main():
    sense = SenseHat()
    sense.set_imu_config(False, True, True)
    # sense.clear()

    grid = deque([deque([BLANK] * GRID_SIZE)] * GRID_SIZE)

    ctrs = {'left': 0, 'right': 0, 'toward': 0, 'away': 0, 'flat': 0}

    while True:
        # convert deques to a flattened list
        data = sample_sensor_output(sense)

        # determine whether pitch and roll are +10 degrees from the origin in either direction
        # and if so, which value is higher
        if data['avg_pitch'] >= 180:
            data['avg_pitch'] = abs(data['avg_pitch'] - 360)

        if data['avg_roll'] >= 180:
            data['avg_roll'] = abs(data['avg_roll'] - 360)

        # keep sensor parallel with the ground
        if data['avg_pitch'] < 15 and data['avg_roll'] < 15:
            print("ctrs: {}".format(ctrs['flat']))
            manage_flat_ctrs(ctrs, grid, sense)
        # tilt around z axis (left and right)
        else:
            if data['avg_pitch'] > data['avg_roll']:
                print("left: {}, right: {}".format(ctrs['left'], ctrs['right']))
                manage_pitch_ctrs(ctrs, data['pitch_region'], grid)
            # tilt around x axis (toward and away)
            else:
                print("toward: {}, away: {}".format(ctrs['toward'], ctrs['away']))
                manage_roll_ctrs(ctrs, data['roll_region'], grid)

            grid_list = []

            for row in grid:
                grid_list += list(row)

            sense.set_pixels(grid_list)

            sleep(.1)


main()
