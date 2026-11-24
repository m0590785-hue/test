import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Constants
TILE_SIZE = 30
ROWS, COLS = 15, 19
WIDTH, HEIGHT = COLS * TILE_SIZE, ROWS * TILE_SIZE + 40
FPS = 10

# Colors
BLACK = (0, 0, 0)
BLUE = (33, 33, 222)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
PINK = (255, 184, 255)
CYAN = (0, 255, 255)

# Maze Layout (1 = Wall, 0 = Pellet, 2 = Empty)
LAYOUT = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,0,1,1,1,0,1,0,1,1,1,0,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,0,1,0,1,1,1,1,1,0,1,0,1,1,0,1],
    [1,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,1],
    [1,1,1,1,0,1,1,1,2,1,2,1,1,1,0,1,1,1,1],
    [1,2,2,2,0,2,2,2,2,2,2,2,2,2,0,2,2,2,1],
    [1,1,1,1,0,1,0,1,1,2,1,1,0,1,0,1,1,1,1],
    [1,0,0,0,0,0,0,1,2,2,2,1,0,0,0,0,0,0,1],
    [1,0,1,1,0,1,0,1,1,1,1,1,0,1,0,1,1,0,1],
    [1,0,0,1,0,0,0,0,0,2,0,0,0,0,0,1,0,0,1],
    [1,1,0,1,0,1,0,1,1,1,1,1,0,1,0,1,0,1,1],
    [1,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pac-Man")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 24, bold=True)

# Game State
pacman_pos = [11, 9]
pacman_dir = [0, 0]
score = 0
ghosts = [
    {"pos": [7, 8], "dir": [0, -1], "color": RED},
    {"pos": [7, 9], "dir": [0, 1], "color": PINK},
    {"pos": [7, 10], "dir": [-1, 0], "color": CYAN},
]

def valid_move(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS and LAYOUT[r][c] != 1

def move_ghosts():
    for g in ghosts:
        r, c = g["pos"]
        dr, dc = g["dir"]
        # Pick valid directions, avoiding immediate 180-degree turns if possible
        options = []
        for nr, nc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if valid_move(r + nr, c + nc) and (nr, nc) != (-dr, -dc):
                options.append((nr, nc))
        if not options and valid_move(r - dr, c - dc):
            options.append((-dr, -dc))
        if options:
            g["dir"] = random.choice(options)
            g["pos"][0] += g["dir"][0]
            g["pos"][1] += g["dir"][1]

def draw():
    screen.fill(BLACK)
    pellets_left = 0

    # Draw Maze and Pellets
    for r in range(ROWS):
        for c in range(COLS):
            x, y = c * TILE_SIZE, r * TILE_SIZE
            if LAYOUT[r][c] == 1:
                pygame.draw.rect(screen, BLUE, (x, y, TILE_SIZE, TILE_SIZE))
            elif LAYOUT[r][c] == 0:
                pellets_left += 1
                pygame.draw.circle(screen, WHITE, (x + TILE_SIZE // 2, y + TILE_SIZE // 2), 4)

    # Draw Pac-Man
    px = pacman_pos[1] * TILE_SIZE + TILE_SIZE // 2
    py = pacman_pos[0] * TILE_SIZE + TILE_SIZE // 2
    pygame.draw.circle(screen, YELLOW, (px, py), TILE_SIZE // 2 - 2)

    # Draw Ghosts
    for g in ghosts:
        gx = g["pos"][1] * TILE_SIZE + TILE_SIZE // 2
        gy = g["pos"][0] * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.circle(screen, g["color"], (gx, gy), TILE_SIZE // 2 - 2)

    # Draw Score
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, HEIGHT - 32))
    pygame.display.flip()
    return pellets_left

# Main Game Loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: pacman_dir = [-1, 0]
            elif event.key == pygame.K_DOWN: pacman_dir = [1, 0]
            elif event.key == pygame.K_LEFT: pacman_dir = [0, -1]
            elif event.key == pygame.K_RIGHT: pacman_dir = [0, 1]

    # Move Pac-Man
    next_r = pacman_pos[0] + pacman_dir[0]
    next_c = pacman_pos[1] + pacman_dir[1]
    if valid_move(next_r, next_c):
        pacman_pos = [next_r, next_c]

    # Eat Pellet
    if LAYOUT[pacman_pos[0]][pacman_pos[1]] == 0:
        LAYOUT[pacman_pos[0]][pacman_pos[1]] = 2
        score += 10

    # Check Collision Before & After Ghost Move
    if any(g["pos"] == pacman_pos for g in ghosts):
        print(f"Game Over! Final Score: {score}")
        break

    move_ghosts()

    if any(g["pos"] == pacman_pos for g in ghosts):
        print(f"Game Over! Final Score: {score}")
        break

    if draw() == 0:
        print(f"You Win! Final Score: {score}")
        break

    clock.tick(FPS)

pygame.quit()
sys.exit()