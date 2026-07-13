import os

# Comentario semántico: forzamos ALSA para usar la salida de audio correcta en Raspberry.
os.environ["SDL_AUDIODRIVER"] = "alsa"

import sys
import pygame

from prueba1 import Prueba1
from prueba2 import Prueba2
from prueba3 import Prueba3
from prueba4 import Prueba4
from final_juego import FinalJuego


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600

STATE_MENU = "menu"
STATE_PRUEBA1 = "prueba1"
STATE_PRUEBA2 = "prueba2"
STATE_PRUEBA3 = "prueba3"
STATE_PRUEBA4 = "prueba4"
STATE_FINAL_JUEGO = "final_juego"
STATE_PLACEHOLDER = "placeholder"
MODO_DESBLOQUEO_RAPIDO = True


# Paleta temática
BACKGROUND_TOP = (65, 48, 40)
BACKGROUND_BOTTOM = (154, 124, 88)

PANEL = (246, 235, 210)
PANEL_BORDER = (97, 70, 48)
PANEL_SHADOW = (38, 28, 24)

TEXT = (35, 25, 20)
TEXT_SOFT = (95, 76, 58)
TITLE = (255, 241, 205)

BUTTON = (222, 200, 158)
BUTTON_SELECTED = (245, 220, 165)
BUTTON_BORDER = (95, 66, 40)
BUTTON_SHADOW = (70, 47, 32)

HELP_TEXT = (245, 235, 215)


def draw_text(screen, text, font, color, center):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=center)
    screen.blit(surface, rect)


def draw_text_with_shadow(screen, text, font, color, center, shadow_offset=(3, 3)):
    shadow_surface = font.render(text, True, (30, 22, 18))
    shadow_rect = shadow_surface.get_rect(
        center=(center[0] + shadow_offset[0], center[1] + shadow_offset[1])
    )
    screen.blit(shadow_surface, shadow_rect)

    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center)
    screen.blit(text_surface, text_rect)


def draw_vertical_gradient(screen, top_color, bottom_color):
    for y in range(SCREEN_HEIGHT):
        ratio = y / SCREEN_HEIGHT
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))


def draw_decorative_frame(screen):
    outer_rect = pygame.Rect(26, 22, SCREEN_WIDTH - 52, SCREEN_HEIGHT - 44)
    inner_rect = pygame.Rect(38, 34, SCREEN_WIDTH - 76, SCREEN_HEIGHT - 68)

    pygame.draw.rect(screen, (232, 205, 150), outer_rect, width=4, border_radius=18)
    pygame.draw.rect(screen, (92, 62, 38), inner_rect, width=2, border_radius=14)

    # Comentario semántico: pequeños círculos decorativos para recordar vidrieras o adornos de iglesia.
    corner_points = [
        (56, 52),
        (SCREEN_WIDTH - 56, 52),
        (56, SCREEN_HEIGHT - 52),
        (SCREEN_WIDTH - 56, SCREEN_HEIGHT - 52),
    ]

    for point in corner_points:
        pygame.draw.circle(screen, (232, 205, 150), point, 8)
        pygame.draw.circle(screen, (92, 62, 38), point, 8, width=2)


def draw_panel(screen, rect):
    shadow_rect = rect.move(8, 8)

    pygame.draw.rect(screen, PANEL_SHADOW, shadow_rect, border_radius=24)
    pygame.draw.rect(screen, PANEL, rect, border_radius=24)
    pygame.draw.rect(screen, PANEL_BORDER, rect, width=4, border_radius=24)

    # Comentario semántico: línea interior para simular una tarjeta o invitación antigua.
    inner_rect = rect.inflate(-24, -24)
    pygame.draw.rect(screen, (198, 160, 105), inner_rect, width=2, border_radius=18)


