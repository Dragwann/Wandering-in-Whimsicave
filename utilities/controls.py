import math
import pygame

from utilities.settings import (JOY_DEADZONE, JOY_BTN_SHOOT, JOY_AXIS_AIM_X, JOY_AXIS_AIM_Y,
                      JOY_AIM_DEADZONE, JOY_STICK_AUTOFIRE)


def read_input(keys, joysticks):
    """Merge keyboard, mouse and controller(s) into (move_x, move_y, shooting, stick_aim).
    stick_aim is a unit vector from the right stick, or None when the stick is at rest."""
    dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
    dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
    shooting = keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0]
    stick_aim = None

    for joy in joysticks.values():
        # left stick, with a deadzone because sticks never rest at exactly 0
        jx, jy = joy.get_axis(0), joy.get_axis(1)
        if math.hypot(jx, jy) < JOY_DEADZONE:
            jx = jy = 0
        dx += jx
        dy += jy
        # D-pad (a "hat"): up is +1 on the hat but -y on screen
        if joy.get_numhats() > 0:
            hx, hy = joy.get_hat(0)
            dx += hx
            dy -= hy
        if joy.get_numbuttons() > JOY_BTN_SHOOT and joy.get_button(JOY_BTN_SHOOT):
            shooting = True
        # right stick = aim direction (normalized: only the direction matters, not how far)
        if joy.get_numaxes() > max(JOY_AXIS_AIM_X, JOY_AXIS_AIM_Y):
            ax, ay = joy.get_axis(JOY_AXIS_AIM_X), joy.get_axis(JOY_AXIS_AIM_Y)
            alen = math.hypot(ax, ay)
            if alen >= JOY_AIM_DEADZONE:
                stick_aim = (ax / alen, ay / alen)
                if JOY_STICK_AUTOFIRE:
                    shooting = True

    # cap at length 1 so diagonals aren't faster; a half-pushed stick stays slower
    length = math.hypot(dx, dy)
    if length > 1:
        dx, dy = dx / length, dy / length
    return dx, dy, shooting, stick_aim
