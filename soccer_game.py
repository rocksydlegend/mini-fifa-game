import pygame
import sys
import math
import random
from dataclasses import dataclass

# =========================================================
# MINI FIFA STYLE SOCCER GAME
# =========================================================

pygame.init()

# -----------------------
# CONFIG
# -----------------------
WIDTH, HEIGHT = 1000, 700
FPS = 60
GOAL_WIDTH = 220
MATCH_TIME = 180  # seconds

# Colors
WHITE = (255, 255, 255)
GREEN = (40, 140, 60)
DARK_GREEN = (30, 110, 45)
BLACK = (0, 0, 0)
BLUE = (50, 140, 255)
RED = (220, 50, 70)
YELLOW = (255, 210, 0)
GRAY = (180, 180, 180)

# Gameplay
PLAYER_RADIUS = 16
BALL_RADIUS = 9

PLAYER_SPEED = 260
AI_SPEED = 210

PASS_SPEED = 520
SHOT_SPEED = 900

BALL_FRICTION = 0.992
POSSESSION_DISTANCE = 24

# -----------------------
# WINDOW
# -----------------------
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini FIFA Prototype")

clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 54)

# =========================================================
# HELPERS
# =========================================================

def clamp(value, low, high):
    return max(low, min(high, value))


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def normalize(vx, vy):
    length = math.hypot(vx, vy)

    if length == 0:
        return 0, 0

    return vx / length, vy / length


# =========================================================
# DATA CLASSES
# =========================================================

@dataclass
class Player:
    x: float
    y: float
    team: int
    color: tuple
    controlled: bool
    name: str

    has_ball: bool = False
    speed: float = PLAYER_SPEED

    vx: float = 0
    vy: float = 0

    def pos(self):
        return (self.x, self.y)

    def move(self, dx, dy, dt):
        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt

        self.x = clamp(self.x, PLAYER_RADIUS, WIDTH - PLAYER_RADIUS)
        self.y = clamp(self.y, PLAYER_RADIUS, HEIGHT - PLAYER_RADIUS)

@dataclass
class Ball:
    x: float
    y: float

    vx: float = 0
    vy: float = 0

    holder = None

    def pos(self):
        return (self.x, self.y)


# =========================================================
# GAME CLASS
# =========================================================