def draw_button(screen, rect, text, font, is_selected):
    fill = BUTTON_SELECTED if is_selected else BUTTON

    shadow_rect = rect.move(5, 6)
    pygame.draw.rect(screen, BUTTON_SHADOW, shadow_rect, border_radius=18)

    pygame.draw.rect(screen, fill, rect, border_radius=18)
    pygame.draw.rect(screen, BUTTON_BORDER, rect, width=3, border_radius=18)

    if is_selected:
        glow_rect = rect.inflate(10, 10)
        pygame.draw.rect(screen, (255, 234, 175), glow_rect, width=3, border_radius=22)

    draw_text(screen, text, font, TEXT, rect.center)


def draw_exit_button(screen, rect, font):
    shadow_rect = rect.move(4, 5)

    pygame.draw.ellipse(screen, BUTTON_SHADOW, shadow_rect)
    pygame.draw.ellipse(screen, BUTTON_SELECTED, rect)
    pygame.draw.ellipse(screen, BUTTON_BORDER, rect, width=3)

    draw_text(screen, "X", font, TEXT, rect.center)


def draw_final_bar(screen, rect, font):
    shadow_rect = rect.move(5, 6)

    pygame.draw.rect(screen, BUTTON_SHADOW, shadow_rect, border_radius=18)
    pygame.draw.rect(screen, BUTTON_SELECTED, rect, border_radius=18)
    pygame.draw.rect(screen, BUTTON_BORDER, rect, width=3, border_radius=18)

    draw_text(screen, "Introducir código final", font, TEXT, rect.center)


def draw_icon(screen, center, index, is_selected):
    color = (105, 72, 42) if not is_selected else (70, 45, 25)

    x, y = center

    if index == 0:
        # Anillo con diamante
        pygame.draw.circle(screen, color, (x, y + 8), 15, width=4)

        diamond_points = [
            (x - 9, y - 16),
            (x - 4, y - 23),
            (x + 4, y - 23),
            (x + 9, y - 16),
            (x, y - 6),
        ]

        pygame.draw.polygon(screen, color, diamond_points, width=3)

        pygame.draw.line(screen, color, (x - 9, y - 16), (x + 9, y - 16), width=2)
        pygame.draw.line(screen, color, (x - 4, y - 23), (x, y - 6), width=2)
        pygame.draw.line(screen, color, (x + 4, y - 23), (x, y - 6), width=2)
        pygame.draw.line(screen, color, (x, y - 23), (x, y - 6), width=2)

    elif index == 1:
        # Candelabro 
        pygame.draw.line(screen, color, (x, y - 5), (x, y + 15), width=3)
        pygame.draw.line(screen, color, (x - 16, y + 3), (x + 16, y + 3), width=3)

        pygame.draw.arc(screen, color, pygame.Rect(x - 21, y - 3, 18, 18), 3.14, 6.28, width=3)
        pygame.draw.arc(screen, color, pygame.Rect(x + 3, y - 3, 18, 18), 3.14, 6.28, width=3)

        candle_positions = [
            (x - 18, y - 3),
            (x, y - 11),
            (x + 18, y - 3),
        ]

        for candle_x, candle_y in candle_positions:
            pygame.draw.rect(screen, color, pygame.Rect(candle_x - 3, candle_y, 6, 15), width=2)
            pygame.draw.polygon(
                screen,
                color,
                [
                    (candle_x, candle_y - 8),
                    (candle_x - 4, candle_y),
                    (candle_x + 4, candle_y),
                ],
                width=2
            )

        pygame.draw.rect(screen, color, pygame.Rect(x - 10, y + 15, 20, 5), border_radius=3)

    elif index == 2:
        # Bocadillo de diálogo
        bubble_rect = pygame.Rect(x - 18, y - 12, 36, 24)
        pygame.draw.rect(screen, color, bubble_rect, width=3, border_radius=8)
        pygame.draw.polygon(screen, color, [(x - 5, y + 11), (x - 13, y + 21), (x + 3, y + 12)])

    else:
        # Operaciones matemáticas
        font = pygame.font.SysFont("Arial", 20, bold=True)

        symbols = [
            ("+", (x - 11, y - 10)),
            ("−", (x + 12, y - 10)),
            ("×", (x - 11, y + 11)),
            ("=", (x + 12, y + 11)),
        ]

        for symbol, pos in symbols:
            surface = font.render(symbol, True, color)
            rect = surface.get_rect(center=pos)
            screen.blit(surface, rect)


