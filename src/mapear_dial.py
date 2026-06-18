from time import sleep

try:
    import smbus
except ImportError:
    print("Falta instalar smbus. Ejecuta: sudo apt install -y python3-smbus")
    raise SystemExit


ADDRESS = 0x27

IODIRA = 0x00
GPPUA = 0x0C
GPIOA = 0x12

ROWS = ["R1", "R2", "R3", "R4"]
COLS = ["C1", "C2", "C3", "C4"]

bus = smbus.SMBus(1)

# PA0-PA3 como salidas para filas, PA4-PA7 como entradas para columnas.
bus.write_byte_data(ADDRESS, IODIRA, 0b11110000)

# Activamos pull-up interno en las columnas PA4-PA7.
bus.write_byte_data(ADDRESS, GPPUA, 0b11110000)


def set_active_row(row_index):
    # Comentario semántico: dejamos una fila a nivel bajo para detectar qué columna se conecta al pulsar.
    value = 0b00001111
    value &= ~(1 << row_index)
    bus.write_byte_data(ADDRESS, GPIOA, value)


def read_columns():
    value = bus.read_byte_data(ADDRESS, GPIOA)

    pressed_cols = []
    for col_index in range(4):
        bit = 4 + col_index
        is_low = not bool(value & (1 << bit))

        if is_low:
            pressed_cols.append(col_index)

    return pressed_cols


print("Mapeo del teclado telefónico")
print("Pulsa una tecla cada vez. Pulsa Ctrl+C para salir.")
print()

last_detection = None

try:
    while True:
        detection = None

        for row_index in range(4):
            set_active_row(row_index)
            sleep(0.01)

            pressed_cols = read_columns()

            if pressed_cols:
                col_index = pressed_cols[0]
                detection = (ROWS[row_index], COLS[col_index])

        if detection and detection != last_detection:
            print(f"Tecla detectada: {detection[0]} + {detection[1]}")
            last_detection = detection

        if detection is None:
            last_detection = None

        sleep(0.05)

except KeyboardInterrupt:
    print("\nPrueba finalizada.")