class SoccerGame:

    def __init__(self):

        self.reset_game()

    # -----------------------------------------------------

    def reset_game(self):

        self.blue_score = 0
        self.red_score = 0

        self.time_left = MATCH_TIME

        self.players = []

        # BLUE TEAM
        self.blue1 = Player(
            180,
            HEIGHT // 2 - 80,
            0,
            BLUE,
            True,
            "Blue Captain"
        )

        self.blue2 = Player(
            260,
            HEIGHT // 2 + 80,
            0,
            BLUE,
            False,
            "Blue AI"
        )

        # RED TEAM
        self.red1 = Player(
            WIDTH - 180,
            HEIGHT // 2 - 80,
            1,
            RED,
            True,
            "Red Captain"
        )

        self.red2 = Player(
            WIDTH - 260,
            HEIGHT // 2 + 80,
            1,
            RED,
            False,
            "Red AI"
        )

        self.players.extend([
            self.blue1,
            self.blue2,
            self.red1,
            self.red2
        ])

        # BALL
        self.ball = Ball(WIDTH / 2, HEIGHT / 2)

    # -----------------------------------------------------

    def reset_positions(self):

        self.blue1.x, self.blue1.y = 180, HEIGHT // 2 - 80
        self.blue2.x, self.blue2.y = 260, HEIGHT // 2 + 80

        self.red1.x, self.red1.y = WIDTH - 180, HEIGHT // 2 - 80
        self.red2.x, self.red2.y = WIDTH - 260, HEIGHT // 2 + 80

        for p in self.players:
            p.has_ball = False

        self.ball.x = WIDTH / 2
        self.ball.y = HEIGHT / 2
        self.ball.vx = 0
        self.ball.vy = 0
        self.ball.holder = None

    # -----------------------------------------------------

    def give_ball(self, player):

        for p in self.players:
            p.has_ball = False

        player.has_ball = True
        self.ball.holder = player

    # -----------------------------------------------------

    def kick_ball(self, player, speed):

        target_x = WIDTH if player.team == 0 else 0
        target_y = HEIGHT / 2

        dx = target_x - player.x
        dy = target_y - player.y

        nx, ny = normalize(dx, dy)

        self.ball.holder = None
        player.has_ball = False

        self.ball.vx = nx * speed
        self.ball.vy = ny * speed

    # -----------------------------------------------------

    def pass_ball(self, player):

        teammates = [
            p for p in self.players
            if p.team == player.team and p != player
        ]

        if not teammates:
            return

        teammate = min(
            teammates,
            key=lambda p: distance(player.pos(), p.pos())
        )

        dx = teammate.x - player.x
        dy = teammate.y - player.y

        nx, ny = normalize(dx, dy)

        player.has_ball = False
        self.ball.holder = None

        self.ball.vx = nx * PASS_SPEED
        self.ball.vy = ny * PASS_SPEED

    # -----------------------------------------------------

    def update_human_controls(self, dt):

        keys = pygame.key.get_pressed()

        # BLUE PLAYER
        dx = dy = 0

        if keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_s]:
            dy += 1
        if keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_d]:
            dx += 1

        nx, ny = normalize(dx, dy)
        self.blue1.move(nx, ny, dt)

        # RED PLAYER
        dx = dy = 0

        if keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_RIGHT]:
            dx += 1

        nx, ny = normalize(dx, dy)
        self.red1.move(nx, ny, dt)

    # -----------------------------------------------------

    def update_ai(self, dt):

        ai_players = [self.blue2, self.red2]

        for ai in ai_players:

            # Chase ball
            target_x = self.ball.x
            target_y = self.ball.y

            if self.ball.holder and self.ball.holder.team == ai.team:
                # Move toward goal if teammate has ball
                target_x = WIDTH if ai.team == 0 else 0
                target_y = HEIGHT / 2

            dx = target_x - ai.x
            dy = target_y - ai.y

            nx, ny = normalize(dx, dy)

            ai.x += nx * AI_SPEED * dt
            ai.y += ny * AI_SPEED * dt

            ai.x = clamp(ai.x, PLAYER_RADIUS, WIDTH - PLAYER_RADIUS)
            ai.y = clamp(ai.y, PLAYER_RADIUS, HEIGHT - PLAYER_RADIUS)

            # AI shoot chance
            if ai.has_ball:

                goal_distance = abs(
                    (WIDTH if ai.team == 0 else 0) - ai.x
                )

                if goal_distance < 260:
                    self.kick_ball(ai, SHOT_SPEED)
                else:
                    if random.random() < 0.01:
                        self.pass_ball(ai)

    # -----------------------------------------------------

    def update_ball(self, dt):

        # Follow holder
        if self.ball.holder:

            holder = self.ball.holder

            offset = 18 if holder.team == 0 else -18

            self.ball.x = holder.x + offset
            self.ball.y = holder.y

            return

        # Free ball movement
        self.ball.x += self.ball.vx * dt
        self.ball.y += self.ball.vy * dt

        self.ball.vx *= BALL_FRICTION
        self.ball.vy *= BALL_FRICTION

        # Wall collisions
        if self.ball.y < BALL_RADIUS:
            self.ball.y = BALL_RADIUS
            self.ball.vy *= -0.8

        if self.ball.y > HEIGHT - BALL_RADIUS:
            self.ball.y = HEIGHT - BALL_RADIUS
            self.ball.vy *= -0.8

        # Left wall
        if self.ball.x < BALL_RADIUS:

            # Goal check
            if HEIGHT / 2 - GOAL_WIDTH / 2 < self.ball.y < HEIGHT / 2 + GOAL_WIDTH / 2:
                self.blue_score += 1
                self.reset_positions()
                return

            self.ball.x = BALL_RADIUS
            self.ball.vx *= -0.8

        # Right wall
        if self.ball.x > WIDTH - BALL_RADIUS:

            # Goal check
            if HEIGHT / 2 - GOAL_WIDTH / 2 < self.ball.y < HEIGHT / 2 + GOAL_WIDTH / 2:
                self.red_score += 1
                self.reset_positions()
                return

            self.ball.x = WIDTH - BALL_RADIUS
            self.ball.vx *= -0.8

        # Ball possession
        for p in self.players:

            if distance(p.pos(), self.ball.pos()) < POSSESSION_DISTANCE:
                self.give_ball(p)
                break

    # -----------------------------------------------------

    def draw_pitch(self):

        screen.fill(GREEN)

        # stripes
        for i in range(0, WIDTH, 120):
            color = GREEN if (i // 120) % 2 == 0 else DARK_GREEN
            pygame.draw.rect(screen, color, (i, 0, 120, HEIGHT))

        # Mid line
        pygame.draw.line(
            screen,
            WHITE,
            (WIDTH // 2, 0),
            (WIDTH // 2, HEIGHT),
            4
        )

        # Center circle
        pygame.draw.circle(
            screen,
            WHITE,
            (WIDTH // 2, HEIGHT // 2),
            90,
            4
        )

        # Goals
        pygame.draw.rect(
            screen,
            WHITE,
            (0, HEIGHT / 2 - GOAL_WIDTH / 2, 12, GOAL_WIDTH)
        )

        pygame.draw.rect(
            screen,
            WHITE,
            (WIDTH - 12, HEIGHT / 2 - GOAL_WIDTH / 2, 12, GOAL_WIDTH)
        )

    # -----------------------------------------------------

    def draw_players(self):

        for p in self.players:

            pygame.draw.circle(
                screen,
                p.color,
                (int(p.x), int(p.y)),
                PLAYER_RADIUS
            )

            if p.has_ball:
                pygame.draw.circle(
                    screen,
                    YELLOW,
                    (int(p.x), int(p.y)),
                    PLAYER_RADIUS + 4,
                    3
                )

    # -----------------------------------------------------

    def draw_ball(self):

        pygame.draw.circle(
            screen,
            WHITE,
            (int(self.ball.x), int(self.ball.y)),
            BALL_RADIUS
        )

        pygame.draw.circle(
            screen,
            BLACK,
            (int(self.ball.x), int(self.ball.y)),
            BALL_RADIUS,
            2
        )

    # -----------------------------------------------------

    def draw_ui(self):

        timer = max(0, int(self.time_left))

        minutes = timer // 60
        seconds = timer % 60

        score_text = font.render(
            f"BLUE {self.blue_score} - {self.red_score} RED",
            True,
            WHITE
        )

        time_text = font.render(
            f"{minutes:02}:{seconds:02}",
            True,
            YELLOW
        )

        controls = font.render(
            "Blue: WASD + F(pass) G(shoot) | Red: Arrows + K(pass) L(shoot)",
            True,
            WHITE
        )

        screen.blit(score_text, (20, 20))
        screen.blit(time_text, (WIDTH // 2 - 40, 20))
        screen.blit(controls, (140, HEIGHT - 35))

        # Match over
        if self.time_left <= 0:

            if self.blue_score > self.red_score:
                result = "BLUE WINS!"
            elif self.red_score > self.blue_score:
                result = "RED WINS!"
            else:
                result = "DRAW!"

            txt = big_font.render(result, True, YELLOW)

            screen.blit(
                txt,
                (
                    WIDTH // 2 - txt.get_width() // 2,
                    HEIGHT // 2 - 40
                )
            )

    # -----------------------------------------------------

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                # BLUE PASS
                if event.key == pygame.K_f:
                    if self.blue1.has_ball:
                        self.pass_ball(self.blue1)

                # BLUE SHOOT
                if event.key == pygame.K_g:
                    if self.blue1.has_ball:
                        self.kick_ball(self.blue1, SHOT_SPEED)

                # RED PASS
                if event.key == pygame.K_k:
                    if self.red1.has_ball:
                        self.pass_ball(self.red1)

                # RED SHOOT
                if event.key == pygame.K_l:
                    if self.red1.has_ball:
                        self.kick_ball(self.red1, SHOT_SPEED)

    # -----------------------------------------------------

    def update(self, dt):

        if self.time_left <= 0:
            return

        self.time_left -= dt

        self.update_human_controls(dt)
        self.update_ai(dt)
        self.update_ball(dt)

    # -----------------------------------------------------

    def draw(self):

        self.draw_pitch()
        self.draw_players()
        self.draw_ball()
        self.draw_ui()

        pygame.display.flip()

    # -----------------------------------------------------

    def run(self):

        while True:

            dt = clock.tick(FPS) / 1000

            self.handle_events()
            self.update(dt)
            self.draw()


# =========================================================
# START GAME
# =========================================================

if __name__ == "__main__":

    game = SoccerGame()
    game.run()