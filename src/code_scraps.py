'''
HARD_LEFT = RED
SOFT_LEFT = VIOLET_RED
SOFT_RIGHT = LIGHT_PURPLE
HARD_RIGHT = PURPLE

HARD_TOWARD = GREEN
SOFT_TOWARD = GREEN_YELLOW
SOFT_AWAY = GOLD
HARD_AWAY = ORANGE

H_LEFT_SPIN = DARK_CYAN
S_LEFT_SPIN = CYAN
S_RIGHT_SPIN = BLUE
H_RIGHT_SPIN = DARK_BLUE
'''

'''
def get_region_30(num):
    if num < 30:
        return 0
    elif num >= 30 and num < 60:
        return 1
    elif num >= 60 and num < 90:
        return 2
    elif num >= 90 and num < 180:
        return 3
    elif num >= 180 and num < 270:
        return 4
    elif num >= 270 and num < 300:
        return 5
    elif num >= 300 and num < 330:
        return 6
    elif num >= 330:
        return 7


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
'''

'''
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
'''

'''
# pop old pixels and insert new values for left/right rotation
def shift_pitch(grid, region):
    if region < math.ceil(MAX_REGIONS / 2):
        for i in range(GRID_SIZE):
            grid[i].popleft()
            grid[i].append(PITCH[region])
    else:
        for i in range(GRID_SIZE):
            grid[i].pop()
            grid[i].appendleft(PITCH[region])

    return grid
'''

'''
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
'''
