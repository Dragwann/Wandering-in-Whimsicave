"""CollisionManager: DETECTS who touches whom. It never applies damage, never removes anything.

main.py reads the result and applies the gameplay consequences (take_hit, lose, win...).
Works on any object that has a `.hitboxes` list, so it never imports Player or the bosses.
"""
import pygame

from utilities.hitbox import touches, CIRCLE
from utilities.settings import WHITE


class CollisionResult:
    def __init__(self):
        self.boss_hit_by = []              # player bullets touching a boss hitbox
        self.hazards_hitting_player = []   # boss bullets / walls / mines touching the player
        self.player_touches_boss = False   # the boss body overlaps the player


class CollisionManager:
    def detect(self, player, boss, player_bullets, hazards):
        """Call once per frame, AFTER every update. Each pair is tested once."""
        result = CollisionResult()

        for bullet in player_bullets:
            if self.any_touch(boss.hitboxes, bullet.hitboxes):
                result.boss_hit_by.append(bullet)

        for hazard in hazards:
            if self.any_touch(hazard.hitboxes, player.hitboxes):
                result.hazards_hitting_player.append(hazard)

        result.player_touches_boss = self.any_touch(boss.hitboxes, player.hitboxes)

        # Remember where the big movers are NOW: next frame's swept test starts from here.
        for hitbox in boss.hitboxes + player.hitboxes:
            hitbox.remember_position()
        return result

    @staticmethod
    def any_touch(hitboxes_a, hitboxes_b):
        return any(touches(a, b) for a in hitboxes_a for b in hitboxes_b)

    @staticmethod
    def draw_debug(surf, *groups):
        """Draw every ENABLED hitbox, from the very same data the collisions use.
        Each group is a list of objects having `.hitboxes`: draw_debug(screen, [player, boss], bullets)."""
        for group in groups:
            for owner in group:
                for hitbox in owner.hitboxes:
                    if not hitbox.enabled:
                        continue
                    cx, cy = hitbox.center()
                    if hitbox.shape == CIRCLE:
                        pygame.draw.circle(surf, WHITE, (int(cx), int(cy)), max(1, int(hitbox.radius)), 1)
                    else:
                        rect = pygame.Rect(0, 0, int(hitbox.width), int(hitbox.height))
                        rect.center = (int(cx), int(cy))
                        pygame.draw.rect(surf, WHITE, rect, 1)