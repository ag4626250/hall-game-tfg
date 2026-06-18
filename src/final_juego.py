import time
import wave
from pathlib import Path

import pygame


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600

STATE_INTRO = "intro"
STATE_CODIGO = "codigo"
STATE_ERROR = "error"
STATE_CORRECTO = "correcto"
STATE_FINAL = "final"

CODIGO_FINAL = "32779"

MCP23017_ADDRESS = 0x27

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


class FinalJuego:
    def __init__(self, screen):
        self.screen = screen

        self.title_font = pygame.font.SysFont("Arial", 50, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 42)
        self.button_font = pygame.font.SysFont("Arial", 34, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 32)
        self.code_font = pygame.font.SysFont("Arial", 58, bold=True)

        self.continue_rect = pygame.Rect(292, 485, 440, 66)
        self.menu_rect = pygame.Rect(292, 485, 440, 66)
        self.back_rect = pygame.Rect(55, 485, 80, 60)

        self.base_dir = Path(__file__).resolve().parent.parent
        self.audio_dir = self.base_dir / "assets" / "audios"
        self.silence_path = self.audio_dir / "silencio.wav"

        self.audio_inicio_path = self.audio_dir / "final_inicio.mp3"
        self.audio_correcto_path = self.audio_dir / "final_correcto.mp3"
        self.audio_error_path = self.audio_dir / "final_error.mp3"
        self.audio_cancion_path = self.audio_dir / "final_cancion.ogg"

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

            # Comentario semántico: PA0-PA3 son filas y PA4-PA6 son columnas del teclado telefónico.
            self.bus.write_byte_data(MCP23017_ADDRESS, self.IODIRA, 0b11110000)

            # Comentario semántico: las columnas usan pull-up para detectar cada tecla como nivel bajo.
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
        self.codigo_introducido = ""

        self.intentos = 0
        self.errores = 0
        self.codigos_introducidos = []
        self.tiempo_inicio = None
        self.tiempo_fin = None
        self.completado = False

        self.audio_inicio_reproducido = False
        self.audio_correcto_reproducido = False
        self.audio_error_reproducido = False
        self.audio_cancion_reproducido = False

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
            # Comentario semántico: activamos una fila cada vez para saber qué tecla se ha pulsado.
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
        if self.state != STATE_CODIGO:
            return

        key = self.read_keypad_key()

        if key is None:
            return

        self.process_key(key)

    def process_key(self, key):
        if self.state != STATE_CODIGO:
            return

        if key in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            if len(self.codigo_introducido) < len(CODIGO_FINAL):
                self.codigo_introducido += key

        elif key == "*":
            if self.codigo_introducido:
                self.codigo_introducido = self.codigo_introducido[:-1]

        elif key == "#":
            self.validar_codigo()

    def validar_codigo(self):
        if self.codigo_introducido == "":
            return

        self.intentos += 1
        self.codigos_introducidos.append(self.codigo_introducido)

        if self.codigo_introducido == CODIGO_FINAL:
            self.completado = True
            self.tiempo_fin = time.time()
            self.state = STATE_CORRECTO
        else:
            self.errores += 1
            self.state = STATE_ERROR

    def handle_keydown(self, key):
        # Comentario semántico: permite probar la interfaz con teclado del ordenador si el MCP23017 no está conectado.
        if self.state != STATE_CODIGO:
            return

        if pygame.K_0 <= key <= pygame.K_9:
            self.process_key(str(key - pygame.K_0))

        elif key == pygame.K_BACKSPACE:
            self.process_key("*")

        elif key == pygame.K_RETURN:
            self.process_key("#")

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

    def draw(self):
        self.process_keypad()

        if self.state == STATE_INTRO:
            self.draw_intro()
        elif self.state == STATE_CODIGO:
            self.draw_codigo()
        elif self.state == STATE_ERROR:
            self.draw_error()
        elif self.state == STATE_CORRECTO:
            self.draw_correcto()
        elif self.state == STATE_FINAL:
            self.draw_final()

    def draw_intro(self):
        self.draw_background()

        panel_rect = pygame.Rect(92, 82, 840, 395)
        self.draw_panel(panel_rect)

        self.draw_text(
            "Final del juego",
            self.button_font,
            SECONDARY_TEXT,
            (SCREEN_WIDTH // 2, 125)
        )

        self.draw_text(
            "Código final de la boda",
            self.title_font,
            TEXT,
            (SCREEN_WIDTH // 2, 185)
        )

        y = 250

        y = self.draw_wrapped_text_centered(
            "Habéis reunido todos los dígitos.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        y += 8

        y = self.draw_wrapped_text_centered(
            "Introducid el código en el teléfono",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        y = self.draw_wrapped_text_centered(
            "de la iglesia.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        y += 12

        self.draw_wrapped_text_centered(
            "# Confirmar        * Borrar",
            self.small_font,
            SECONDARY_TEXT,
            SCREEN_WIDTH // 2,
            y,
            780
        )

        if not self.audio_inicio_reproducido:
            self.reproducir_audio(self.audio_inicio_path)
            self.audio_inicio_reproducido = True

        self.draw_button(self.continue_rect, "Introducir código")
        self.draw_back_button()

    def draw_codigo(self):
        self.draw_background()

        self.draw_text_with_shadow(
            "Introducid el código final",
            self.title_font,
            TITLE,
            (SCREEN_WIDTH // 2, 90)
        )

        panel_rect = pygame.Rect(120, 145, 784, 280)
        self.draw_panel(panel_rect)

        self.draw_text(
            "Código introducido:",
            self.text_font,
            SECONDARY_TEXT,
            (SCREEN_WIDTH // 2, 210)
        )

        codigo_visible = self.codigo_introducido if self.codigo_introducido else "-----"

        code_rect = pygame.Rect(270, 260, 484, 90)
        self.draw_card(code_rect)

        self.draw_text(
            codigo_visible,
            self.code_font,
            TEXT,
            code_rect.center
        )

        self.draw_text(
            "# Confirmar        * Borrar",
            self.small_font,
            TITLE,
            (SCREEN_WIDTH // 2, 470)
        )

        self.draw_text(
            "Usad el teclado telefónico de la iglesia.",
            self.small_font,
            TITLE,
            (SCREEN_WIDTH // 2, 525)
        )

    def draw_error(self):
        self.draw_background()

        panel_rect = pygame.Rect(112, 115, 800, 315)
        self.draw_panel(panel_rect)

        self.draw_text(
            "Código incorrecto",
            self.title_font,
            RED,
            (SCREEN_WIDTH // 2, 170)
        )

        self.draw_wrapped_text_centered(
            "El teléfono no ha dado la señal correcta.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            245,
            730
        )

        self.draw_wrapped_text_centered(
            "Revisad los dígitos e intentadlo de nuevo.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            320,
            730
        )

        if not self.audio_error_reproducido:
            self.reproducir_audio(self.audio_error_path)
            self.audio_error_reproducido = True

        self.draw_button(self.continue_rect, "Intentar de nuevo")

    def draw_correcto(self):
        self.draw_background()

        panel_rect = pygame.Rect(100, 105, 824, 330)
        self.draw_panel(panel_rect)

        self.draw_text(
            "¡Llamada completada!",
            self.title_font,
            GREEN,
            (SCREEN_WIDTH // 2, 165)
        )

        self.draw_wrapped_text_centered(
            "El teléfono de la iglesia ha respondido.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            235,
            760
        )

        self.draw_wrapped_text_centered(
            "Buscad en el confesionario.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            300,
            760
        )

        self.draw_wrapped_text_centered(
            "Allí encontraréis la última pista.",
            self.text_font,
            SECONDARY_TEXT,
            SCREEN_WIDTH // 2,
            360,
            760
        )

        if not self.audio_correcto_reproducido:
            self.reproducir_audio(self.audio_correcto_path)
            self.audio_correcto_reproducido = True

        self.draw_button(self.continue_rect, "Finalizar")

    def draw_final(self):
        self.draw_background()

        panel_rect = pygame.Rect(110, 115, 804, 330)
        self.draw_panel(panel_rect)

        self.draw_text(
            "¡Misterio resuelto!",
            self.title_font,
            GREEN,
            (SCREEN_WIDTH // 2, 175)
        )

        y = 230

        y = self.draw_wrapped_text_centered(
            "Habéis recuperado el anillo a tiempo.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            760
        )

        y += 6

        y = self.draw_wrapped_text_centered(
            "Pablo y María ya pueden celebrar su boda.",
            self.text_font,
            TEXT,
            SCREEN_WIDTH // 2,
            y,
            760
        )

        y += 6

        self.draw_wrapped_text_centered(
            "Gracias por vuestra ayuda, detectives.",
            self.text_font,
            SECONDARY_TEXT,
            SCREEN_WIDTH // 2,
            y,
            760
        )

        if not self.audio_cancion_reproducido:
            self.reproducir_audio(self.audio_cancion_path)
            self.audio_cancion_reproducido = True

        self.draw_button(self.menu_rect, "Volver al menú")

    def handle_click(self, mouse_pos):
        if self.state == STATE_INTRO:
            if self.back_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                return "menu"

            if self.continue_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                self.codigo_introducido = ""
                self.tiempo_inicio = time.time()
                self.state = STATE_CODIGO

        elif self.state == STATE_ERROR:
            if self.continue_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                self.codigo_introducido = ""
                self.audio_error_reproducido = False
                self.state = STATE_CODIGO

        elif self.state == STATE_CORRECTO:
            if self.continue_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                self.state = STATE_FINAL

        elif self.state == STATE_FINAL:
            if self.menu_rect.collidepoint(mouse_pos):
                pygame.mixer.music.stop()
                return "menu"

        return None