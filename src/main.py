from sense_hat import SenseHat
from time import sleep, strftime, tzset
from collections import deque
from random import randint
import os
import logging

# import math

WIDTH = 8
SIZE = WIDTH * WIDTH
MAX_PIXELS = WIDTH * 5
MAX_DEGREES = 360

# How much to increment/decrement to shift grid values to adjacent idx
LEFT_SHIFT = 1
RIGHT_SHIFT = -1
UP_SHIFT = -WIDTH
DOWN_SHIFT = WIDTH

NUM_SAMPLES = 10
DELAY = .02
PAUSE = .1

# RGB COLOR CODES
PINK = (100, 0, 15)
RED = (230, 15, 30)
DARK_RED = (130, 15, 30)
DARK_PURPLE = (100, 0, 100)
PURPLE = (130, 0, 130)
LIGHT_PURPLE = (166, 65, 190)
DARK_ORANGE = (180, 120, 0)
ORANGE = (220, 165, 0)
GOLD = (255, 215, 0)
LIME_GREEN = (51, 205, 50)
GREEN = (30, 170, 30)
DARK_GREEN = (0, 100, 0)
DARK_CYAN = (0, 140, 140)
M_CYAN = (0, 195, 195)
CYAN = (0, 255, 255)
BLUE = (0, 190, 255)
M_BLUE = (0, 100, 200)
MD_BLUE = (0, 70, 160)
DARK_BLUE = (0, 50, 140)
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
YAW = [WHITE, INDIGO, TOMATO, CYAN, VIOLET_RED]
FLAT = [DARK_CYAN, M_CYAN, CYAN, BLUE, M_BLUE, MD_BLUE, DARK_BLUE]


