import sys
import math
import pygame

from utilities.settings import (WIDTH, HEIGHT, FPS, DEBUG_KEYS, WHITE, BACKGROUND_COLOR,
                      PLAYER_RADIUS, JOY_BTN_RESTART, CROSSHAIR_DISTANCE)
from utilities.utils import circle_hit
from utilities.controls import read_input
from entities.player import Player
from entities.boss1 import Boss
from entities.boss2 import Boss2
from utilities.ui import draw_crosshair
from scenes.menu import BOSS_NAMES, draw_menu


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Wandering in Whimsicave (prototype)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 28)
    title_font = pygame.font.SysFont("arial", 64)
    menu_font = pygame.font.SysFont("arial", 36)

    def new_game(boss_index):
        boss = Boss() if boss_index == 0 else Boss2()
        return Player(), boss, [], [], "playing"

    selected = 0
    player, boss, player_bullets, boss_bullets, state = new_game(selected)
    state = "menu"        # the game opens on the boss select screen
    god_mode = False
    aim_mode = "mouse"
    aim_dir = (1.0, 0.0)

    # connected controllers, by instance id (so pads can be plugged in/out while playing)
    joysticks = {}
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        joysticks[joy.get_instance_id()] = joy

    # debug: key -> boss HP fraction (just inside each phase)
    debug_phase_hp = {pygame.K_1: 1.0, pygame.K_2: 0.6, pygame.K_3: 0.3}

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                aim_mode = "mouse"
            if event.type == pygame.JOYDEVICEADDED:
                joy = pygame.joystick.Joystick(event.device_index)
                joysticks[joy.get_instance_id()] = joy
            if event.type == pygame.JOYDEVICEREMOVED:
                joysticks.pop(event.instance_id, None)
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == JOY_BTN_RESTART and state in ("win", "lose"):
                    player, boss, player_bullets, boss_bullets, state = new_game(selected)
            if event.type == pygame.KEYDOWN:
                if state == "menu":
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % len(BOSS_NAMES)
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(BOSS_NAMES)
                    elif event.key == pygame.K_RETURN:
                        player, boss, player_bullets, boss_bullets, state = new_game(selected)
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                else:
                    if event.key == pygame.K_ESCAPE:
                        state = "menu"
                    if event.key == pygame.K_r and state in ("win", "lose"):
                        player, boss, player_bullets, boss_bullets, state = new_game(selected)
                    if DEBUG_KEYS and state == "playing":
                        if event.key in debug_phase_hp:
                            boss.hp = boss.max_hp * debug_phase_hp[event.key]
                        if event.key == pygame.K_g:
                            god_mode = not god_mode
                            print("God mode:", "ON" if god_mode else "OFF")

        keys = pygame.key.get_pressed()
        move_x, move_y, shooting, stick_aim = read_input(keys, joysticks)

        # Aim: the right stick wins when it is pushed, otherwise follow the mouse.
        # The mouse direction is recomputed EVERY frame because the player moves too.
        if stick_aim is not None:
            aim_mode = "stick"
            aim_dir = stick_aim
        elif aim_mode == "mouse":
            mx, my = pygame.mouse.get_pos()
            adx, ady = mx - player.x, my - player.y
            alen = math.hypot(adx, ady)
            if alen > 1:
                aim_dir = (adx / alen, ady / alen)

        if state == "playing":
            player.update(dt, move_x, move_y, shooting, aim_dir, player_bullets)
            boss.update(dt, boss_bullets, player)

            for b in player_bullets:
                b.update(dt)

            # boss hazards can spawn new hazards (rain), so collect them first
            spawned = []
            for b in boss_bullets:
                b.update(dt, spawned)
            boss_bullets.extend(spawned)

            player_bullets[:] = [b for b in player_bullets if not b.offscreen()]
            boss_bullets[:] = [b for b in boss_bullets if not (b.dead or b.offscreen())]

            # collisions : Player vs. boss shots (absorbed, but no damage, during transitions)
            still_alive_bullets = []
            for b in player_bullets:
                if circle_hit(b.x, b.y, b.radius, boss.x, boss.y, boss.radius):
                    boss.take_hit(1)
                else:
                    still_alive_bullets.append(b)
            player_bullets[:] = still_alive_bullets

            # collisions : boss hazards + boss body vs player
            if not god_mode:
                for b in boss_bullets:
                    if b.hits(player.x, player.y, PLAYER_RADIUS):
                        state = "lose"
                        break
                if boss.deals_contact_damage() and circle_hit(
                        player.x, player.y, PLAYER_RADIUS, boss.x, boss.y, boss.radius):
                    state = "lose"

            if boss.hp <= 0:
                state = "win"

        # Drawing
        if state == "menu":
            draw_menu(screen, title_font, menu_font, selected)
        else:
            screen.fill(BACKGROUND_COLOR)
            boss.draw(screen)
            for b in boss_bullets:
                b.draw(screen)
            for b in player_bullets:
                b.draw(screen)
            player.draw(screen)

            if aim_mode == "mouse":
                draw_crosshair(screen, *pygame.mouse.get_pos())
            else:
                draw_crosshair(screen, player.x + aim_dir[0] * CROSSHAIR_DISTANCE,
                               player.y + aim_dir[1] * CROSSHAIR_DISTANCE)

            screen.blit(font.render(BOSS_NAMES[selected], True, WHITE), (10, 10))

            if state == "win":
                txt = font.render("VICTOIRE ! Appuie sur R pour recommencer", True, WHITE)
                screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 20))
            elif state == "lose":
                txt = font.render("TOUCHE... Appuie sur R pour reessayer", True, WHITE)
                screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 20))

        pygame.mouse.set_visible(state == "menu")
        pygame.display.flip()


if __name__ == "__main__":
    main()
