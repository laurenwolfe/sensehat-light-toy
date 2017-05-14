from sense_hat import SenseHat
from time import sleep
from collections import deque

L_RED = (100, 0, 0)
RED = (209, 0, 0)
ORANGE = (255, 102, 34)
YELLOW = (255, 118, 33)
GREEN = (51, 221, 0)
BLUE = (17, 51, 204)
INDIGO = (34, 0, 102)
L_PURPLE = (70, 0, 70)
PURPLE = (140, 0, 0)
BLANK = (0, 0, 0)
WHITE = (255, 255, 255)

GRID_SIZE = 8
SOFT_LEFT = L_RED
SOFT_TOWARD = PURPLE
HARD_TOWARD = L_PURPLE
HARD_LEFT = RED
SOFT_RIGHT = BLUE
HARD_RIGHT = INDIGO
SOFT_AWAY = YELLOW
HARD_AWAY = GREEN
BLANK = BLANK
NUM_SAMPLES = 10
DELAY = 0.1


def get_region_45(num):
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


def get_region_90(num):
    if num < 90:
        return 0
    elif num >= 90 and num < 180:
        return 1
    elif num >= 180 and num < 270:
        return 2
    elif num >= 270:
        return 3


# pop old pixels and insert new values for left/right rotation
def shift_pitch(grid, region):
    # soft left, 0 -> 45
    if region == 0:
        for i in range(GRID_SIZE):
            grid[i].popleft()
            grid[i].append(SOFT_LEFT)

    # hard left, 45 -> 90
    elif region == 1:
        for i in range(GRID_SIZE):
            grid[i].popleft()
            grid[i].append(HARD_LEFT)

    # too far left, 90 -> 180:
    elif region == 2:
        for i in range(GRID_SIZE):
            grid[i].popleft()
            grid.append(BLANK)

    # too far right, 180 -> 270:
    elif region == 3:
        for i in range(GRID_SIZE):
            grid[i].pop()
            grid[i].appendleft(BLANK)

    # hard right, 270 -> 315
    elif region == 4:
        for i in range(GRID_SIZE):
            grid[i].pop()
            grid[i].appendleft(HARD_RIGHT)

    # soft right, 315 -> 360
    elif region == 5:
        for i in range(GRID_SIZE):
            grid[i].pop()
            grid[i].appendleft(SOFT_RIGHT)

    return grid


def shift_roll(grid, region):
    # soft towards, 0 -> 45
    if region == 0:
        grid.pop()
        grid.appendleft(deque([SOFT_TOWARD] * GRID_SIZE))

    # hard towards, 45 -> 90
    elif region == 1:
        grid.pop()
        grid.appendleft(deque([HARD_TOWARD] * GRID_SIZE))

    # too hard towards, 90 -> 180
    elif region == 2:
        grid.pop()
        grid.appendleft(deque([BLANK] * GRID_SIZE))

    # too hard away, 180 -> 270
    elif region == 3:
        grid.popleft()
        grid.append(deque([BLANK] * GRID_SIZE))

    # hard away, 270 -> 315
    elif region == 4:
        grid.popleft()
        grid.append(deque([HARD_AWAY] * GRID_SIZE))

    # soft away, 315 -> 360
    elif region == 5:
        grid.popleft()
        grid.append(deque([SOFT_AWAY] * GRID_SIZE))

    return grid


def main():
    sense = SenseHat()
    sense.set_imu_config(False, True, True)
    sense.clear()

    grid = deque([deque([BLANK] * GRID_SIZE), deque([BLANK] * GRID_SIZE),
                  deque([BLANK] * GRID_SIZE), deque([BLANK] * GRID_SIZE),
                  deque([BLANK] * GRID_SIZE), deque([BLANK] * GRID_SIZE),
                  deque([BLANK] * GRID_SIZE), deque([BLANK] * GRID_SIZE)])

    # old_pitch, old_roll, old_yaw = 0, 0, 0

    while True:
        pitch_counts = [0] * 6
        pitch_sums = [0] * 6
        roll_counts = [0] * 6
        roll_sums = [0] * 6
        yaw_counts = [0] * 4
        yaw_sums = [0] * 4

        # take sample_size samples at sleep_time interval
        for i in range(NUM_SAMPLES):
            orient = sense.get_orientation()
            p, r, y = orient['pitch'], orient['roll'], orient['yaw']

            # sum each value by region and tally the counts
            pitch_counts[get_region_45(p)] += 1
            pitch_sums[get_region_45(p)] += p
            roll_counts[get_region_45(r)] += 1
            roll_sums[get_region_45(r)] += r
            yaw_counts[get_region_90(y)] += 1
            yaw_sums[get_region_90(y)] += y

            # short delay between samples
            # sleep(DELAY)

        # get average value of highest frequency region for pitch
        pitch_count = max(pitch_counts)
        pitch_region = pitch_counts.index(pitch_count)
        print("pitch: region {}, count {}".format(pitch_region, pitch_count))
        pitch = pitch_sums[pitch_region] / pitch_count

        # get average value of highest frequency region for roll
        roll_count = max(roll_counts)
        roll_region = roll_counts.index(roll_count)
        print("roll: region {}, count {}". format(roll_region, roll_count))
        roll = roll_sums[roll_region] / roll_count

        # get average value of highest frequency region for yaw
        yaw_count = max(yaw_counts)
        yaw_region = yaw_counts.index(yaw_count)
        yaw = yaw_sums[yaw_region] / yaw_count

        # determine whether pitch or roll has the largest delta:
        # large will take precedent in

        if pitch > 180:
            pitch -= 360
        if roll > 180:
            roll -= 360

        if abs(pitch) > abs(roll):
            # shift horizontal pixels
            print("pitch: {}, roll: {}".format(pitch, roll))
            grid = shift_pitch(grid, pitch_region)
        else:
            # shift vertical pixels
            print("pitch: {}, roll: {}".format(pitch, roll))
            grid = shift_roll(grid, roll_region)

        # old_pitch, old_roll, old_yaw = pitch, roll, yaw

        grid_list = []

        for row in grid:
            grid_list += list(row)

        sense.set_pixels(grid_list)
        sleep(.1)

main()