# determine number corresponding to color index in list
def get_region(degrees, list_len):
    vis_segments = list_len - 2
    segment_size = 200 // vis_segments

    # calculate region # based on number of visible segments
    if degrees < 100:
        return degrees // segment_size

    # only two blank segments, each 90 degrees
    elif 100 <= degrees < MAX_DEGREES/2:
        return (vis_segments // 2) + 1
    elif MAX_DEGREES/2 <= degrees < 260:
        return (vis_segments // 2) + 2

    # upper region of values
    elif degrees >= 260:
        # How many segments to subtract from the top?
        degrees = abs(degrees - 360)
        return list_len - 1 - (degrees // segment_size)


# simply divide into equal regions if all segments are visible
def get_region_all_visible(degrees, list_len):
    seg_size = MAX_DEGREES / list_len
    return int(degrees // seg_size)


def sample_sensor_output(sense):
    data = {}
    pitch_counts = [0] * len(PITCH)
    pitch_sums = [0] * len(PITCH)
    roll_counts = [0] * len(ROLL)
    roll_sums = [0] * len(ROLL)
    yaw_counts = [0] * len(YAW)
    yaw_sums = [0] * len(YAW)

    accel = sense.get_accelerometer_raw()
    print("x: %s, y: %s, z: %s" % (accel['x'], accel['y'], accel['z']))
    logging.warning("x: %s, y: %s, z: %s" % (accel['x'], accel['y'], accel['z']))

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


def overwrite_grid(grid, sense, color_list, ctrs, rings):
    # store the steps out from center to set pixel ring
    right = WIDTH // 2
    left = right - 1

    tmp_left = left
    tmp_right = right

    rings.pop()

    if ctrs['flat'] <= MAX_PIXELS:
        rings.appendleft(color_list[ctrs['flat_color_idx']])
        ctrs['flat_color_idx'] -= 1

        if ctrs['flat_color_idx'] < 0:
            ctrs['flat_color_idx'] = len(color_list) - 1
    else:
        rings.appendleft(BLANK)

    for i in range(len(rings)):
        for step in range(tmp_right - tmp_left + 1):
            l_edge = int(tmp_left + step)

            grid[tmp_left][l_edge] = rings[i]
            grid[tmp_right][l_edge] = rings[i]
            grid[l_edge][tmp_right] = rings[i]
            grid[l_edge][tmp_left] = rings[i]

        tmp_left -= 1
        tmp_right += 1

        # write pixels to board once grid is loaded with newest batch of data
        if tmp_left < 0 or tmp_right >= WIDTH:
            tmp_left = left
            tmp_right = right

    #push_grid(grid, sense)


def count_rounds_flat_position(ctrs, grid, sense, rings):
    overwrite_grid(grid, sense, FLAT, ctrs, rings)

    ctrs['flat'] += 1
    ctrs['away'], ctrs['toward'], ctrs['left'], ctrs['right'] = 0, 0, 0, 0


def count_rounds_pitch(sense, ctrs, pitch_region):
    # reset counters of all other types -- pitch is dominant sensor input
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
    if ctrs['left'] >= MAX_PIXELS or ctrs['right'] >= MAX_PIXELS:
        pitch_region = BLANK

    shift_list_values(sense, pitch_region, True)


def count_rounds_roll(sense, ctrs, roll_region):
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

    shift_list_values(sense, roll_region, False)

    #shift_grid(grid, roll_region, False, ROLL)


def yaw_spiral(sense):
    grid_list = sense.get_pixels()
    new_list = BLANK * 64
    horizontal_idx_offset = WIDTH + 1
    vertical_idx_offset = WIDTH - 1

    #get acceleration values. side spins spiral, drops scatter pixels/remove some


def shift_list_values(sense, region, is_pitch):
    grid_list = sense.get_pixels()
    color_midpoint = (len(color_list - 1)) // 2
    new_list = BLANK * 64
    idx = 0

    # SHIFT LEFT
    if is_pitch and region <= color_midpoint:
        while idx < SIZE:
            for i in range(0, WIDTH - 1):
                new_list[idx + i + 1] = grid_list[idx + i]
            idx += WIDTH
        #add new pixel column
        for i in range(0, SIZE, WIDTH):
            new_list[i] = PITCH[region]
    
    # SHIFT RIGHT
    elif is_pitch:
        while idx < SIZE:
            for i in range(1, WIDTH):
                new_list[i + idx - 1] = grid_list[idx + i]
            idx += WIDTH
        for i in range(WIDTH - 1, SIZE, WIDTH):
            new_list[i] = PITCH[region]

    #SHIFT UP
    elif region <= color_midpoint:
        idx = 8
        while idx < SIZE:
            for i in range(0, WIDTH):
                new_list[i + idx - WIDTH] = grid_list[i + idx]
        for i in range (SIZE - WIDTH, SIZE):
            new_list[i] = ROLL[region]

    #SHIFT DOWN
    else: 
        while idx < SIZE - WIDTH:
            for i in range(0, WIDTH):
                new_list[idx + i + WIDTH] = grid_list[idx + i]
        for i in range(0, WIDTH):
            new_list[i] = ROLL[region]

    sense.set_pixels(new_list)
    sleep(PAUSE)


def main():
    sense = SenseHat()
    sense.set_imu_config(False, True, True)
    # sense.clear()

    grid_list = [PINK] * 64
    sense.set_pixels(grid_list)

    #grid = deque([deque([BLANK] * WIDTH)] * WIDTH)
    ctrs = {'left': 0, 'right': 0, 'toward': 0, 'away': 0, 'flat': 0, 'flat_color_idx': randint(0, len(FLAT) - 1)}
    #rings = deque([BLANK] * WIDTH)

    while True:
        # convert deques to a flattened list
        data = sample_sensor_output(sense)

        # determine whether pitch and roll are +10 degrees from the origin in either direction
        # and if so, which value is higher
        if data['avg_pitch'] >= MAX_DEGREES/2:
            data['avg_pitch'] = abs(data['avg_pitch'] - MAX_DEGREES)

        if data['avg_roll'] >= MAX_DEGREES/2:
            data['avg_roll'] = abs(data['avg_roll'] - MAX_DEGREES)

        # keep sensor parallel with the ground
        if data['avg_pitch'] < 10 and data['avg_roll'] < 10:
            count_rounds_flat_position(ctrs, grid_list, sense, rings)
        # tilt around z axis (left and right)
        elif data['avg_pitch'] > data['avg_roll']:
            count_rounds_pitch(sense, ctrs, data['pitch_region'])
        # tilt around x axis (toward and away)
        else:
            count_rounds_roll(sense, ctrs, data['roll_region'])

main()
