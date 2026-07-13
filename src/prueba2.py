import random
import wave
from pathlib import Path

import pygame
from gpiozero import Button, LED


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600

STATE_INTRO = "intro"
STATE_LEVEL_READY = "level_ready"
STATE_SHOW_SEQUENCE = "show_sequence"
STATE_WAIT_RESPONSE = "wait_response"
STATE_PENDING_FEEDBACK = "pending_feedback"
STATE_FEEDBACK = "feedback"
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

OVERLAY = (248, 242, 225)

GREEN = (30, 130, 60)
RED = (180, 40, 40)
BLUE = (40, 90, 180)
YELLOW = (210, 160, 20)

COLOR_MAP = {
    "rojo": RED,
    "azul": BLUE,
    "verde": GREEN,
    "amarillo": YELLOW,
}

SEQUENCE_NORMAL_ON_MS = 900
SEQUENCE_NORMAL_OFF_MS = 450

SEQUENCE_SLOW_ON_MS = 1500
SEQUENCE_SLOW_OFF_MS = 750

PENDING_FEEDBACK_MS = 700

DIGITO_OBTENIDO = 27  


class Prueba2:
    def __init__(self, screen):
        self.screen = screen

        self.title_font = pygame.font.SysFont("Arial", 50, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 40)
        self.button_font = pygame.font.SysFont("Arial", 34, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 30)
        self.metrics_font = pygame.font.SysFont("Arial", 26)

        self.continue_rect = pygame.Rect(292, 485, 440, 66)
        self.back_rect = pygame.Rect(55, 485, 80, 60)
        self.menu_rect = pygame.Rect(292, 485, 440, 66)

        self.metrics_rect = pygame.Rect(780, 490, 170, 55)
        self.close_metrics_rect = pygame.Rect(845, 85, 45, 45)

        self.base_dir = Path(__file__).resolve().parent.parent
        self.audio_dir = self.base_dir / "assets" / "audios"

        self.silence_path = self.audio_dir / "silencio.wav"

        self.audio_inicio_path = self.audio_dir / "prueba2_inicio.mp3"
        self.audio_correcto_path = self.audio_dir / "prueba2_correcto.mp3"
        self.audio_error_path = self.audio_dir / "prueba2_error.mp3"
        self.audio_lento_path = self.audio_dir / "prueba2_lento.mp3"
        self.audio_ayuda_path = self.audio_dir / "prueba2_ayuda.mp3"
        self.audio_final_path = self.audio_dir / "prueba2_final.mp3"

        if not pygame.mixer.get_init():
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()

        self.crear_silencio()

        # Comentario semántico: cada botón físico representa un color de la secuencia.
        self.boton_rojo = Button(5, pull_up=True, bounce_time=0.08)
        self.boton_azul = Button(6, pull_up=True, bounce_time=0.08)
        self.boton_verde = Button(13, pull_up=True, bounce_time=0.08)
        self.boton_amarillo = Button(19, pull_up=True, bounce_time=0.08)

        self.boton_rojo.when_pressed = self.pulsado_rojo
        self.boton_azul.when_pressed = self.pulsado_azul
        self.boton_verde.when_pressed = self.pulsado_verde
        self.boton_amarillo.when_pressed = self.pulsado_amarillo

        # Comentario semántico: cada LED físico muestra el estímulo visual de su color.
        self.led_rojo = LED(12)
        self.led_azul = LED(16)
        self.led_verde = LED(20)
        self.led_amarillo = LED(21)

        self.leds = {
            "rojo": self.led_rojo,
            "azul": self.led_azul,
            "verde": self.led_verde,
            "amarillo": self.led_amarillo,
        }

        self.reset()

    def reset(self):
        self.apagar_leds()

        self.state = STATE_INTRO
        self.level = 1
        self.sequence = []
        self.user_sequence = []

        self.sequence_index = 0
        self.showing_light = False
        self.sequence_timer = 0
        self.current_color = None
        self.sequence_is_slow = False

        self.feedback_correcto = False
        self.feedback_message = ""
        self.feedback_button_text = "Continuar"

        self.color_pulsado = None

        self.failures_current_level = 0
        self.help_used_current_level = False

        self.audio_inicio_reproducido = False
        self.audio_final_reproducido = False

        self.pending_feedback_start_time = 0
        self.pending_audio_path = None

        self.show_metrics = False

        self.reset_metrics()

        pygame.mixer.music.stop()

    def reset_metrics(self):
        self.test_start_time = None
        self.final_time = None
        self.level_start_time = None

        self.level_times = [None, None, None]
        self.attempts_per_level = [0, 0, 0]
        self.errors_per_level = [0, 0, 0]
        self.help_used_per_level = [False, False, False]
        self.sequences_per_level = ["", "", ""]
        self.last_response_per_level = ["", "", ""]

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

    def apagar_leds(self):
        for led in self.leds.values():
            led.off()

    def encender_led_color(self, color):
        self.apagar_leds()
        self.leds[color].on()

    def pulsado_rojo(self):
        self.color_pulsado = "rojo"

    def pulsado_azul(self):
        self.color_pulsado = "azul"

    def pulsado_verde(self):
        self.color_pulsado = "verde"

    def pulsado_amarillo(self):
        self.color_pulsado = "amarillo"

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

    def draw_back_button(self):
        shadow_rect = self.back_rect.move(4, 5)
        pygame.draw.rect(self.screen, BUTTON_SHADOW, shadow_rect, border_radius=14)
        pygame.draw.rect(self.screen, CARD_SELECTED, self.back_rect, border_radius=14)
        pygame.draw.rect(self.screen, BORDER, self.back_rect, width=3, border_radius=14)
        self.draw_text("←", self.title_font, TEXT, self.back_rect.center)

    def get_sequence_length(self):
        return self.level + 1

    def get_current_on_time(self):
        if self.sequence_is_slow:
            return SEQUENCE_SLOW_ON_MS
        return SEQUENCE_NORMAL_ON_MS

    def get_current_off_time(self):
        if self.sequence_is_slow:
            return SEQUENCE_SLOW_OFF_MS
        return SEQUENCE_NORMAL_OFF_MS

    def get_elapsed_seconds(self, start, end):
        if start is None or end is None:
            return 0

        return round((end - start) / 1000, 1)

    def generate_sequence(self):
        colores = ["rojo", "azul", "verde", "amarillo"]
        self.sequence = random.choices(colores, k=self.get_sequence_length())
        self.user_sequence = []

        level_index = self.level - 1
        self.sequences_per_level[level_index] = " → ".join(self.sequence)

    def prepare_new_level(self):
        self.sequence = []
        self.user_sequence = []
        self.failures_current_level = 0
        self.help_used_current_level = False
        self.sequence_is_slow = False
        self.level_start_time = None
        self.state = STATE_LEVEL_READY

    def start_sequence_display(self, generate_new_sequence):
        if self.test_start_time is None:
            self.test_start_time = pygame.time.get_ticks()

        if self.level_start_time is None:
            self.level_start_time = pygame.time.get_ticks()

        if generate_new_sequence:
            self.generate_sequence()

        self.sequence_index = 0
        self.showing_light = True
        self.current_color = self.sequence[0]
        self.sequence_timer = pygame.time.get_ticks()
        self.user_sequence = []
        self.color_pulsado = None

        self.encender_led_color(self.current_color)

        self.state = STATE_SHOW_SEQUENCE

    def process_sequence_display(self):
        if self.state != STATE_SHOW_SEQUENCE:
            return

        now = pygame.time.get_ticks()
        elapsed = now - self.sequence_timer

        if self.showing_light:
            if elapsed >= self.get_current_on_time():
                self.showing_light = False
                self.current_color = None
                self.sequence_timer = now
                self.apagar_leds()
        else:
            if elapsed >= self.get_current_off_time():
                self.sequence_index += 1

                if self.sequence_index >= len(self.sequence):
                    self.current_color = None
                    self.user_sequence = []
                    self.color_pulsado = None
                    self.apagar_leds()
                    self.state = STATE_WAIT_RESPONSE
                else:
                    self.showing_light = True
                    self.current_color = self.sequence[self.sequence_index]
                    self.sequence_timer = now
                    self.encender_led_color(self.current_color)

    def set_pending_feedback(self, audio_path):
        self.pending_audio_path = audio_path
        self.pending_feedback_start_time = pygame.time.get_ticks()
        self.state = STATE_PENDING_FEEDBACK

    def process_pending_feedback(self):
        if self.state != STATE_PENDING_FEEDBACK:
            return

        elapsed = pygame.time.get_ticks() - self.pending_feedback_start_time

        if elapsed >= PENDING_FEEDBACK_MS:
            if self.pending_audio_path is not None:
                self.reproducir_audio(self.pending_audio_path)

            self.pending_audio_path = None
            self.state = STATE_FEEDBACK

    def close_level_metrics(self):
        level_index = self.level - 1
        now = pygame.time.get_ticks()

        self.level_times[level_index] = self.get_elapsed_seconds(
            self.level_start_time,
            now
        )

        self.help_used_per_level[level_index] = self.help_used_current_level

    def register_attempt(self):
        level_index = self.level - 1
        self.attempts_per_level[level_index] += 1
        self.last_response_per_level[level_index] = " → ".join(self.user_sequence)

    def process_physical_buttons(self):
        if self.state != STATE_WAIT_RESPONSE:
            self.color_pulsado = None
            return

        if self.color_pulsado is None:
            return

        selected_color = self.color_pulsado
        self.color_pulsado = None

        self.user_sequence.append(selected_color)

        expected_color = self.sequence[len(self.user_sequence) - 1]

        if selected_color != expected_color:
            level_index = self.level - 1

            self.register_attempt()

            self.failures_current_level += 1
            self.errors_per_level[level_index] += 1
            self.feedback_correcto = False
            self.apagar_leds()

            if self.failures_current_level == 1:
                self.feedback_message = "La secuencia no coincide. Vamos a intentarlo de nuevo."
                self.feedback_button_text = "Repetir secuencia"
                self.set_pending_feedback(self.audio_error_path)

            elif self.failures_current_level == 2:
                self.feedback_message = "Vamos a repetir la misma secuencia más despacio."
                self.feedback_button_text = "Repetir despacio"
                self.sequence_is_slow = True
                self.set_pending_feedback(self.audio_lento_path)

            else:
                self.feedback_message = "La persona responsable puede ayudar y continuar con el siguiente nivel."
                self.feedback_button_text = "Continuar con ayuda"
                self.help_used_current_level = True
                self.close_level_metrics()
                self.set_pending_feedback(self.audio_ayuda_path)

            return

        if len(self.user_sequence) == len(self.sequence):
            self.register_attempt()
            self.close_level_metrics()

            self.feedback_correcto = True
            self.feedback_message = "Habéis repetido correctamente la secuencia."
            self.feedback_button_text = "Continuar"
            self.apagar_leds()
            self.set_pending_feedback(self.audio_correcto_path)

    def advance_to_next_level(self):
        self.level += 1

        if self.level > 3:
            self.final_time = pygame.time.get_ticks()
            self.state = STATE_FINAL
        else:
            self.prepare_new_level()

    def draw_color_panel(self):
        positions = {
            "rojo": pygame.Rect(235, 175, 220, 110),
            "azul": pygame.Rect(570, 175, 220, 110),
            "verde": pygame.Rect(235, 330, 220, 110),
            "amarillo": pygame.Rect(570, 330, 220, 110),
        }

        for color_name, rect in positions.items():
            shadow_rect = rect.move(5, 6)
            pygame.draw.rect(self.screen, BUTTON_SHADOW, shadow_rect, border_radius=18)

            if color_name == self.current_color:
                fill = COLOR_MAP[color_name]
            else:
                fill = CARD

            pygame.draw.rect(self.screen, fill, rect, border_radius=18)
            pygame.draw.rect(self.screen, BORDER, rect, width=3, border_radius=18)

            self.draw_text(color_name.capitalize(), self.button_font, TEXT, rect.center)

    def draw(self):
        self.process_sequence_display()
        self.process_physical_buttons()
        self.process_pending_feedback()

        if self.state == STATE_INTRO:
            self.draw_intro()
        elif self.state == STATE_LEVEL_READY:
            self.draw_level_ready()
        elif self.state == STATE_SHOW_SEQUENCE:
            self.draw_show_sequence()
        elif self.state == STATE_WAIT_RESPONSE:
            self.draw_wait_response()
        elif self.state == STATE_PENDING_FEEDBACK:
            self.draw_wait_response()
        elif self.state == STATE_FEEDBACK:
            self.draw_feedback()
        elif self.state == STATE_FINAL:
            self.draw_final()

        if self.show_metrics:
            self.draw_metrics_popup()

    def draw_intro(self):
        self.draw_background()

        panel_rect = pygame.Rect(92, 92, 840, 385)
        self.draw_panel(panel_rect)

        self.draw_text(
            "Prueba 2",
            self.button_font,
            SECONDARY_TEXT,
            (SCREEN_WIDTH // 2, 135)
        )

        self.draw_text(
            "Las luces de la iglesia",
            self.title_font,
            TEXT,
            (SCREEN_WIDTH // 2, 190)
        )

        y = 255

        y = self.draw_wrapped_text_centered(
            "Observad la secuencia de colores.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        y += 12

        y = self.draw_wrapped_text_centered(
            "Después tendréis que repetirla",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        y = self.draw_wrapped_text_centered(
            "usando los botones físicos.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        y += 16

        self.draw_wrapped_text_centered(
            "La prueba tendrá tres niveles de dificultad.",
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

    def draw_level_ready(self):
        self.draw_background()

        panel_rect = pygame.Rect(112, 105, 800, 320)
        self.draw_panel(panel_rect)

        self.draw_text(
            f"Nivel {self.level} de 3",
            self.title_font,
            TEXT,
            (SCREEN_WIDTH // 2, 165)
        )

        self.draw_wrapped_text_centered(
            f"La secuencia tendrá {self.get_sequence_length()} colores.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            245,
            740
        )

        self.draw_wrapped_text_centered(
            "Cuando estéis preparados, comenzamos.",
            self.text_font,
            SECONDARY_TEXT,
            SCREEN_WIDTH // 2,
            320,
            740
        )

        self.draw_button(self.continue_rect, "Mostrar secuencia")

    def draw_show_sequence(self):
        self.draw_background()

        if self.sequence_is_slow:
            title = "Memorizad el orden despacio"
        else:
            title = "Memorizad el orden"

        self.draw_text_with_shadow(
            title,
            self.title_font,
            TITLE,
            (SCREEN_WIDTH // 2, 92)
        )

        self.draw_color_panel()

    def draw_wait_response(self):
        self.draw_background()

        self.draw_text_with_shadow(
            "Ahora repetid la secuencia",
            self.title_font,
            TITLE,
            (SCREEN_WIDTH // 2, 90)
        )

        self.draw_color_panel()

        self.draw_wrapped_text_centered(
            "Usad los botones físicos de colores.",
            self.small_font,
            TITLE,
            SCREEN_WIDTH // 2,
            492,
            900
        )

        respuesta = " → ".join(self.user_sequence)

        if respuesta:
            self.draw_wrapped_text_centered(
                respuesta,
                self.small_font,
                TITLE,
                SCREEN_WIDTH // 2,
                535,
                900
            )

    def draw_feedback(self):
        self.draw_background()

        panel_rect = pygame.Rect(112, 105, 800, 340)
        self.draw_panel(panel_rect)

        if self.feedback_correcto:
            title = "Correcto"
            title_color = GREEN
        else:
            title = "No es correcto"
            title_color = RED

        self.draw_text(
            title,
            self.title_font,
            title_color,
            (SCREEN_WIDTH // 2, 165)
        )

        feedback_rect = pygame.Rect(150, 220, 724, 150)
        self.draw_wrapped_text_in_rect(
            self.feedback_message,
            self.text_font,
            TEXT,
            feedback_rect,
            680,
            line_spacing=8
        )

        self.draw_button(self.continue_rect, self.feedback_button_text)

    def draw_final(self):
        self.draw_background()

        self.apagar_leds()

        panel_rect = pygame.Rect(100, 90, 824, 365)
        self.draw_panel(panel_rect)

        self.draw_text(
            "Prueba superada",
            self.title_font,
            GREEN,
            (SCREEN_WIDTH // 2, 145)
        )

        self.draw_wrapped_text_centered(
            "Habéis completado la secuencia",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            240,
            760
        )

        self.draw_wrapped_text_centered(
            "de colores.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            290,
            760
        )

        self.draw_wrapped_text_centered(
            f"Código obtenido: {DIGITO_OBTENIDO}",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            365,
            760
        )

        if not self.audio_final_reproducido:
            self.reproducir_audio(self.audio_final_path)
            self.audio_final_reproducido = True

        self.draw_button(self.menu_rect, "Volver al menú")
        self.draw_button(self.metrics_rect, "Métricas")

    def draw_metrics_popup(self):
        popup_rect = pygame.Rect(80, 55, 864, 490)

        pygame.draw.rect(self.screen, PANEL_SHADOW, popup_rect.move(8, 8), border_radius=22)
        pygame.draw.rect(self.screen, OVERLAY, popup_rect, border_radius=22)
        pygame.draw.rect(self.screen, BORDER, popup_rect, width=4, border_radius=22)

        inner_rect = popup_rect.inflate(-24, -24)
        pygame.draw.rect(self.screen, (198, 160, 105), inner_rect, width=2, border_radius=16)

        pygame.draw.rect(self.screen, CARD_SELECTED, self.close_metrics_rect, border_radius=10)
        pygame.draw.rect(self.screen, BORDER, self.close_metrics_rect, width=3, border_radius=10)
        self.draw_text("X", self.button_font, TEXT, self.close_metrics_rect.center)

        self.draw_text(
            "Resumen de la prueba",
            self.title_font,
            TEXT,
            (SCREEN_WIDTH // 2, 105)
        )

        tiempo_total = self.get_elapsed_seconds(self.test_start_time, self.final_time)
        errores_totales = sum(self.errors_per_level)
        intentos_totales = sum(self.attempts_per_level)
        ayudas_totales = sum(1 for ayuda in self.help_used_per_level if ayuda)

        metricas = [
            "Prueba completada: sí",
            f"Tiempo total: {tiempo_total} s",
            f"Intentos totales: {intentos_totales}",
            f"Errores totales: {errores_totales}",
            f"Niveles con ayuda: {ayudas_totales}",
            "",
            f"Nivel 1 | intentos: {self.attempts_per_level[0]} | errores: {self.errors_per_level[0]} | ayuda: {'sí' if self.help_used_per_level[0] else 'no'} | tiempo: {self.level_times[0]} s",
            f"Secuencia N1: {self.sequences_per_level[0]}",
            f"Última respuesta N1: {self.last_response_per_level[0]}",
            "",
            f"Nivel 2 | intentos: {self.attempts_per_level[1]} | errores: {self.errors_per_level[1]} | ayuda: {'sí' if self.help_used_per_level[1] else 'no'} | tiempo: {self.level_times[1]} s",
            f"Secuencia N2: {self.sequences_per_level[1]}",
            f"Última respuesta N2: {self.last_response_per_level[1]}",
            "",
            f"Nivel 3 | intentos: {self.attempts_per_level[2]} | errores: {self.errors_per_level[2]} | ayuda: {'sí' if self.help_used_per_level[2] else 'no'} | tiempo: {self.level_times[2]} s",
            f"Secuencia N3: {self.sequences_per_level[2]}",
            f"Última respuesta N3: {self.last_response_per_level[2]}",
        ]

        y = 145
        for metrica in metricas:
            if metrica == "":
                y += 10
                continue

            surface = self.metrics_font.render(metrica, True, TEXT)
            self.screen.blit(surface, (115, y))
            y += 25

    def handle_click(self, mouse_pos):
        if self.show_metrics:
            if self.close_metrics_rect.collidepoint(mouse_pos):
                self.show_metrics = False
            return None

        if self.state == STATE_INTRO:
            if self.back_rect.collidepoint(mouse_pos):
                self.apagar_leds()
                pygame.mixer.music.stop()
                return "menu"

            if self.continue_rect.collidepoint(mouse_pos):
                self.prepare_new_level()

        elif self.state == STATE_LEVEL_READY:
            if self.continue_rect.collidepoint(mouse_pos):
                self.sequence_is_slow = False
                self.start_sequence_display(generate_new_sequence=True)

        elif self.state == STATE_FEEDBACK:
            if self.continue_rect.collidepoint(mouse_pos):
                if self.feedback_correcto:
                    self.advance_to_next_level()

                elif self.failures_current_level >= 3:
                    self.advance_to_next_level()

                else:
                    self.start_sequence_display(generate_new_sequence=False)

        elif self.state == STATE_FINAL:
            if self.menu_rect.collidepoint(mouse_pos):
                self.apagar_leds()
                pygame.mixer.music.stop()
                return "menu"

            if self.metrics_rect.collidepoint(mouse_pos):
                self.show_metrics = True

        return None

    def handle_keydown(self, key):
        return