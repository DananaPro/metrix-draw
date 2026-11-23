
import pygame
import serial
import time
import math
import random
import sys

# ============================================================
# MATRIX STUDIO
# Python GUI + Arduino Serial + 32x24 HT1632C Display
# ============================================================

WIDTH, HEIGHT = 1100, 760
FPS = 60

MATRIX_W = 32
MATRIX_H = 24

SERIAL_PORT = "COM3"
BAUD_RATE = 115200

SEND_FPS = 15

# ---------------- COLORS ----------------

BG = (10, 12, 22)
PANEL = (19, 23, 39)
PANEL_LIGHT = (28, 34, 55)
ACCENT = (170, 100, 255)
CYAN = (75, 210, 255)
PINK = (255, 80, 155)
WHITE = (235, 238, 250)
MUTED = (130, 140, 165)
GREEN = (80, 220, 150)
RED = (255, 90, 100)

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MATRIX STUDIO")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("consolas", 17)
SMALL = pygame.font.SysFont("consolas", 13)
MEDIUM = pygame.font.SysFont("consolas", 22, bold=True)
BIG = pygame.font.SysFont("consolas", 34, bold=True)

# ---------------- SERIAL ----------------

arduino = None
connected = False

try:
    arduino = serial.Serial(
        SERIAL_PORT,
        BAUD_RATE,
        timeout=0.1
    )
    time.sleep(2)
    connected = True
    print("Arduino connected")

except serial.SerialException as error:
    print("Arduino not connected:", error)


# ---------------- APP STATE ----------------

page = "home"
selected_animation = "starfield"

running = True
animation_time = 0
last_send = 0

draw_frame = [
    [0 for _ in range(MATRIX_W)]
    for _ in range(MATRIX_H)
]

drawing = False
draw_value = 1

stars = [
    {
        "x": random.uniform(0, MATRIX_W - 1),
        "y": random.uniform(0, MATRIX_H - 1),
        "speed": random.uniform(2, 8)
    }
    for _ in range(35)
]

shooting_stars = []


# ============================================================
# HELPERS
# ============================================================

def text(surface, value, x, y, font=FONT, color=WHITE):
    image = font.render(str(value), True, color)
    surface.blit(image, (x, y))


def button(rect, label, mouse, active=False):
    hovered = rect.collidepoint(mouse)

    color = PANEL_LIGHT if hovered else PANEL

    if active:
        color = (65, 45, 100)

    pygame.draw.rect(
        screen, color, rect, border_radius=10
    )

    pygame.draw.rect(
        screen,
        ACCENT if active or hovered else (45, 52, 75),
        rect,
        1,
        border_radius=10
    )

    label_image = MEDIUM.render(label, True, WHITE)

    screen.blit(
        label_image,
        label_image.get_rect(center=rect.center)
    )

    return hovered


def empty_frame():
    return [
        [0 for _ in range(MATRIX_W)]
        for _ in range(MATRIX_H)
    ]


# ============================================================
# SERIAL FRAME TRANSMISSION
# ============================================================

def send_matrix(frame):

    global connected

    if not connected or arduino is None:
        return

    data = bytearray()

    for row in frame:

        for byte_index in range(4):

            value = 0

            for bit in range(8):

                x = byte_index * 8 + bit

                if row[x]:
                    value |= 1 << (7 - bit)

            data.append(value)

    packet = bytes([0xAA, 0x55]) + data

    try:
        arduino.write(packet)

    except serial.SerialException:
        connected = False


# ============================================================
# ANIMATION 1: STARFIELD
# ============================================================

def starfield(dt):

    frame = empty_frame()

    for star in stars:

        star["y"] += star["speed"] * dt

        if star["y"] >= MATRIX_H:
            star["y"] = 0
            star["x"] = random.uniform(0, MATRIX_W - 1)

        x = int(star["x"])
        y = int(star["y"])

        if 0 <= x < MATRIX_W and 0 <= y < MATRIX_H:
            frame[y][x] = 1

    # Occasionally create shooting stars
    if random.random() < 0.025:
        shooting_stars.append({
            "x": random.randint(0, MATRIX_W - 1),
            "y": random.randint(0, 8),
            "life": 4
        })

    for star in shooting_stars[:]:

        x = int(star["x"])
        y = int(star["y"])

        for offset in range(4):

            px = x - offset
            py = y - offset

            if 0 <= px < MATRIX_W and 0 <= py < MATRIX_H:
                frame[py][px] = 1

        star["x"] += 1
        star["y"] += 1
        star["life"] -= 1

        if star["life"] <= 0:
            shooting_stars.remove(star)

    return frame


# ============================================================
# ANIMATION 2: PULSING HEART
# ============================================================

def heart_animation(t):

    frame = empty_frame()

    pulse = 1 + 0.08 * math.sin(t * 3)

    for y in range(MATRIX_H):

        for x in range(MATRIX_W):

            hx = (x - 15.5) / (11 * pulse)
            hy = -(y - 13.5) / (10 * pulse)

            equation = (
                (hx**2 + hy**2 - 1)**3
                - hx**2 * hy**3
            )

            if equation <= 0:
                frame[y][x] = 1

    return frame


