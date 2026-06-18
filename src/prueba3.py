import random
import wave
from pathlib import Path

import pygame


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600

STATE_INTRO = "intro"
STATE_REFRAN = "refran"
STATE_FASE = "fase"
STATE_FINAL = "final"

# Paleta visual compartida con el menú principal.
BACKGROUND_TOP = (65, 48, 40)
BACKGROUND_BOTTOM = (154, 124, 88)

PANEL = (246, 235, 210)
PANEL_BORDER = (97, 70, 48)
PANEL_SHADOW = (38, 28, 24)

CARD = (235, 216, 176)
CARD_SELECTED = (245, 225, 178)
BORDER = (95, 66, 40)
BUTTON_SHADOW = (70, 47, 32)

TEXT = (35, 25, 20)
SECONDARY_TEXT = (95, 76, 58)
TITLE = (255, 241, 205)

GREEN = (30, 130, 60)

DIGITO_OBTENIDO = 7


class Prueba3:
    def __init__(self, screen):
        self.screen = screen

        self.title_font = pygame.font.SysFont("Arial", 50, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 42)
        self.button_font = pygame.font.SysFont("Arial", 34, bold=True)
        self.help_button_font = pygame.font.SysFont("Arial", 44, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 32)
        self.refran_font = pygame.font.SysFont("Arial", 50, bold=True)

        self.continue_rect = pygame.Rect(292, 485, 440, 66)
        self.help_rect = pygame.Rect(895, 52, 64, 64)
        self.menu_rect = pygame.Rect(292, 485, 440, 66)
        self.back_rect = pygame.Rect(55, 485, 80, 60)

        self.base_dir = Path(__file__).resolve().parent.parent
        self.audio_dir = self.base_dir / "assets" / "audios"
        self.silence_path = self.audio_dir / "silencio.wav"

        self.audio_inicio_path = self.audio_dir / "prueba3_inicio.mp3"
        self.audio_final_path = self.audio_dir / "prueba3_final.mp3"

        self.audio_fases = [
            self.audio_dir / "prueba3_fase1.mp3",
            self.audio_dir / "prueba3_fase2.mp3",
            self.audio_dir / "prueba3_fase3.mp3",
        ]

        self.refranes = [
            {
                "texto": "Más vale prevenir que curar.",
                "audio": self.audio_dir / "prueba3_refran1.mp3",
            },
            {
                "texto": "Más vale tarde que nunca.",
                "audio": self.audio_dir / "prueba3_refran2.mp3",
            },
            {
                "texto": "A quien madruga, Dios le ayuda.",
                "audio": self.audio_dir / "prueba3_refran3.mp3",
            },
            {
                "texto": "No hay mal que por bien no venga.",
                "audio": self.audio_dir / "prueba3_refran4.mp3",
            },
            {
                "texto": "El que la sigue la consigue.",
                "audio": self.audio_dir / "prueba3_refran5.mp3",
            },
        ]

        self.fases = [
            {
                "titulo": "Fase 1 — Comprensión",
                "pregunta": "¿Qué creéis que significa este refrán?",
                "ayuda": "Pensad en qué consejo intenta dar este refrán.",
            },
            {
                "titulo": "Fase 2 — Recuerdo personal",
                "pregunta": "¿Recordáis alguna situación de vuestra vida relacionada con este refrán?",
                "ayuda": "Puede ser una experiencia de familia, trabajo, amistad o salud.",
            },
            {
                "titulo": "Fase 3 — Asociación verbal",
                "pregunta": "¿Os recuerda este refrán a otro parecido?",
                "ayuda": "Pensad en otros refranes que hayáis escuchado en casa, en el trabajo o de vuestros mayores.",
            },
        ]

        if not pygame.mixer.get_init():
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()

        self.crear_silencio()
        self.reset()

    def reset(self):
        self.state = STATE_INTRO
        self.selected_refran = None
        self.phase_index = 0
        self.show_help = False

        self.audio_inicio_reproducido = False
        self.audio_refran_reproducido = False
        self.audio_final_reproducido = False
        self.audio_fase_reproducido = [False, False, False]

        pygame.mixer.music.stop()

    def crear_silencio(self):
        if self.silence_path.exists():
            return

        self.audio_dir.mkdir(parents=True, exist_ok=True)

        sample_rate = 44100
        duracion = 0.7

        with wave.open(str(self.silence_path), "w") as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)

            silencio = (0).to_bytes(2, byteorder="little", signed=True)

            for _ in range(int(sample_rate * duracion)):
                wav.writeframes(silencio + silencio)

    def reproducir_audio(self, audio_path):
        if not audio_path.exists():
            print(f"No se ha encontrado el audio: {audio_path}")
            return

        pygame.mixer.music.stop()
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.load(str(self.silence_path))
        pygame.mixer.music.play()
        pygame.mixer.music.queue(str(audio_path))

    def seleccionar_refran(self):
        # Comentario semántico: la selección aleatoria evita que la prueba sea siempre igual.
        self.selected_refran = random.choice(self.refranes)

    def draw_text(self, text, font, color, center):
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=center)
        self.screen.blit(surface, rect)

    def draw_text_with_shadow(self, text, font, color, center):
        shadow_surface = font.render(text, True, (30, 22, 18))
        shadow_rect = shadow_surface.get_rect(center=(center[0] + 3, center[1] + 3))
        self.screen.blit(shadow_surface, shadow_rect)

        surface = font.render(text, True, color)
        rect = surface.get_rect(center=center)
        self.screen.blit(surface, rect)

    def get_wrapped_lines(self, text, font, max_width):
        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "

            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        return lines

    def draw_wrapped_text_centered(self, text, font, color, center_x, y, max_width, line_spacing=8):
        lines = self.get_wrapped_lines(text, font, max_width)

        for line in lines:
            surface = font.render(line, True, color)
            rect = surface.get_rect(center=(center_x, y))
            self.screen.blit(surface, rect)
            y += font.get_height() + line_spacing

        return y

    def draw_wrapped_text_in_rect(self, text, font, color, rect, max_width, line_spacing=8):
        lines = self.get_wrapped_lines(text, font, max_width)
        total_height = len(lines) * font.get_height() + (len(lines) - 1) * line_spacing

        y = rect.centery - total_height // 2

        for line in lines:
            surface = font.render(line, True, color)
            line_rect = surface.get_rect(center=(rect.centerx, y + font.get_height() // 2))
            self.screen.blit(surface, line_rect)
            y += font.get_height() + line_spacing

    def draw_vertical_gradient(self):
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(BACKGROUND_TOP[0] * (1 - ratio) + BACKGROUND_BOTTOM[0] * ratio)
            g = int(BACKGROUND_TOP[1] * (1 - ratio) + BACKGROUND_BOTTOM[1] * ratio)
            b = int(BACKGROUND_TOP[2] * (1 - ratio) + BACKGROUND_BOTTOM[2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def draw_decorative_frame(self):
        outer_rect = pygame.Rect(26, 22, SCREEN_WIDTH - 52, SCREEN_HEIGHT - 44)
        inner_rect = pygame.Rect(38, 34, SCREEN_WIDTH - 76, SCREEN_HEIGHT - 68)

        pygame.draw.rect(self.screen, (232, 205, 150), outer_rect, width=4, border_radius=18)
        pygame.draw.rect(self.screen, (92, 62, 38), inner_rect, width=2, border_radius=14)

        corner_points = [
            (56, 52),
            (SCREEN_WIDTH - 56, 52),
            (56, SCREEN_HEIGHT - 52),
            (SCREEN_WIDTH - 56, SCREEN_HEIGHT - 52),
        ]

        for point in corner_points:
            pygame.draw.circle(self.screen, (232, 205, 150), point, 8)
            pygame.draw.circle(self.screen, (92, 62, 38), point, 8, width=2)

    def draw_panel(self, rect):
        shadow_rect = rect.move(8, 8)

        pygame.draw.rect(self.screen, PANEL_SHADOW, shadow_rect, border_radius=24)
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=24)
        pygame.draw.rect(self.screen, PANEL_BORDER, rect, width=4, border_radius=24)

        inner_rect = rect.inflate(-24, -24)
        pygame.draw.rect(self.screen, (198, 160, 105), inner_rect, width=2, border_radius=18)

    def draw_card(self, rect):
        shadow_rect = rect.move(5, 6)
        pygame.draw.rect(self.screen, BUTTON_SHADOW, shadow_rect, border_radius=18)
        pygame.draw.rect(self.screen, CARD, rect, border_radius=18)
        pygame.draw.rect(self.screen, BORDER, rect, width=3, border_radius=18)

    def draw_background(self):
        self.draw_vertical_gradient()
        self.draw_decorative_frame()

    def draw_button(self, rect, text):
        shadow_rect = rect.move(5, 6)
        pygame.draw.rect(self.screen, BUTTON_SHADOW, shadow_rect, border_radius=18)
        pygame.draw.rect(self.screen, CARD_SELECTED, rect, border_radius=18)
        pygame.draw.rect(self.screen, BORDER, rect, width=3, border_radius=18)
        self.draw_text(text, self.button_font, TEXT, rect.center)

    def draw_help_button(self):
        shadow_rect = self.help_rect.move(4, 5)
        pygame.draw.ellipse(self.screen, BUTTON_SHADOW, shadow_rect)
        pygame.draw.ellipse(self.screen, CARD_SELECTED, self.help_rect)
        pygame.draw.ellipse(self.screen, BORDER, self.help_rect, width=3)
        self.draw_text("?", self.help_button_font, TEXT, self.help_rect.center)

    def draw_back_button(self):
        shadow_rect = self.back_rect.move(4, 5)
        pygame.draw.rect(self.screen, BUTTON_SHADOW, shadow_rect, border_radius=14)
        pygame.draw.rect(self.screen, CARD_SELECTED, self.back_rect, border_radius=14)
        pygame.draw.rect(self.screen, BORDER, self.back_rect, width=3, border_radius=14)
        self.draw_text("←", self.title_font, TEXT, self.back_rect.center)

    def draw(self):
        if self.state == STATE_INTRO:
            self.draw_intro()
        elif self.state == STATE_REFRAN:
            self.draw_refran()
        elif self.state == STATE_FASE:
            self.draw_fase()
        elif self.state == STATE_FINAL:
            self.draw_final()

    def draw_intro(self):
        self.draw_background()

        panel_rect = pygame.Rect(92, 92, 840, 385)
        self.draw_panel(panel_rect)

        self.draw_text(
            "Prueba 3",
            self.button_font,
            SECONDARY_TEXT,
            (SCREEN_WIDTH // 2, 135)
        )

        self.draw_text(
            "¡Vaya refrán!",
            self.title_font,
            TEXT,
            (SCREEN_WIDTH // 2, 190)
        )

        y = 255

        y = self.draw_wrapped_text_centered(
            "Escuchad el refrán con atención.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        y += 10

        y = self.draw_wrapped_text_centered(
            "Después hablaremos sobre su significado",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        y = self.draw_wrapped_text_centered(
            "y sobre recuerdos relacionados.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        y += 18

        self.draw_wrapped_text_centered(
            "Aquí lo importante es participar.",
            self.text_font,
            SECONDARY_TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        if not self.audio_inicio_reproducido:
            self.reproducir_audio(self.audio_inicio_path)
            self.audio_inicio_reproducido = True

        self.draw_button(self.continue_rect, "Comenzar")
        self.draw_back_button()

    def draw_refran(self):
        self.draw_background()

        self.draw_text_with_shadow(
            "Refrán seleccionado",
            self.title_font,
            TITLE,
            (SCREEN_WIDTH // 2, 88)
        )

        refran_rect = pygame.Rect(95, 150, 834, 220)
        self.draw_panel(refran_rect)

        self.draw_wrapped_text_in_rect(
            f"“{self.selected_refran['texto']}”",
            self.refran_font,
            TEXT,
            refran_rect,
            730,
            line_spacing=12
        )

        self.draw_wrapped_text_centered(
            "Cuando termine el audio, podéis continuar.",
            self.text_font,
            TITLE,
            SCREEN_WIDTH // 2,
            420,
            850
        )

        if not self.audio_refran_reproducido:
            self.reproducir_audio(self.selected_refran["audio"])
            self.audio_refran_reproducido = True

        self.draw_button(self.continue_rect, "Continuar")

    def draw_fase(self):
        self.draw_background()

        fase = self.fases[self.phase_index]

        self.draw_text_with_shadow(
            fase["titulo"],
            self.title_font,
            TITLE,
            (SCREEN_WIDTH // 2, 88)
        )

        pregunta_rect = pygame.Rect(95, 135, 834, 205)
        self.draw_panel(pregunta_rect)

        self.draw_wrapped_text_in_rect(
            fase["pregunta"],
            self.text_font,
            TEXT,
            pregunta_rect,
            740,
            line_spacing=12
        )

        if self.show_help:
            pista_rect = pygame.Rect(115, 360, 794, 100)
            self.draw_card(pista_rect)

            self.draw_wrapped_text_in_rect(
                fase["ayuda"],
                self.small_font,
                TEXT,
                pista_rect,
                710,
                line_spacing=8
            )

        if not self.audio_fase_reproducido[self.phase_index]:
            self.reproducir_audio(self.audio_fases[self.phase_index])
            self.audio_fase_reproducido[self.phase_index] = True

        self.draw_help_button()

        if self.phase_index == len(self.fases) - 1:
            self.draw_button(self.continue_rect, "Finalizar prueba")
        else:
            self.draw_button(self.continue_rect, "Continuar")

    def draw_final(self):
        self.draw_background()

        panel_rect = pygame.Rect(100, 90, 824, 365)
        self.draw_panel(panel_rect)

        self.draw_text(
            "Prueba superada",
            self.title_font,
            GREEN,
            (SCREEN_WIDTH // 2, 135)
        )

        self.draw_wrapped_text_centered(
            "Habéis compartido recuerdos",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            190,
            760
        )

        self.draw_wrapped_text_centered(
            "y experiencias.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            240,
            760
        )

        self.draw_wrapped_text_centered(
            "Vuestros recuerdos os han dado",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            300,
            760
        )

        self.draw_wrapped_text_centered(
            "una nueva pista.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            350,
            760
        )

        self.draw_wrapped_text_centered(
            f"Dígito obtenido: {DIGITO_OBTENIDO}",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            410,
            760
        )

        if not self.audio_final_reproducido:
            self.reproducir_audio(self.audio_final_path)
            self.audio_final_reproducido = True

        self.draw_button(self.menu_rect, "Volver al menú")

    def handle_click(self, mouse_pos):
        if self.state == STATE_INTRO:
            if self.back_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                return "menu"

            if self.continue_rect.collidepoint(mouse_pos):
                self.seleccionar_refran()
                self.state = STATE_REFRAN

        elif self.state == STATE_REFRAN:
            if self.continue_rect.collidepoint(mouse_pos):
                self.phase_index = 0
                self.show_help = False
                self.state = STATE_FASE

        elif self.state == STATE_FASE:
            if self.help_rect.collidepoint(mouse_pos):
                self.show_help = True

            elif self.continue_rect.collidepoint(mouse_pos):
                self.show_help = False

                if self.phase_index >= len(self.fases) - 1:
                    self.state = STATE_FINAL
                else:
                    self.phase_index += 1

        elif self.state == STATE_FINAL:
            if self.menu_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                return "menu"

        return None