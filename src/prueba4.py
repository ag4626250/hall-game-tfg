import random
import time
import wave
from pathlib import Path

import pygame


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600

STATE_INTRO = "intro"
STATE_DIFICULTAD = "dificultad"
STATE_PRUEBA = "prueba"
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

MCP23017_ADDRESS = 0x27

# Cambiar estos valores por el número real de bancos y vidrieras de la iglesia.
NUM_BANCOS = 6
NUM_VIDRIERAS = 8

DIGITO_OBTENIDO = 9


class Prueba4:
    def __init__(self, screen):
        self.screen = screen

        self.title_font = pygame.font.SysFont("Arial", 50, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 42)
        self.button_font = pygame.font.SysFont("Arial", 34, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 32)
        self.result_font = pygame.font.SysFont("Arial", 52, bold=True)

        self.continue_rect = pygame.Rect(292, 485, 440, 66)
        self.back_rect = pygame.Rect(55, 485, 80, 60)
        self.metrics_rect = pygame.Rect(780, 490, 170, 55)
        self.menu_rect = pygame.Rect(292, 485, 440, 66)
        self.metrics_close_rect = pygame.Rect(776, 102, 50, 50)

        self.easy_rect = pygame.Rect(292, 220, 440, 70)
        self.medium_rect = pygame.Rect(292, 320, 440, 70)
        self.hard_rect = pygame.Rect(292, 420, 440, 70)

        self.base_dir = Path(__file__).resolve().parent.parent
        self.audio_dir = self.base_dir / "assets" / "audios"
        self.silence_path = self.audio_dir / "silencio.wav"

        self.audio_inicio_path = self.audio_dir / "prueba4_inicio.mp3"
        self.audio_correcto_path = self.audio_dir / "prueba4_correcto.mp3"
        self.audio_error_path = self.audio_dir / "prueba4_error.mp3"
        self.audio_final_path = self.audio_dir / "prueba4_final.mp3"

        self.image_dir = self.base_dir / "assets" / "imagenes"

        self.ramo_img = self.cargar_imagen("ramo.png", (82, 82))
        self.banco_img = self.cargar_imagen("banco.png", (110, 110))
        self.vidriera_img = self.cargar_imagen("vidriera.png", (103, 103))

        if not pygame.mixer.get_init():
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()

        self.crear_silencio()
        self.setup_keypad()
        self.reset()

    def setup_keypad(self):
        self.keypad_available = False

        try:
            import smbus

            self.bus = smbus.SMBus(1)

            self.IODIRA = 0x00
            self.GPPUA = 0x0C
            self.GPIOA = 0x12

            # PA0-PA3 como salidas para filas, PA4-PA7 como entradas para columnas.
            self.bus.write_byte_data(MCP23017_ADDRESS, self.IODIRA, 0b11110000)

            # Comentario semántico: activamos pull-up en columnas para detectar pulsación como nivel bajo.
            self.bus.write_byte_data(MCP23017_ADDRESS, self.GPPUA, 0b11110000)

            self.keypad_available = True

        except ImportError:
            print("Falta instalar smbus. Ejecuta: sudo apt install -y python3-smbus")

        except Exception as error:
            print(f"No se ha podido inicializar el teclado MCP23017: {error}")

        self.key_is_down = False
        self.last_pressed_key = None
        self.last_key_time = 0

    def reset(self):
        self.state = STATE_INTRO

        self.dificultad = None
        self.ramo = None
        self.resultado_correcto = None
        self.resultado_introducido = ""

        self.feedback_correcto = False
        self.feedback_message = ""

        self.audio_inicio_reproducido = False
        self.audio_final_reproducido = False

        self.respuestas_introducidas = []
        self.intentos_totales = 0
        self.num_borrados = 0
        self.num_digitos_introducidos = 0

        self.tiempo_inicio = None
        self.tiempo_fin = None
        self.completada = False

        self.show_metrics_popup = False

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

    def cargar_imagen(self, filename, size):
        image_path = self.image_dir / filename

        if not image_path.exists():
            print(f"No se ha encontrado la imagen: {image_path}")
            return None

        image = pygame.image.load(str(image_path)).convert_alpha()
        return pygame.transform.smoothscale(image, size)

    def configurar_prueba(self, dificultad):
        self.dificultad = dificultad
        self.ramo = random.randint(1, 10)
        self.resultado_introducido = ""

        self.respuestas_introducidas = []
        self.intentos_totales = 0
        self.num_borrados = 0
        self.num_digitos_introducidos = 0

        self.tiempo_inicio = time.time()
        self.tiempo_fin = None
        self.completada = False

        self.show_metrics_popup = False

        if self.dificultad == "facil":
            self.resultado_correcto = self.ramo + NUM_BANCOS + NUM_VIDRIERAS

        elif self.dificultad == "medio":
            self.resultado_correcto = self.ramo + NUM_VIDRIERAS

        elif self.dificultad == "dificil":
            self.resultado_correcto = self.ramo * 2 + NUM_VIDRIERAS

        self.state = STATE_PRUEBA


    def get_nombre_dificultad(self):
        if self.dificultad == "facil":
            return "Fácil"

        if self.dificultad == "medio":
            return "Medio"

        return "Difícil"

    def read_keypad_key(self):
        if not self.keypad_available:
            return None

        key_map = {
            (0, 0): "1",
            (0, 1): "2",
            (0, 2): "3",
            (1, 0): "4",
            (1, 1): "5",
            (1, 2): "6",
            (2, 0): "7",
            (2, 1): "8",
            (2, 2): "9",
            (3, 0): "*",
            (3, 1): "0",
            (3, 2): "#",
        }

        pressed_key = None

        for row_index in range(4):
            # Comentario semántico: dejamos una fila a nivel bajo para detectar qué columna se conecta al pulsar.
            value = 0b00001111
            value &= ~(1 << row_index)
            self.bus.write_byte_data(MCP23017_ADDRESS, self.GPIOA, value)

            time.sleep(0.01)

            gpio_value = self.bus.read_byte_data(MCP23017_ADDRESS, self.GPIOA)

            for col_index in range(3):
                bit = 4 + col_index
                is_low = not bool(gpio_value & (1 << bit))

                if is_low:
                    pressed_key = key_map.get((row_index, col_index))

        now = pygame.time.get_ticks()

        if pressed_key is None:
            self.key_is_down = False
            self.last_pressed_key = None
            return None

        if self.key_is_down and pressed_key == self.last_pressed_key:
            return None

        if now - self.last_key_time < 180:
            return None

        self.key_is_down = True
        self.last_pressed_key = pressed_key
        self.last_key_time = now

        return pressed_key

    def process_keypad(self):
        if self.state != STATE_PRUEBA:
            return

        key = self.read_keypad_key()

        if key is None:
            return

        if key in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            if len(self.resultado_introducido) < 4:
                self.resultado_introducido += key
                self.num_digitos_introducidos += 1

        elif key == "*":
            # Comentario semántico: la tecla de borrar elimina solo el último dígito introducido.
            if self.resultado_introducido:
                self.resultado_introducido = self.resultado_introducido[:-1]
                self.num_borrados += 1

        elif key == "#":
            self.validar_resultado()

    def validar_resultado(self):
        if self.resultado_introducido == "":
            return

        self.intentos_totales += 1
        self.respuestas_introducidas.append(self.resultado_introducido)

        if self.resultado_introducido == str(self.resultado_correcto):
            self.feedback_correcto = True
            self.feedback_message = "Habéis resuelto correctamente la operación de la iglesia."
            self.completada = True
            self.tiempo_fin = time.time()
            self.reproducir_audio(self.audio_correcto_path)
            self.state = STATE_FEEDBACK

        else:
            self.feedback_correcto = False
            self.feedback_message = "Revisad los bancos, las vidrieras y el valor del ramo."
            self.reproducir_audio(self.audio_error_path)
            self.state = STATE_FEEDBACK

    def obtener_tiempo_total(self):
        if self.tiempo_inicio is None:
            return 0

        if self.tiempo_fin is not None:
            return round(self.tiempo_fin - self.tiempo_inicio, 2)

        return round(time.time() - self.tiempo_inicio, 2)


    def obtener_metricas(self):
        return {
            "dificultad": self.get_nombre_dificultad(),
            "valor_ramo": self.ramo,
            "num_bancos": NUM_BANCOS,
            "num_vidrieras": NUM_VIDRIERAS,
            "resultado_correcto": self.resultado_correcto,
            "respuestas_introducidas": " | ".join(self.respuestas_introducidas),
            "intentos_totales": self.intentos_totales,
            "num_borrados": self.num_borrados,
            "num_digitos_introducidos": self.num_digitos_introducidos,
            "tiempo_total_segundos": self.obtener_tiempo_total(),
            "completada": self.completada,
        }

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


    def draw_expression_image(self, image, center):
        if image is not None:
            image_rect = image.get_rect(center=center)
            self.screen.blit(image, image_rect)

    def draw_expression_symbol(self, symbol, center):
        self.draw_text(symbol, self.result_font, TEXT, center)


    def draw_first_expression(self, y):
        if self.dificultad == "facil":
            elements = [
                ("image", self.ramo_img),
                ("symbol", "+"),
                ("image", self.ramo_img),
                ("symbol", "="),
                ("symbol", str(self.ramo * 2)),
            ]
        else:
            elements = [
                ("image", self.banco_img),
                ("symbol", "+"),
                ("image", self.ramo_img),
                ("symbol", "="),
                ("symbol", str(NUM_BANCOS + self.ramo)),
            ]

        self.draw_expression(elements, y)


    def draw_final_expression(self, y):
        if self.dificultad == "facil":
            elements = [
                ("image", self.ramo_img),
                ("symbol", "+"),
                ("image", self.banco_img),
                ("symbol", "+"),
                ("image", self.vidriera_img),
                ("symbol", "="),
                ("symbol", "?"),
            ]

        elif self.dificultad == "medio":
            elements = [
                ("image", self.ramo_img),
                ("symbol", "+"),
                ("image", self.vidriera_img),
                ("symbol", "="),
                ("symbol", "?"),
            ]

        else:
            elements = [
                ("image", self.ramo_img),
                ("symbol", "×"),
                ("symbol", "2"),
                ("symbol", "+"),
                ("image", self.vidriera_img),
                ("symbol", "="),
                ("symbol", "?"),
            ]

        self.draw_expression(elements, y)


    def draw_expression(self, elements, y):
        spacing = 88
        total_width = (len(elements) - 1) * spacing
        start_x = (SCREEN_WIDTH // 2) - (total_width // 2)

        for i, element in enumerate(elements):
            x = start_x + i * spacing
            kind = element[0]
            value = element[1]

            if kind == "image":
                self.draw_expression_image(value, (x, y))
            else:
                self.draw_expression_symbol(value, (x, y))

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
        self.process_keypad()

        if self.state == STATE_INTRO:
            self.draw_intro()
        elif self.state == STATE_DIFICULTAD:
            self.draw_dificultad()
        elif self.state == STATE_PRUEBA:
            self.draw_prueba()
        elif self.state == STATE_FEEDBACK:
            self.draw_feedback()
        elif self.state == STATE_FINAL:
            self.draw_final()

    def draw_intro(self):
        self.draw_background()

        panel_rect = pygame.Rect(92, 92, 840, 385)
        self.draw_panel(panel_rect)

        self.draw_text(
            "Prueba 4",
            self.button_font,
            SECONDARY_TEXT,
            (SCREEN_WIDTH // 2, 135)
        )

        self.draw_text(
            "Un total de...",
            self.title_font,
            TEXT,
            (SCREEN_WIDTH // 2, 190)
        )

        y = 252

        y = self.draw_wrapped_text_centered(
            "Resolved la operación usando la iglesia",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        y = self.draw_wrapped_text_centered(
            "y el teclado telefónico.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        y += 20

        self.draw_wrapped_text_centered(
            "Tendréis que contar bancos, vidrieras y averiguar el valor del ramo.",
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

    def draw_dificultad(self):
        self.draw_background()

        self.draw_text_with_shadow(
            "Selecciona la dificultad",
            self.title_font,
            TITLE,
            (SCREEN_WIDTH // 2, 125)
        )

        self.draw_button(self.easy_rect, "Fácil")
        self.draw_button(self.medium_rect, "Medio")
        self.draw_button(self.hard_rect, "Difícil")

        self.draw_back_button()

    def draw_prueba(self):
        self.draw_background()

        self.draw_text_with_shadow(
            f"Nivel {self.get_nombre_dificultad()}",
            self.title_font,
            TITLE,
            (SCREEN_WIDTH // 2, 82)
        )

        first_panel = pygame.Rect(85, 122, 854, 145)
        self.draw_card(first_panel)

        self.draw_text(
            "Averiguad el valor del ramo",
            self.small_font,
            SECONDARY_TEXT,
            (SCREEN_WIDTH // 2, 150)
        )

        self.draw_first_expression(218)

        final_panel = pygame.Rect(85, 282, 854, 145)
        self.draw_card(final_panel)

        self.draw_text(
            "Calculad el resultado final",
            self.small_font,
            SECONDARY_TEXT,
            (SCREEN_WIDTH // 2, 310)
        )

        self.draw_final_expression(378)

        input_panel = pygame.Rect(200, 452, 624, 60)
        self.draw_card(input_panel)

        resultado = self.resultado_introducido if self.resultado_introducido else "__"

        self.draw_text(
            f"Resultado: {resultado}",
            self.small_font,
            TEXT,
            (SCREEN_WIDTH // 2, 482)
        )

        self.draw_text(
            "# Confirmar      * Borrar",
            self.small_font,
            TITLE,
            (SCREEN_WIDTH // 2, 542)
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
            self.draw_button(self.continue_rect, "Intentar de nuevo")

    def draw_metrics_popup(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 145))
        self.screen.blit(overlay, (0, 0))

        popup_rect = pygame.Rect(160, 85, 704, 430)
        self.draw_panel(popup_rect)

        self.draw_text(
            "Métricas de la prueba",
            self.button_font,
            TEXT,
            (SCREEN_WIDTH // 2, 128)
        )

        # Guardamos el rectángulo en self para que la zona de click coincida
        # exactamente con la posición visual de la X.
        self.metrics_close_rect = pygame.Rect(popup_rect.right - 68, popup_rect.y + 18, 50, 50)

        pygame.draw.rect(self.screen, RED, self.metrics_close_rect, border_radius=12)
        pygame.draw.rect(self.screen, BORDER, self.metrics_close_rect, width=3, border_radius=12)
        self.draw_text("X", self.button_font, TITLE, self.metrics_close_rect.center)

        metricas = self.obtener_metricas()

        lineas = [
            f"Dificultad: {metricas['dificultad']}",
            f"Valor del ramo: {metricas['valor_ramo']}",
            f"Bancos: {metricas['num_bancos']}    Vidrieras: {metricas['num_vidrieras']}",
            f"Resultado correcto: {metricas['resultado_correcto']}",
            f"Respuestas introducidas: {metricas['respuestas_introducidas']}",
            f"Intentos totales: {metricas['intentos_totales']}",
            f"Borrados realizados: {metricas['num_borrados']}",
            f"Dígitos introducidos: {metricas['num_digitos_introducidos']}",
            f"Tiempo total: {metricas['tiempo_total_segundos']} s",
        ]

        x = popup_rect.x + 70
        y = 168

        for linea in lineas:
            surface = self.small_font.render(linea, True, TEXT)
            self.screen.blit(surface, (x, y))
            y += 34


    def draw_final(self):
        self.draw_background()

        panel_rect = pygame.Rect(100, 90, 824, 365)
        self.draw_panel(panel_rect)

        self.draw_text(
            "Prueba superada",
            self.title_font,
            GREEN,
            (SCREEN_WIDTH // 2, 145)
        )

        self.draw_wrapped_text_centered(
            "Habéis completado el cálculo",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            220,
            760
        )

        self.draw_wrapped_text_centered(
            "de la iglesia.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            270,
            760
        )

        self.draw_wrapped_text_centered(
            "Habéis conseguido una nueva pista.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            340,
            760
        )

        self.draw_wrapped_text_centered(
            f"Dígito obtenido: {DIGITO_OBTENIDO}",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            405,
            760
        )

        if not self.audio_final_reproducido:
            self.reproducir_audio(self.audio_final_path)
            self.audio_final_reproducido = True

        self.draw_button(self.metrics_rect, "Métricas")
        self.draw_button(self.menu_rect, "Volver al menú")

        if self.show_metrics_popup:
            self.draw_metrics_popup()

    def handle_click(self, mouse_pos):
        if self.state == STATE_INTRO:
            if self.back_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                return "menu"

            if self.continue_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                self.state = STATE_DIFICULTAD

        elif self.state == STATE_DIFICULTAD:
            if self.back_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                self.state = STATE_INTRO

            elif self.easy_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                self.configurar_prueba("facil")

            elif self.medium_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                self.configurar_prueba("medio")

            elif self.hard_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                self.configurar_prueba("dificil")

        elif self.state == STATE_FEEDBACK:
            if self.continue_rect.collidepoint(mouse_pos):
                if self.feedback_correcto:
                    self.state = STATE_FINAL
                else:
                    pygame.mixer.music.stop()
                    self.resultado_introducido = ""
                    self.state = STATE_PRUEBA

        elif self.state == STATE_FINAL:
            if self.show_metrics_popup:
                if self.metrics_close_rect.collidepoint(mouse_pos):
                    self.show_metrics_popup = False
                return None

            if self.metrics_rect.collidepoint(mouse_pos):
                self.show_metrics_popup = True

            elif self.menu_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                return "menu"

        return None