# ============================================================
# ANIMATION 3: BOUNCING BALL
# ============================================================

def bouncing_ball(t):

    frame = empty_frame()

    x = int(15.5 + 13 * math.sin(t * 2))
    y = int(11.5 + 9 * math.sin(t * 3))

    x = max(0, min(31, x))
    y = max(0, min(23, y))

    frame[y][x] = 1

    return frame


# ============================================================
# DRAW MATRIX PREVIEW
# ============================================================

def draw_matrix_preview(frame, rect, editable=False):

    cell_w = rect.width / MATRIX_W
    cell_h = rect.height / MATRIX_H

    pygame.draw.rect(
        screen,
        (8, 10, 18),
        rect,
        border_radius=5
    )

    for y in range(MATRIX_H):

        for x in range(MATRIX_W):

            cell = pygame.Rect(
                rect.x + x * cell_w,
                rect.y + y * cell_h,
                max(1, cell_w - 2),
                max(1, cell_h - 2)
            )

            color = (
                PINK if frame[y][x]
                else (35, 42, 58)
            )

            pygame.draw.rect(
                screen,
                color,
                cell,
                border_radius=2
            )


# ============================================================
# SIDEBAR
# ============================================================

def draw_sidebar(mouse):

    pygame.draw.rect(
        screen,
        PANEL,
        (0, 0, 220, HEIGHT)
    )

    text(screen, "MATRIX", 25, 28, BIG, ACCENT)
    text(screen, "STUDIO", 25, 66, BIG, WHITE)

    pygame.draw.line(
        screen,
        (55, 62, 85),
        (20, 120),
        (200, 120)
    )

    navigation = [
        ("HOME", "home"),
        ("ANIMATIONS", "animations"),
        ("CREATE", "create"),
        ("READ ME", "readme")
    ]

    for i, (label, destination) in enumerate(navigation):

        rect = pygame.Rect(
            15,
            145 + i * 65,
            190,
            48
        )

        if button(
            rect,
            label,
            mouse,
            page == destination
        ):
            pass

    pygame.draw.line(
        screen,
        (55, 62, 85),
        (20, HEIGHT - 95),
        (200, HEIGHT - 95)
    )

    status_color = GREEN if connected else RED

    pygame.draw.circle(
        screen,
        status_color,
        (35, HEIGHT - 60),
        6
    )

    text(
        screen,
        "ARDUINO ONLINE" if connected else "ARDUINO OFFLINE",
        50,
        HEIGHT - 68,
        SMALL,
        status_color
    )


# ============================================================
# HOME PAGE
# ============================================================

def home_page(mouse):

    text(screen, "WELCOME TO MATRIX STUDIO", 260, 45, BIG)

    text(
        screen,
        "Your personal LED matrix control center.",
        260,
        95,
        FONT,
        MUTED
    )

    cards = [
        ("ANIMATIONS", "Choose what your display shows", "animations"),
        ("CREATE", "Design your own pixel art", "create"),
        ("READ ME", "Understand how the system works", "readme")
    ]

    for i, (title, description, destination) in enumerate(cards):

        rect = pygame.Rect(
            260,
            165 + i * 145,
            770,
            115
        )

        pygame.draw.rect(
            screen,
            PANEL,
            rect,
            border_radius=14
        )

        pygame.draw.rect(
            screen,
            (55, 62, 85),
            rect,
            1,
            border_radius=14
        )

        text(
            screen,
            title,
            285,
            rect.y + 20,
            MEDIUM,
            ACCENT
        )

        text(
            screen,
            description,
            285,
            rect.y + 57,
            SMALL,
            MUTED
        )

        button_rect = pygame.Rect(
            850,
            rect.y + 35,
            150,
            45
        )

        button(button_rect, "OPEN", mouse)

    # Display information

    text(screen, "DISPLAY INFORMATION", 260, 630, MEDIUM)

    text(
        screen,
        "32 x 24 pixels     |     768 LEDs     |     3 controllers",
        260,
        670,
        SMALL,
        MUTED
    )


# ============================================================
# ANIMATIONS PAGE
# ============================================================