def draw_menu(screen, title_font, button_font, info_font, subtitle_font, options, selected_index, final_desbloqueado):
    draw_vertical_gradient(screen, BACKGROUND_TOP, BACKGROUND_BOTTOM)
    draw_decorative_frame(screen)

    draw_text_with_shadow(
        screen,
        "UNA BODA A CONTRARRELOJ",
        title_font,
        TITLE,
        (SCREEN_WIDTH // 2, 78)
    )

    panel_rect = pygame.Rect(190, 120, 644, 395)
    draw_panel(screen, panel_rect)

    draw_text(
        screen,
        "Selecciona una prueba",
        info_font,
        TEXT_SOFT,
        (SCREEN_WIDTH // 2, 160)
    )

    button_width = 500
    button_height = 66
    button_spacing = 12
    start_y = 187

    button_rects = []

    for i, option in enumerate(options):
        x = (SCREEN_WIDTH - button_width) // 2
        y = start_y + i * (button_height + button_spacing)

        rect = pygame.Rect(x, y, button_width, button_height)
        button_rects.append(rect)

        draw_button(screen, rect, option, button_font, i == selected_index)
        draw_icon(screen, (rect.left + 40, rect.centery), i, i == selected_index)

    final_rect = None

    if final_desbloqueado:
        final_rect = pygame.Rect(102, 518, 820, 48)
        draw_final_bar(screen, final_rect, subtitle_font)
    else:
        draw_text(
            screen,
            "Ayudad a resolver el misterio antes de la boda.",
            subtitle_font,
            HELP_TEXT,
            (SCREEN_WIDTH // 2, 542)
        )

    exit_rect = pygame.Rect(895, 52, 64, 64)
    draw_exit_button(screen, exit_rect, info_font)

    return button_rects, exit_rect, final_rect


def draw_placeholder(screen, title_font, info_font, test_name):
    draw_vertical_gradient(screen, BACKGROUND_TOP, BACKGROUND_BOTTOM)
    draw_decorative_frame(screen)

    panel_rect = pygame.Rect(212, 150, 600, 300)
    draw_panel(screen, panel_rect)

    draw_text(screen, test_name, title_font, TEXT, (SCREEN_WIDTH // 2, 215))
    draw_text(
        screen,
        "Esta prueba se implementará más adelante.",
        info_font,
        TEXT_SOFT,
        (SCREEN_WIDTH // 2, 295)
    )

    back_rect = pygame.Rect(312, 470, 400, 70)
    draw_button(screen, back_rect, "Volver al menú", info_font, False)

    return back_rect


def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("Hall Game")

    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("Arial", 44, bold=True)
    button_font = pygame.font.SysFont("Arial", 32, bold=True)
    info_font = pygame.font.SysFont("Arial", 31, bold=True)
    subtitle_font = pygame.font.SysFont("Arial", 25)

    options = [
        "El misterio del anillo",
        "Las luces de la iglesia",
        "¡Vaya refrán!",
        "Un total de..."
    ]

    current_state = STATE_MENU
    selected_index = 0
    active_test_name = ""

    prueba1 = Prueba1(screen)
    prueba2 = Prueba2(screen)
    prueba3 = Prueba3(screen)
    prueba4 = Prueba4(screen)
    final_juego = FinalJuego(screen)

    pruebas_completadas = [False, False, False, False]

    running = True

    while running:
        button_rects = []
        back_rect = None
        exit_rect = None
        final_rect = None

        if current_state == STATE_MENU:
            if MODO_DESBLOQUEO_RAPIDO:
                final_desbloqueado = pruebas_completadas[2]
            else:
                final_desbloqueado = all(pruebas_completadas)

            button_rects, exit_rect, final_rect = draw_menu(
                screen,
                title_font,
                button_font,
                info_font,
                subtitle_font,
                options,
                selected_index,
                final_desbloqueado
)

        elif current_state == STATE_PRUEBA1:
            prueba1.draw()

        elif current_state == STATE_PRUEBA2:
            prueba2.draw()

        elif current_state == STATE_PRUEBA3:
            prueba3.draw()

        elif current_state == STATE_PRUEBA4:
            prueba4.draw()

        elif current_state == STATE_FINAL_JUEGO:
            final_juego.draw()

        elif current_state == STATE_PLACEHOLDER:
            back_rect = draw_placeholder(screen, title_font, info_font, active_test_name)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif current_state == STATE_PRUEBA2:
                    prueba2.handle_keydown(event.key)

                elif current_state == STATE_FINAL_JUEGO:
                    final_juego.handle_keydown(event.key)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    # Comentario semántico: usamos la posición exacta del toque actual, no la posición previa del ratón.
                    touch_pos = event.pos

                    if current_state == STATE_MENU:
                        if exit_rect and exit_rect.collidepoint(touch_pos):
                            running = False

                        elif final_rect and final_rect.collidepoint(touch_pos):
                            final_juego.reset()
                            current_state = STATE_FINAL_JUEGO
                            pygame.event.clear()

                        else:
                            for i, rect in enumerate(button_rects):
                                if rect.collidepoint(touch_pos):
                                    selected_index = i
                                    active_test_name = options[selected_index]

                                    if selected_index == 0:
                                        prueba1.reset()
                                        current_state = STATE_PRUEBA1

                                    elif selected_index == 1:
                                        prueba2.reset()
                                        current_state = STATE_PRUEBA2

                                    elif selected_index == 2:
                                        prueba3.reset()
                                        current_state = STATE_PRUEBA3

                                    elif selected_index == 3:
                                        prueba4.reset()
                                        current_state = STATE_PRUEBA4

                                    else:
                                        current_state = STATE_PLACEHOLDER

                                    pygame.event.clear()
                                    break

                    elif current_state == STATE_PRUEBA1:
                        estado_previo = getattr(prueba1, "state", None)
                        result = prueba1.handle_click(touch_pos)

                        if result == "menu":
                            if estado_previo == "final":
                                pruebas_completadas[0] = True

                            current_state = STATE_MENU
                            pygame.event.clear()

                    elif current_state == STATE_PRUEBA2:
                        estado_previo = getattr(prueba2, "state", None)
                        result = prueba2.handle_click(touch_pos)

                        if result == "menu":
                            if estado_previo == "final":
                                pruebas_completadas[1] = True

                            current_state = STATE_MENU
                            pygame.event.clear()

                    elif current_state == STATE_PRUEBA3:
                        estado_previo = getattr(prueba3, "state", None)
                        result = prueba3.handle_click(touch_pos)

                        if result == "menu":
                            if estado_previo == "final":
                                pruebas_completadas[2] = True

                            current_state = STATE_MENU
                            pygame.event.clear()

                    elif current_state == STATE_PRUEBA4:
                        estado_previo = getattr(prueba4, "state", None)
                        result = prueba4.handle_click(touch_pos)

                        if result == "menu":
                            if estado_previo == "final":
                                pruebas_completadas[3] = True

                            current_state = STATE_MENU
                            pygame.event.clear()

                    elif current_state == STATE_FINAL_JUEGO:
                        result = final_juego.handle_click(touch_pos)

                        if result == "menu":
                            current_state = STATE_MENU
                            pygame.event.clear()

                    elif current_state == STATE_PLACEHOLDER:
                        if back_rect and back_rect.collidepoint(touch_pos):
                            current_state = STATE_MENU
                            pygame.event.clear()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()