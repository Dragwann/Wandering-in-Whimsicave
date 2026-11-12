"""Hitboxes: the collision geometry of an object, independent from its sprite.

A Hitbox does NOT store its own position. It stores an OFFSET from its owner and reads
owner.x / owner.y on demand, so it follows the owner automatically (dash included).

Shapes: circle (radius) and axis-aligned rectangle (width, height), both CENTER-based.
All overlap tests are strict (< and not <=): two shapes that only touch do not collide,
exactly like the old circle_hit.

This file imports nothing from the project.
"""
import math

CIRCLE = "circle"
RECT = "rect"


class Hitbox:
    def __init__(self, owner, shape, radius=0.0, width=0.0, height=0.0,
                 offset=(0, 0), enabled=True, swept=False, tag="body"):
        self.owner = owner            # any object with .x and .y (its center)
        self.shape = shape            # CIRCLE or RECT
        self.radius = radius          # circles (can be changed at any time, e.g. TrailBullet)
        self.width = width            # rectangles
        self.height = height
        self.offset_x, self.offset_y = offset
        self.enabled = enabled        # a disabled hitbox is ignored by collisions AND by debug drawing
        self.swept = swept            # True = also test the path travelled since last frame
        self.tag = tag                # just a label for now ("body", later maybe "weak_point")
        self.previous_center = None   # filled by CollisionManager, used by the swept test

    @classmethod
    def circle(cls, owner, radius, offset=(0, 0), enabled=True, swept=False, tag="body"):
        return cls(owner, CIRCLE, radius=radius, offset=offset,
                   enabled=enabled, swept=swept, tag=tag)

    @classmethod
    def rect(cls, owner, width, height, offset=(0, 0), enabled=True, swept=False, tag="body"):
        return cls(owner, RECT, width=width, height=height, offset=offset,
                   enabled=enabled, swept=swept, tag=tag)

    def center(self):
        return (self.owner.x + self.offset_x, self.owner.y + self.offset_y)

    def smallest_half_size(self):
        """Radius of a circle, half of the shortest side of a rectangle. Sets the sweep step."""
        if self.shape == CIRCLE:
            return self.radius
        return min(self.width, self.height) / 2

    def remember_position(self):
        self.previous_center = self.center()


# ---------------------------------------------------------------- geometry (pure functions)

def circles_overlap(center_1, radius_1, center_2, radius_2):
    return math.hypot(center_1[0] - center_2[0], center_1[1] - center_2[1]) < radius_1 + radius_2


def circle_rect_overlap(circle_center, radius, rect_center, width, height):
    # closest point of the rectangle to the circle center (same idea as the old Wall.hits)
    half_w, half_h = width / 2, height / 2
    nearest_x = max(rect_center[0] - half_w, min(circle_center[0], rect_center[0] + half_w))
    nearest_y = max(rect_center[1] - half_h, min(circle_center[1], rect_center[1] + half_h))
    return math.hypot(circle_center[0] - nearest_x, circle_center[1] - nearest_y) < radius


def rects_overlap(center_1, width_1, height_1, center_2, width_2, height_2):
    return (abs(center_1[0] - center_2[0]) < (width_1 + width_2) / 2 and
            abs(center_1[1] - center_2[1]) < (height_1 + height_2) / 2)


def overlap(a, b, center_a=None, center_b=None):
    """Do two hitboxes overlap right now? A center can be given to test a hypothetical position."""
    if center_a is None:
        center_a = a.center()
    if center_b is None:
        center_b = b.center()

    if a.shape == CIRCLE and b.shape == CIRCLE:
        return circles_overlap(center_a, a.radius, center_b, b.radius)
    if a.shape == CIRCLE and b.shape == RECT:
        return circle_rect_overlap(center_a, a.radius, center_b, b.width, b.height)
    if a.shape == RECT and b.shape == CIRCLE:
        return circle_rect_overlap(center_b, b.radius, center_a, a.width, a.height)
    return rects_overlap(center_a, a.width, a.height, center_b, b.width, b.height)


def swept_overlap(moving, other):
    """Test `moving` along the segment previous_center -> center, against `other` where it is now.

    Sub-steps are never longer than the smallest hitbox dimension, so nothing can be skipped.
    Only the moving hitbox is swept: `other` is considered still (fine for a dash at 800 px/s
    against a player at 320 px/s).
    """
    end = moving.center()
    start = moving.previous_center if moving.previous_center is not None else end
    distance = math.hypot(end[0] - start[0], end[1] - start[1])
    step = max(1.0, min(moving.smallest_half_size(), other.smallest_half_size()))
    sample_count = math.ceil(distance / step)
    if sample_count == 0:
        return overlap(moving, other)

    other_center = other.center()
    for i in range(sample_count + 1):
        t = i / sample_count
        center = (start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t)
        if overlap(moving, other, center_a=center, center_b=other_center):
            return True
    return False


def touches(a, b):
    """The one question the CollisionManager asks. Handles disabled and swept hitboxes."""
    if not (a.enabled and b.enabled):
        return False
    if a.swept:
        return swept_overlap(a, b)
    if b.swept:
        return swept_overlap(b, a)
    return overlap(a, b)