def animations_page(mouse):

    text(screen, "ANIMATION LIBRARY", 260, 45, BIG)

    text(
        screen,
        "Select an animation for your LED display.",
        260,
        95,
        FONT,
        MUTED
    )

    options = [
        ("STARFIELD", "starfield"),
        ("PULSING HEART", "heart"),
        ("BOUNCING BALL", "ball")
    ]

    for i, (label, animation) in enumerate(options):

        rect = pygame.Rect(
            260 + (i % 2) * 380,
            155 + (i // 2) * 190,
            350,
            145
        )

        button(
            rect,
            label,
            mouse,
            selected_animation == animation
        )


# ============================================================
# CREATE PAGE
# ============================================================

def create_page(mouse):

    global drawing, draw_value

    text(screen, "PIXEL ART CREATOR", 260, 35, BIG)

    text(
        screen,
        "Click or drag to draw. Right-click to erase.",
        260,
        85,
        FONT,
        MUTED
    )

    grid_rect = pygame.Rect(
        270,
        145,
        640,
        480
    )

    cell_w = grid_rect.width / MATRIX_W
    cell_h = grid_rect.height / MATRIX_H

    draw_matrix_preview(
        draw_frame,
        grid_rect,
        True
    )

    if pygame.mouse.get_pressed()[0] or pygame.mouse.get_pressed()[2]:

        if grid_rect.collidepoint(mouse):

            x = int((mouse[0] - grid_rect.x) / cell_w)
            y = int((mouse[1] - grid_rect.y) / cell_h)

            if 0 <= x < MATRIX_W and 0 <= y < MATRIX_H:

                draw_value = (
                    0 if pygame.mouse.get_pressed()[2]
                    else 1
                )

                draw_frame[y][x] = draw_value

    clear_rect = pygame.Rect(270, 660, 150, 45)
    send_rect = pygame.Rect(440, 660, 200, 45)

    button(clear_rect, "CLEAR", mouse)
    button(send_rect, "SEND TO LEDS", mouse)


# ============================================================
# README PAGE
# ============================================================

def readme_page():

    text(screen, "HOW MATRIX STUDIO WORKS", 260, 40, BIG)

    sections = [
        ("01 - PYTHON",
         "Python creates the image and manages the GUI."),

        ("02 - PIXEL DATA",
         "The image is stored as a 32 x 24 array."),

        ("03 - SERIAL COMMUNICATION",
         "Python sends 96 bytes through USB to the Arduino."),

        ("04 - ARDUINO",
         "The Arduino receives the data and identifies each pixel."),

        ("05 - HT1632C CONTROLLERS",
         "Three controllers receive their respective 8 x 32 buffers."),

        ("06 - LED DISPLAY",
         "The controllers operate the LEDs on your three panels.")
    ]

    for i, (heading, description) in enumerate(sections):

        y = 115 + i * 85

        text(
            screen,
            heading,
            270,
            y,
            MEDIUM,
            ACCENT
        )

        text(
            screen,
            description,
            270,
            y + 35,
            SMALL,
            MUTED
        )

    text(
        screen,
        "PROTOCOL: AA 55 + 96 BYTES",
        270,
        650,
        FONT,
        CYAN
    )


# ============================================================
# MAIN LOOP
# ============================================================

while running:

    dt = clock.tick(FPS) / 1000
    animation_time += dt

    mouse = pygame.mouse.get_pos()

    screen.fill(BG)

    draw_sidebar(mouse)

    # ---------------- EVENTS ----------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                page = "home"

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                # Sidebar navigation
                if mouse[0] < 220:

                    index = (mouse[1] - 145) // 65

                    destinations = [
                        "home",
                        "animations",
                        "create",
                        "readme"
                    ]

                    if 0 <= index < len(destinations):
                        page = destinations[index]

                elif page == "home":

                    if 165 <= mouse[1] < 280:
                        page = "animations"

                    elif 310 <= mouse[1] < 425:
                        page = "create"

                    elif 455 <= mouse[1] < 570:
                        page = "readme"

                elif page == "animations":

                    if 155 <= mouse[1] < 300:

                        if 260 <= mouse[0] < 610:
                            selected_animation = "starfield"

                        elif 640 <= mouse[0] < 990:
                            selected_animation = "heart"

                    elif 345 <= mouse[1] < 490:
                        selected_animation = "ball"

                elif page == "create":

                    if pygame.Rect(270, 660, 150, 45).collidepoint(mouse):

                        draw_frame = empty_frame()

                    elif pygame.Rect(440, 660, 200, 45).collidepoint(mouse):

                        send_matrix(draw_frame)

    # ---------------- PAGES ----------------

    if page == "home":
        home_page(mouse)

    elif page == "animations":
        animations_page(mouse)

    elif page == "create":
        create_page(mouse)

    elif page == "readme":
        readme_page()

    # ---------------- LIVE ANIMATION ----------------

    if page == "animations":

        if selected_animation == "starfield":
            frame = starfield(dt)

        elif selected_animation == "heart":
            frame = heart_animation(animation_time)

        else:
            frame = bouncing_ball(animation_time)

        preview_rect = pygame.Rect(
            760,
            530,
            240,
            180
        )

        draw_matrix_preview(frame, preview_rect)

        text(
            screen,
            "LIVE PREVIEW",
            760,
            500,
            SMALL,
            CYAN
        )

        if time.time() - last_send >= 1 / SEND_FPS:

            send_matrix(frame)
            last_send = time.time()

    pygame.display.flip()


# ============================================================
# SHUTDOWN
# ============================================================

if arduino is not None:

    try:
        arduino.close()
    except serial.SerialException:
        pass

pygame.quit()
sys.exit()
