from sense_hat import SenseHat
from time import sleep, strftime, tzset
from collections import deque
from random import randint
import os

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
    #print("x: %s, y: %s, z: %s" % (accel['x'], accel['y'], accel['z']))

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
    data['accel'] = accel

    return data


def inc_horizontal_count(sense, ctrs):
    shift_rings(sense, ctrs)

    ctrs['flat'] += 1
    ctrs['away'], ctrs['toward'], ctrs['left'], ctrs['right'] = 0, 0, 0, 0


def inc_pitch_count(sense, ctrs, pitch_region):
    # reset counters of all other types -- pitch is dominant sensor input
    ctrs['away'], ctrs['toward'], ctrs['flat'] = 0, 0, 0
    if pitch_region < (len(PITCH) - 2) // 2:
        ctrs['left'] += 1
        ctrs['right'] = 0
        region = 0
    elif pitch_region >= (len(PITCH) - 1) // 2:
        ctrs['right'] += 1
        ctrs['left'] = 0
        region = 1
    else:
        ctrs['left'], ctrs['right'] = 0, 0
        region = -1

    # if counter reaches/exceeds grid size, stop outputting color until direction changes
    if ctrs['left'] >= MAX_PIXELS or ctrs['right'] >= MAX_PIXELS:
        color = BLANK
    else:
        color = PITCH[pitch_region]

    shift_colors(sense, color, region, True)


def inc_roll_count(sense, ctrs, roll_region):
    # reset counters of all other types -- roll is dominant sensor input
    ctrs['left'], ctrs['right'], ctrs['flat'] = 0, 0, 0

    # region count for tilting towards
    if roll_region < (len(ROLL) - 2) // 2:
        ctrs['toward'] += 1
        ctrs['away'] = 0
        region = 1
    # region count for tilting away
    elif roll_region >= (len(ROLL) - 1) // 2:
        ctrs['away'] += 1
        ctrs['toward'] = 0
        region = 0
    # in the blank zone between 90 -> 270, reset counters
    else:
        ctrs['away'], ctrs['toward'], = 0, 0
        region = -1

    # if counter reaches/exceeds maximum # of sequential pixels for a given direction, stop outputting
    # until direction changes by setting region equal to a non-visible segment.
    # the pixels fall off the screen in a downward direction.
    if ctrs['away'] > MAX_PIXELS or ctrs['toward'] > MAX_PIXELS:
        color = BLANK
    else:
        color = ROLL[roll_region]

    shift_colors(sense, color, region, False)


def shift_spiral(sense):
    grid_list = sense.get_pixels()
    new_list = [BLANK] * 64
    horizontal_idx_offset = WIDTH + 1
    vertical_idx_offset = WIDTH - 1

    #get acceleration values. side spins spiral, drops scatter pixels/remove some


def shift_rings(sense, ctrs):
    grid_list = sense.get_pixels()
    new_list = [BLANK] * 64

    #the four corners of the box
    box = {'top_left': 0, 'top_right': WIDTH, 'bottom_left': SIZE - WIDTH, 'bottom_right': SIZE}

    while top_left + WIDTH + 1 < bottom_right:
        color = grid_list[top_left + WIDTH + 1]

        for i in range(box['top_left'], box['top_right']):
            new_list[i] = color
        for i in range(box['bottom_left'], box['bottom_right']):
            new_list[i] = color
        for i in range(box['top_left'], box['bottom_left'], WIDTH):
            new_list[i] = color
        for i in range(box['top_right'], box['bottom_right'], WIDTH):
            new_list[i] = color

        top_left += WIDTH + 1
        bottom_right -= WIDTH + 1
        top_right += WIDTH - 1
        bottom_left -= WIDTH - 1

    if ctrs['flat'] <= MAX_PIXELS:
        color = FLAT[ctrs['flat_color_idx' % len(FLAT)]]
    else:
        color = BLANK

    new_list[top_left] = color
    new_list[top_right] = color
    new_list[bottom_left] = color
    new_list[bottom_right] = color

    sense.set_pixels(new_list)
    sleep(PAUSE)


def shift_colors(sense, color, region, is_pitch):
    grid_list = sense.get_pixels()

    new_list = [BLANK] * 64
    idx = 0

    if region != -1:
        # SHIFT LEFT
        if is_pitch and region == 0:
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

        #SHIFT AWAY
        elif region == 0:
            idx = 8
            while idx < SIZE:
                for i in range(0, WIDTH):
                    new_list[idx + i - WIDTH] = grid_list[idx + i]
            for i in range (SIZE - WIDTH, SIZE):
                new_list[i] = ROLL[region]

        #SHIFT TOWARD    
        else: 
            while idx < SIZE - WIDTH:
                for i in range(0, WIDTH):
                    new_list[idx + i + WIDTH] = grid_list[idx + i]
            for i in range(0, WIDTH):
                new_list[i] = ROLL[region]

        sense.set_pixels(new_list)
        sleep(PAUSE)
    else:
        print("unspecified direction.")


def main():
    ctrs = {'left': 0, 'right': 0, 'toward': 0, 'away': 0, 'flat': 0, 'flat_color_idx': randint(0, len(FLAT) - 1)}

    sense = SenseHat()
    sense.set_imu_config(False, True, True)

    grid_list = [PINK] * 64
    sense.set_pixels(grid_list)

    while True:
        # convert deques to a flattened list
        data = sample_sensor_output(sense)
        print(data)

        #Adjust degrees to be positive if necessary
        if data['avg_pitch'] < 0:
            data['avg_pitch'] += MAX_DEGREES

        if data['avg_roll'] < 0:
            data['avg_roll'] += MAX_DEGREES

        data['avg_pitch'] = data['avg_pitch'] % MAX_DEGREES
        data['avg_roll'] = data['avg_roll'] % MAX_DEGREES

        # sensor parallel with the ground
        if data['avg_pitch'] < 10 and data['avg_roll'] < 10:
            inc_horizontal_count(sense, ctrs)
            print "1"
        #todo: check for acceleration down and twisting (z or y axis)

        # rotate left and right
        elif data['avg_pitch'] > data['avg_roll']:
            inc_pitch_count(sense, ctrs, data['pitch_region'])
            print "2"
        # rotate towards and away
        else:
            inc_roll_count(sense, ctrs, data['roll_region'])
            print "3"

main()
