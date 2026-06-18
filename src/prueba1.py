
import csv
import wave
from datetime import datetime
from pathlib import Path

import pygame
from gpiozero import Button


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600

STATE_INTRO = "intro"
STATE_HISTORIA = "historia"
STATE_PREGUNTA = "pregunta"
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

GREEN = (30, 130, 60)
RED = (180, 40, 40)

OVERLAY = (248, 242, 225)

ERROR_DISPLAY_MS = 8000
DIGITO_OBTENIDO = 3


class Prueba1:
    def __init__(self, screen):
        self.screen = screen

        self.title_font = pygame.font.SysFont("Arial", 50, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 40)
        self.option_font = pygame.font.SysFont("Arial", 36)
        self.button_font = pygame.font.SysFont("Arial", 34, bold=True)
        self.metrics_font = pygame.font.SysFont("Arial", 30)

        self.base_dir = Path(__file__).resolve().parent.parent
        self.audio_dir = self.base_dir / "assets" / "audios"
        self.datos_dir = self.base_dir / "datos"
        self.csv_path = self.datos_dir / "metricas_prueba1.csv"

        self.silence_path = self.audio_dir / "silencio.wav"

        self.audio_inicio_path = self.audio_dir / "prueba1_inicio.mp3"
        self.audio_correcto_path = self.audio_dir / "prueba1_correcto.mp3"
        self.audio_error_path = self.audio_dir / "prueba1_error.mp3"
        self.audio_final_path = self.audio_dir / "prueba1_final.mp3"

        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
        pygame.mixer.init()

        self.crear_silencio()

        self.state = STATE_INTRO
        self.question_index = 0
        self.feedback_correcto = False
        self.feedback_message = ""
        self.feedback_start_time = 0
        self.respuesta_pulsada = None

        self.audio_inicio_reproducido = False
        self.audio_final_reproducido = False
        self.metricas_guardadas = False

        self.boton_a = Button(17, pull_up=True, bounce_time=0.05)
        self.boton_b = Button(27, pull_up=True, bounce_time=0.05)

        self.boton_a.when_pressed = self.pulsado_a
        self.boton_b.when_pressed = self.pulsado_b

        self.questions = [
            {
                "pregunta": "¿Qué ocurrió el día de la boda de Pablo y María?",
                "a": "Carmen robó el anillo de compromiso y lo escondió.",
                "b": "Pablo perdió el anillo mientras se preparaba.",
                "correcta": "A",
                "pista": "Pensad de nuevo en lo que ocurrió con el anillo.",
                "acierto": "Habéis entendido qué problema ocurrió."
            },
            {
                "pregunta": "¿Por qué Carmen robó el anillo?",
                "a": "Porque quería venderlo antes de la ceremonia.",
                "b": "Porque sentía envidia de la relación entre Pablo y María.",
                "correcta": "B",
                "pista": "Recordad cómo se sentía Carmen respecto a Pablo y María.",
                "acierto": "Habéis comprendido el motivo del robo."
            },
            {
                "pregunta": "¿Cuál es la misión de los detectives?",
                "a": "Encontrar el anillo antes de la boda siguiendo las pistas.",
                "b": "Preparar la ceremonia mientras llegan los invitados.",
                "correcta": "A",
                "pista": "Pensad cuál era vuestro objetivo como detectives.",
                "acierto": "Habéis comprendido vuestra misión."
            }
        ]

        self.continue_rect = pygame.Rect(292, 485, 440, 66)
        self.menu_rect = pygame.Rect(292, 485, 440, 66)
        self.back_rect = pygame.Rect(55, 485, 80, 60)

        self.metrics_rect = pygame.Rect(780, 490, 170, 55)
        self.close_metrics_rect = pygame.Rect(845, 85, 45, 45)

        self.reset_metrics()

    def reset(self):
        self.state = STATE_INTRO
        self.question_index = 0
        self.feedback_correcto = False
        self.feedback_message = ""
        self.feedback_start_time = 0
        self.respuesta_pulsada = None

        self.audio_inicio_reproducido = False
        self.audio_final_reproducido = False
        self.metricas_guardadas = False

        self.reset_metrics()

        pygame.mixer.music.stop()

    def reset_metrics(self):
        self.total_errors = 0
        self.attempts_per_question = [0, 0, 0]
        self.errors_per_question = [0, 0, 0]
        self.response_times = [None, None, None]

        self.question_start_time = None
        self.test_start_time = None
        self.final_time = None

        self.show_metrics = False

    def pulsado_a(self):
        self.respuesta_pulsada = "A"

    def pulsado_b(self):
        self.respuesta_pulsada = "B"

    def crear_silencio(self):
        if self.silence_path.exists():
            return

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

    def start_question_timer_if_needed(self):
        if self.test_start_time is None:
            self.test_start_time = pygame.time.get_ticks()

        if self.question_start_time is None:
            self.question_start_time = pygame.time.get_ticks()

    def get_elapsed_seconds(self, start, end):
        if start is None or end is None:
            return 0

        return round((end - start) / 1000, 1)

    def guardar_metricas_csv(self):
        if self.metricas_guardadas:
            return

        self.datos_dir.mkdir(parents=True, exist_ok=True)

        archivo_existe = self.csv_path.exists()
        tiempo_total = self.get_elapsed_seconds(self.test_start_time, self.final_time)

        fila = {
            "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "prueba": "Prueba 1 - La Gran Pregunta",
            "prueba_completada": "si",
            "errores_totales": self.total_errors,
            "errores_pregunta_1": self.errors_per_question[0],
            "errores_pregunta_2": self.errors_per_question[1],
            "errores_pregunta_3": self.errors_per_question[2],
            "intentos_pregunta_1": self.attempts_per_question[0],
            "intentos_pregunta_2": self.attempts_per_question[1],
            "intentos_pregunta_3": self.attempts_per_question[2],
            "tiempo_pregunta_1_s": self.response_times[0],
            "tiempo_pregunta_2_s": self.response_times[1],
            "tiempo_pregunta_3_s": self.response_times[2],
            "tiempo_total_preguntas_s": tiempo_total,
        }

        with open(self.csv_path, mode="a", newline="", encoding="utf-8") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=fila.keys())

            if not archivo_existe:
                writer.writeheader()

            writer.writerow(fila)

        self.metricas_guardadas = True

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

    def draw_wrapped_text(self, text, font, color, x, y, max_width, line_spacing=8):
        words = text.split(" ")
        current_line = ""

        for word in words:
            test_line = current_line + word + " "

            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                surface = font.render(current_line.strip(), True, color)
                self.screen.blit(surface, (x, y))
                y += font.get_height() + line_spacing
                current_line = word + " "

        if current_line:
            surface = font.render(current_line.strip(), True, color)
            self.screen.blit(surface, (x, y))
            y += font.get_height() + line_spacing

        return y

    def draw_wrapped_text_centered(self, text, font, color, center_x, y, max_width, line_spacing=8):
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

        for line in lines:
            surface = font.render(line, True, color)
            rect = surface.get_rect(center=(center_x, y))
            self.screen.blit(surface, rect)
            y += font.get_height() + line_spacing

        return y

    def draw_wrapped_text_in_rect(self, text, font, color, rect, max_width, line_spacing=6):
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

        total_height = len(lines) * font.get_height() + (len(lines) - 1) * line_spacing
        y = rect.centery - total_height // 2

        for line in lines:
            surface = font.render(line, True, color)
            text_rect = surface.get_rect(center=(rect.centerx, y + font.get_height() // 2))
            self.screen.blit(surface, text_rect)
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

    def draw(self):
        self.process_physical_buttons()
        self.process_automatic_return()

        if self.state == STATE_INTRO:
            self.draw_intro()
        elif self.state == STATE_HISTORIA:
            self.draw_historia()
        elif self.state == STATE_PREGUNTA:
            self.draw_pregunta()
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
            "Prueba 1",
            self.button_font,
            SECONDARY_TEXT,
            (SCREEN_WIDTH // 2, 135)
        )

        self.draw_text(
            "El misterio del anillo",
            self.title_font,
            TEXT,
            (SCREEN_WIDTH // 2, 190)
        )

        y = 255
        y = self.draw_wrapped_text_centered(
            "Escuchad atentamente la historia.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        y += 12
        y = self.draw_wrapped_text_centered(
            "Después responderéis tres preguntas.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        y += 25
        self.draw_wrapped_text_centered(
            "La persona responsable leerá la historia en voz alta.",
            self.text_font,
            SECONDARY_TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        if not self.audio_inicio_reproducido:
            self.reproducir_audio(self.audio_inicio_path)
            self.audio_inicio_reproducido = True

        self.draw_button(self.continue_rect, "Continuar")
        self.draw_back_button()

    def draw_historia(self):
        self.draw_background()

        panel_rect = pygame.Rect(90, 80, 844, 400)
        self.draw_panel(panel_rect)

        self.draw_text(
            "Historia en curso...",
            self.title_font,
            TEXT,
            (SCREEN_WIDTH // 2, 130)
        )

        y = 190
        y = self.draw_wrapped_text("Prestad atención a:", self.text_font, TEXT, 155, y, 760)
        y += 15
        y = self.draw_wrapped_text("• qué ha ocurrido,", self.text_font, TEXT, 190, y, 760)
        y = self.draw_wrapped_text("• quién ha robado el anillo,", self.text_font, TEXT, 190, y, 760)
        y = self.draw_wrapped_text("• por qué lo ha hecho,", self.text_font, TEXT, 190, y, 760)
        self.draw_wrapped_text("• cuál es vuestra misión.", self.text_font, TEXT, 190, y, 760)

        self.draw_button(self.continue_rect, "Comenzar preguntas")
        self.draw_back_button()

    def draw_pregunta(self):
        self.start_question_timer_if_needed()

        self.draw_background()

        question = self.questions[self.question_index]

        self.draw_text_with_shadow(
            f"Pregunta {self.question_index + 1} de 3",
            self.title_font,
            TITLE,
            (SCREEN_WIDTH // 2, 62)
        )

        question_panel = pygame.Rect(70, 100, 884, 120)
        self.draw_panel(question_panel)

        self.draw_wrapped_text_in_rect(
            question["pregunta"],
            self.text_font,
            TEXT,
            question_panel,
            810
        )

        rect_a = pygame.Rect(70, 245, 884, 105)
        self.draw_card(rect_a)
        self.draw_wrapped_text_in_rect(
            "A) " + question["a"],
            self.option_font,
            TEXT,
            rect_a,
            800
        )

        rect_b = pygame.Rect(70, 375, 884, 105)
        self.draw_card(rect_b)
        self.draw_wrapped_text_in_rect(
            "B) " + question["b"],
            self.option_font,
            TEXT,
            rect_b,
            800
        )

        self.draw_text(
            "Responded usando los botones físicos A o B",
            self.button_font,
            TITLE,
            (SCREEN_WIDTH // 2, 520)
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

        self.draw_wrapped_text_centered(
            self.feedback_message,
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            245,
            730
        )

        if self.feedback_correcto:
            self.draw_button(self.continue_rect, "Continuar")
        else:
            self.draw_wrapped_text_centered(
                "La pregunta volverá a aparecer automáticamente.",
                self.button_font,
                TITLE,
                SCREEN_WIDTH // 2,
                485,
                850
            )

    def draw_final(self):
        self.draw_background()

        self.guardar_metricas_csv()

        panel_rect = pygame.Rect(100, 90, 824, 365)
        self.draw_panel(panel_rect)

        self.draw_text(
            "Prueba superada",
            self.title_font,
            GREEN,
            (SCREEN_WIDTH // 2, 135)
        )

        self.draw_wrapped_text_centered(
            "Habéis demostrado atención",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            205,
            760
        )

        self.draw_wrapped_text_centered(
            "y comprensión.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            255,
            760
        )

        self.draw_wrapped_text_centered(
            "Habéis conseguido una nueva pista.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            325,
            760
        )

        self.draw_wrapped_text_centered(
            f"Dígito obtenido: {DIGITO_OBTENIDO}",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            390,
            760
        )

        if not self.audio_final_reproducido:
            self.reproducir_audio(self.audio_final_path)
            self.audio_final_reproducido = True

        self.draw_button(self.menu_rect, "Volver al menú")
        self.draw_button(self.metrics_rect, "Métricas")

    def draw_metrics_popup(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 145))
        self.screen.blit(overlay, (0, 0))

        popup_rect = pygame.Rect(110, 70, 804, 460)

        pygame.draw.rect(self.screen, PANEL_SHADOW, popup_rect.move(8, 8), border_radius=22)
        pygame.draw.rect(self.screen, OVERLAY, popup_rect, border_radius=22)
        pygame.draw.rect(self.screen, BORDER, popup_rect, width=4, border_radius=22)

        inner_rect = popup_rect.inflate(-24, -24)
        pygame.draw.rect(self.screen, (198, 160, 105), inner_rect, width=2, border_radius=16)

        pygame.draw.rect(self.screen, RED, self.close_metrics_rect, border_radius=12)
        pygame.draw.rect(self.screen, BORDER, self.close_metrics_rect, width=3, border_radius=12)
        self.draw_text("X", self.button_font, TITLE, self.close_metrics_rect.center)

        self.draw_text(
            "Métricas de la prueba",
            self.title_font,
            TEXT,
            (SCREEN_WIDTH // 2, 120)
        )

        total_time = self.get_elapsed_seconds(self.test_start_time, self.final_time)

        metricas = [
            "Prueba completada: sí",
            f"Errores totales: {self.total_errors}",
            f"Tiempo total de preguntas: {total_time} s",
            f"Intentos pregunta 1: {self.attempts_per_question[0]}",
            f"Intentos pregunta 2: {self.attempts_per_question[1]}",
            f"Intentos pregunta 3: {self.attempts_per_question[2]}",
            f"Tiempo pregunta 1: {self.response_times[0]} s",
            f"Tiempo pregunta 2: {self.response_times[1]} s",
            f"Tiempo pregunta 3: {self.response_times[2]} s",
        ]

        y = 175
        for metrica in metricas:
            surface = self.metrics_font.render(metrica, True, TEXT)
            self.screen.blit(surface, (180, y))
            y += 34

    def handle_click(self, mouse_pos):
        if self.show_metrics:
            if self.close_metrics_rect.collidepoint(mouse_pos):
                self.show_metrics = False
            return None

        if self.state in [STATE_INTRO, STATE_HISTORIA]:
            if self.back_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                return "menu"

        if self.state == STATE_INTRO:
            if self.continue_rect.collidepoint(mouse_pos):
                self.state = STATE_HISTORIA

        elif self.state == STATE_HISTORIA:
            if self.continue_rect.collidepoint(mouse_pos):
                self.state = STATE_PREGUNTA

        elif self.state == STATE_FEEDBACK:
            if self.feedback_correcto and self.continue_rect.collidepoint(mouse_pos):
                self.question_index += 1
                self.question_start_time = None

                if self.question_index >= len(self.questions):
                    self.final_time = pygame.time.get_ticks()
                    self.state = STATE_FINAL
                else:
                    self.state = STATE_PREGUNTA

        elif self.state == STATE_FINAL:
            if self.menu_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                return "menu"

            if self.metrics_rect.collidepoint(mouse_pos):
                self.show_metrics = True

        return None

    def process_physical_buttons(self):
        if self.state != STATE_PREGUNTA:
            self.respuesta_pulsada = None
            return

        if self.respuesta_pulsada is None:
            return

        question = self.questions[self.question_index]

        self.attempts_per_question[self.question_index] += 1

        if self.respuesta_pulsada == question["correcta"]:
            self.feedback_correcto = True
            self.feedback_message = question["acierto"]
            self.reproducir_audio(self.audio_correcto_path)

            now = pygame.time.get_ticks()
            self.response_times[self.question_index] = self.get_elapsed_seconds(
                self.question_start_time,
                now
            )
        else:
            self.feedback_correcto = False
            self.feedback_message = question["pista"]
            self.reproducir_audio(self.audio_error_path)

            self.total_errors += 1
            self.errors_per_question[self.question_index] += 1

        self.feedback_start_time = pygame.time.get_ticks()
        self.respuesta_pulsada = None
        self.state = STATE_FEEDBACK

    def process_automatic_return(self):
        if self.state != STATE_FEEDBACK:
            return

        if self.feedback_correcto:
            return

        elapsed_time = pygame.time.get_ticks() - self.feedback_start_time

        if elapsed_time >= ERROR_DISPLAY_MS:
            self.state = STATE_PREGUNTA