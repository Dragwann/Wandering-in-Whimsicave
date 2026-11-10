from utilities.settings import WIDTH, TITLE, WHITE, YELLOW, BACKGROUND_COLOR

BOSS_NAMES = ["James Pines", "Dr. Maurice"]


def draw_menu(surf, title_font, menu_font, selected):
    """Boss select screen: title on top, list of bosses, selected one highlighted."""
    surf.fill(BACKGROUND_COLOR)

    title = title_font.render(TITLE, True, WHITE)
    surf.blit(title, title.get_rect(center=(WIDTH // 2, 90)))

    for i, name in enumerate(BOSS_NAMES):
        is_selected = (i == selected)
        text = f"> {name} <" if is_selected else name
        color = YELLOW if is_selected else WHITE
        label = menu_font.render(text, True, color)
        surf.blit(label, label.get_rect(center=(WIDTH // 2, 250 + i * 60)))
