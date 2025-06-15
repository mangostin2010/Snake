# ========== 필요한 라이브러리 임포트 ==========
import os
import random
import time
import sys
import requests
import pygame
import json

# ========== 필요한 라이브러리 설치 끝 ==========

DEVELOPERS = [
    "Sam", 
    "Samuel", 
    "Ryan", 
    "Alice", 
    "Justin"
]
VERSION = '1.0.1'

# ========== 리소스 폴더 및 경로 선언 ==========

RESOURCE_DIR = "snake_resources"
DEFAULT_FONT = os.path.join(RESOURCE_DIR, "Merriweather.ttf")
KOREAN_FONT = os.path.join(RESOURCE_DIR, 'ChironSungHK.ttf')
BOLT_IMG_PATH = os.path.join(RESOURCE_DIR, "bolt.png")
STAR_IMG_PATH = os.path.join(RESOURCE_DIR, "star.png")
BGM_PATH = os.path.join(RESOURCE_DIR, "bgm.mp3")
BGM2_PATH = os.path.join(RESOURCE_DIR, "bgm2.mp3")
APPLE_PATH = os.path.join(RESOURCE_DIR, "apple.png")
BACKGROUND_IMG_PATH = os.path.join(RESOURCE_DIR, "background.png")

# ========== 필요한 리소스 다운로드 하는 부분 ==========
'''
아래 부분은 필요한 리소스를 인터넷에서 다운로드 하기 때문에
Github Repository 안에서 리소스를 이제 관리하므로 필요 없습니다.
'''

def download_file(url, save_path):
    if os.path.exists(save_path):
        print(f"{save_path} already exists, skipping download.")
        return True
    try:
        print(f"Downloading {save_path} ...")
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded {save_path}")
        return True
    except Exception as e:
        print(f"Failed to download {save_path}: {e}")
        return False

def initialize():
    if not os.path.exists(RESOURCE_DIR):
        os.makedirs(RESOURCE_DIR)
    resources = [
        {
            'url': "https://github.com/SorkinType/Merriweather/raw/refs/heads/master/fonts/ttf/Merriweather-Regular.ttf",
            'save_path': DEFAULT_FONT,
        },
        {
            'url': 'https://github.com/chiron-fonts/chiron-sung-hk-gf/raw/refs/heads/main/fonts/variable/ChironSungHK-%5Bwght%5D.ttf',
            'save_path': KOREAN_FONT,
        },
        {
            'url': "https://static-00.iconduck.com/assets.00/lightning-bolt-icon-1127x2048-dhh42rkh.png",
            'save_path': BOLT_IMG_PATH,
        },
        {
            'url': 'https://i.namu.wiki/i/Mu2d-mBGLbMbgiN5pxFQ9hrqJcugAvw-6pvwJk66vHkaKMWmM80V6PZGbhhBEn6SNhIVbBcs8-6ndJLLLuptSQ.webp',
            'save_path': STAR_IMG_PATH
        },
        {
            'url': 'https://cdn.pixabay.com/download/audio/2025/06/10/audio_2ba36321f7.mp3?filename=treasure-hunt-8-bit-chiptune-adventure-music-357568.mp3',
            'save_path': BGM_PATH
        },
        {
            'url': 'https://cdn.pixabay.com/download/audio/2025/05/03/audio_327c570a65.mp3?filename=exploration-chiptune-rpg-adventure-theme-336428.mp3',
            'save_path': BGM2_PATH
        },
        {
            'url': 'https://github.com/mangostin2010/Snake/blob/main/snake_resources/apple.png?raw=true',
            'save_path': APPLE_PATH
        },
        {
            'url': 'https://raw.githubusercontent.com/mangostin2010/Snake/refs/heads/main/snake_resources/background.png',
            'save_path': BACKGROUND_IMG_PATH
        }
    ]
    for res in resources:
        success = download_file(res['url'], res['save_path'])
        if not success:
            print(f"Warning: {res['save_path']} could not be downloaded.")


# ========== 게임 코드 시작 ==========

# 기본 변수들
fps = 30  # 게임 속도
frame = (1024, 576)
black = pygame.Color(0, 0, 0)
white = pygame.Color(255, 255, 255)
red = pygame.Color(255, 0, 0)
green = pygame.Color(0, 255, 0)
blue = pygame.Color(0, 0, 255)
fps_controller = pygame.time.Clock()

DIFFICULTY_LEVELS = ["쉬움", "중간", "어려움"]
difficulty = 0  # 0=쉬움, 1=중간, 2=어려움

# 난이도에 따른 음식 개수 및 속도/장애물 등
FOOD_COUNT_BY_DIFFICULTY = [3, 2, 1]
FPS_BY_DIFFICULTY = [20, 30, 40]
OBSTACLE_COUNT_BY_DIFFICULTY = [0, 3, 8]  # 추가: 어려움일수록 장애물 증가


game_mode = "single"  # "single" 또는 "ai"
last_ai_score = 0
last_player_score = 0
last_result = None    # "win" | "lose" | None

# --- 별(무적) 아이템 관련 ---
star_img = None # 나중에 추가됩니당 (밑 __name__ == "__main__"에서)
STAR_RESPAWN_INTERVAL = 1  # 프레임 단위
star_pos = [0, 0]
star_spawn = False
star_timer = 0
STAR_FALL_SPEED = 7  # 별이 떨어지는 속도 (픽셀/프레임)

# --- 무적 상태 (플레이어/AI 각각) ---
invincible = False
invincible_timer = 0
ai_invincible = False
ai_invincible_timer = 0
INVINCIBLE_DURATION = 5.0  # 초
INVINCIBLE_FPS_BOOST = 12  # 무적시 추가 속도
normal_fps = 30  # 현재 라운드의 기본 FPS

GAME_DATA_PATH = os.path.join(RESOURCE_DIR, "game_data.json")
high_score = 0

def get_random_pos(exclude=None):
    while True:
        pos = [random.randrange(1, (frame[0] // 10)) * 10,
               random.randrange(1, (frame[1] // 10)) * 10]
        if not exclude or pos not in exclude:
            return pos

def reset_game():
    global snake_pos, snake_body, direction, score, fps, main_window
    global food_pos_list, food_spawn_list
    global item_pos, item_spawn, item_timer
    global star_pos, star_spawn, star_timer, invincible, invincible_timer, normal_fps
    global obstacles

    snake_pos = [100, 50]
    snake_body = [[100, 50], [90, 50], [80, 50]]
    direction = 'RIGHT'
    score = 0
    fps = FPS_BY_DIFFICULTY[difficulty]
    normal_fps = fps

    # 음식 여러 개
    food_pos_list = []
    food_spawn_list = []
    for _ in range(FOOD_COUNT_BY_DIFFICULTY[difficulty]):
        food_pos_list.append(get_random_pos(snake_body))
        food_spawn_list.append(True)

    # 장애물 여러 개
    obstacles = []
    for _ in range(OBSTACLE_COUNT_BY_DIFFICULTY[difficulty]):
        pos = get_random_pos(snake_body + food_pos_list)
        obstacles.append(pos)

    # 아이템/별 초기화
    item_pos = get_random_pos(snake_body + food_pos_list + obstacles)
    item_spawn = False
    item_timer = 0

    star_pos = get_random_pos(snake_body + food_pos_list + obstacles)
    star_spawn = False
    star_timer = 0
    invincible = False
    invincible_timer = 0

def load_high_score():
    if not os.path.exists(GAME_DATA_PATH):
        return 0
    try:
        with open(GAME_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("high_score", 0)
    except Exception:
        return 0

def save_high_score(score):
    data = {"high_score": score}
    with open(GAME_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)

def reset_ai_game():
    """AI 모드용: 플레이어·AI 뱀 동시에 초기화"""
    global snake_pos, snake_body, direction, score
    global ai_snake_pos, ai_snake_body, ai_direction, ai_score
    global food_pos, food_spawn, fps, item_pos, item_spawn, item_timer
    # 플레이어
    snake_pos = [100, 50]
    snake_body = [[100, 50], [90, 50], [80, 50]]
    direction = 'RIGHT'
    score = 0
    # AI
    ai_snake_pos = [400, 300]
    ai_snake_body = [[400, 300], [390, 300], [380, 300]]
    ai_direction = 'LEFT'
    ai_score = 0
    # 공통
    food_pos = get_random_pos(snake_body + ai_snake_body)
    food_spawn = True
    fps = 30
    # 아이템
    item_pos = get_random_pos(snake_body + ai_snake_body + [food_pos])
    item_spawn = False
    item_timer = 0

def Init(size):
    check_errors = pygame.init()
    if check_errors[1] > 0:
        print(f'[!] Had {check_errors[1]} errors when initialising game, exiting...')
        sys.exit(-1)
    else:
        print('[+] Game successfully initialised')

    pygame.display.set_caption('Snake')
    game_window = pygame.display.set_mode(size)
    return game_window

def show_score(window, size, choice, color, font, fontsize, ai_score=None):
    score_font = pygame.font.Font(DEFAULT_FONT, fontsize)
    if ai_score is not None:
        score_surface = score_font.render(f'You: {score}   AI: {ai_score}', True, color)
    else:
        score_surface = score_font.render('Score : ' + str(score), True, color)
    score_rect = score_surface.get_rect()
    if choice == 1:
        score_rect.midtop = (size[0] / 10, 15)
    else:
        score_rect.midtop = (size[0] / 2, size[1] / 1.25)
    window.blit(score_surface, score_rect)

def get_keyboard(key, cur_dir):
    if cur_dir != 'DOWN' and key == pygame.K_UP:
        return 'UP'
    elif cur_dir != 'UP' and key == pygame.K_DOWN:
        return 'DOWN'
    elif cur_dir != 'RIGHT' and key == pygame.K_LEFT:
        return 'LEFT'
    elif cur_dir != 'LEFT' and key == pygame.K_RIGHT:
        return 'RIGHT'
    return cur_dir

def show_game():
    global snake_pos, snake_body, direction, score, fps, main_window
    global item_pos, item_spawn, item_timer
    global star_img, star_pos, star_spawn, star_timer
    global invincible, invincible_timer, normal_fps
    global food_pos_list, food_spawn_list, obstacles

    item_img = pygame.image.load(BOLT_IMG_PATH)
    item_img = pygame.transform.scale(item_img, (15, 15))
    ITEM_RESPAWN_INTERVAL = 150

    last_time = time.time()

    while True:
        now = time.time()
        dt = now - last_time
        last_time = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                else:
                    direction = get_keyboard(event.key, direction)

        # 뱀 이동
        if direction == 'UP':
            snake_pos[1] -= 10
        elif direction == 'DOWN':
            snake_pos[1] += 10
        elif direction == 'LEFT':
            snake_pos[0] -= 10
        elif direction == 'RIGHT':
            snake_pos[0] += 10
        snake_body.insert(0, list(snake_pos))

        # --- 음식 여러 개 처리 ---
        ate_food = False
        for i, food_pos in enumerate(food_pos_list):
            if snake_pos == food_pos:
                score += 1
                if score % 3 == 0 and not invincible:
                    fps += 5
                    normal_fps = fps
                food_spawn_list[i] = False
                ate_food = True
        if not ate_food:
            snake_body.pop()
        # 음식 재생성
        for i in range(len(food_pos_list)):
            if not food_spawn_list[i]:
                used = snake_body + [pos for j, pos in enumerate(food_pos_list) if food_spawn_list[j]] + obstacles
                food_pos_list[i] = get_random_pos(used)
                food_spawn_list[i] = True

        # --- 아이템 시스템 ---
        if not item_spawn:
            item_timer += 1
            if item_timer >= ITEM_RESPAWN_INTERVAL:
                used = snake_body + food_pos_list + obstacles + ([star_pos] if star_spawn else [])
                item_pos = get_random_pos(used)
                item_spawn = True
                item_timer = 0
        if item_spawn and snake_pos == item_pos:
            if not invincible:
                fps += 5
                normal_fps = fps
            item_spawn = False
            item_timer = 0

        # --- 별 시스템 ---
        if not star_spawn:
            star_timer += 1
            if star_timer >= STAR_RESPAWN_INTERVAL:
                star_pos = [random.randrange(0, frame[0] // 10) * 10, -16]
                star_spawn = True
                star_timer = 0
        if star_spawn:
            star_pos[1] += STAR_FALL_SPEED
            if star_pos[1] > frame[1]:
                star_spawn = False
                star_timer = 0    

        snake_rect = pygame.Rect(snake_pos[0], snake_pos[1], 10, 10)
        star_rect = pygame.Rect(star_pos[0], star_pos[1], 16, 16)
        if star_spawn and snake_rect.colliderect(star_rect):
            invincible = True
            invincible_timer = INVINCIBLE_DURATION
            star_spawn = False
            star_timer = 0
            fps = normal_fps + INVINCIBLE_FPS_BOOST        

        # --- 무적 상태 관리 ---
        if invincible:
            invincible_timer -= dt
            if invincible_timer <= 0:
                invincible = False
                fps = normal_fps

        # --- 그리기 ---
        main_window.fill(black)
        for i, pos in enumerate(snake_body):
            if invincible:
                color = (255, 255, 80) if (int(time.time()*8)%2==0 or i==0) else (255, 200, 60)
            else:
                color = green
            pygame.draw.rect(main_window, color, pygame.Rect(pos[0], pos[1], 10, 10))
        # 음식 여러 개 그리기
        for food_pos in food_pos_list:
            main_window.blit(apple_img, (food_pos[0], food_pos[1]))
        # 장애물 그리기
        for obs in obstacles:
            pygame.draw.rect(main_window, (120,120,120), pygame.Rect(obs[0], obs[1], 10, 10))
        if item_spawn:
            main_window.blit(item_img, (item_pos[0], item_pos[1]))
        if star_spawn:
            main_window.blit(star_img, (star_pos[0], star_pos[1]))

        # --- 충돌 판정 ---
        hit_wall = (
            snake_pos[0] < 0 or snake_pos[0] > frame[0] - 10 or
            snake_pos[1] < 0 or snake_pos[1] > frame[1] - 10
        )
        if hit_wall:
            if invincible:
                if snake_pos[0] < 0:
                    snake_pos[0] = frame[0] - 10
                elif snake_pos[0] > frame[0] - 10:
                    snake_pos[0] = 0
                if snake_pos[1] < 0:
                    snake_pos[1] = frame[1] - 10
                elif snake_pos[1] > frame[1] - 10:
                    snake_pos[1] = 0
                snake_body[0] = list(snake_pos)
            else:
                game_over(main_window, frame)
                return

        for block in snake_body[1:]:
            if snake_pos == block:
                game_over(main_window, frame)
                return

        # --- 장애물 충돌 ---
        if snake_pos in obstacles:
            if not invincible:
                game_over(main_window, frame)
                return

        show_score(main_window, frame, 1, white, 'consolas', 20)
        pygame.display.update()
        fps_controller.tick(fps)


def ai_choose_direction(ai_snake_pos, ai_snake_body, food_pos, player_snake_body, item_pos=None):
    """
    음식과의 x축이 다르면 x축 먼저 맞춤, 그 다음 y축 맞춤.
    충돌이 예상되는 방향은 건너뜀.
    """
    x, y = ai_snake_pos
    fx, fy = food_pos

    candidates = []

    # 1. x축 먼저 맞추기
    if x < fx:
        candidates.append('RIGHT')
    elif x > fx:
        candidates.append('LEFT')
    # 2. y축 맞추기
    if y < fy:
        candidates.append('DOWN')
    elif y > fy:
        candidates.append('UP')

    # 장애물 체크
    for d in candidates:
        nx, ny = x, y
        if d == 'UP':
            ny -= 10
        elif d == 'DOWN':
            ny += 10
        elif d == 'LEFT':
            nx -= 10
        elif d == 'RIGHT':
            nx += 10
        next_pos = [nx, ny]
        if nx < 0 or nx > frame[0] - 10 or ny < 0 or ny > frame[1] - 10:
            continue
        if next_pos in ai_snake_body or next_pos in player_snake_body:
            continue
        return d

    # 만약 위에서 선택 못하면, 살아남을 수 있는 아무 방향
    for d in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
        nx, ny = x, y
        if d == 'UP':
            ny -= 10
        elif d == 'DOWN':
            ny += 10
        elif d == 'LEFT':
            nx -= 10
        elif d == 'RIGHT':
            nx += 10
        next_pos = [nx, ny]
        if nx < 0 or nx > frame[0] - 10 or ny < 0 or ny > frame[1] - 10:
            continue
        if next_pos in ai_snake_body or next_pos in player_snake_body:
            continue
        return d
    return 'UP'  # 어디든 부딪혀야한다면 아무 방향


def show_ai_match():
    global snake_pos, snake_body, direction, score
    global ai_snake_pos, ai_snake_body, ai_direction, ai_score
    global food_pos, food_spawn, fps, main_window
    global item_pos, item_spawn, item_timer
    global last_ai_score, last_player_score, last_result
    global star_img, star_pos, star_spawn, star_timer
    global invincible, invincible_timer, ai_invincible, ai_invincible_timer, normal_fps

    item_img = pygame.image.load(BOLT_IMG_PATH)
    item_img = pygame.transform.scale(item_img, (15, 15))
    ITEM_RESPAWN_INTERVAL = 150

    last_time = time.time()

    while True:
        now = time.time()
        dt = now - last_time
        last_time = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                else:
                    direction = get_keyboard(event.key, direction)

        # --- 플레이어 이동 ---
        if direction == 'UP':
            snake_pos[1] -= 10
        elif direction == 'DOWN':
            snake_pos[1] += 10
        elif direction == 'LEFT':
            snake_pos[0] -= 10
        elif direction == 'RIGHT':
            snake_pos[0] += 10
        snake_body.insert(0, list(snake_pos))

        # --- AI 이동 ---
        ai_direction = ai_choose_direction(ai_snake_pos, ai_snake_body, food_pos, snake_body)
        if ai_direction == 'UP':
            ai_snake_pos[1] -= 10
        elif ai_direction == 'DOWN':
            ai_snake_pos[1] += 10
        elif ai_direction == 'LEFT':
            ai_snake_pos[0] -= 10
        elif ai_direction == 'RIGHT':
            ai_snake_pos[0] += 10
        ai_snake_body.insert(0, list(ai_snake_pos))

        # --- 음식 먹기 ---
        # 플레이어
        if snake_pos == food_pos:
            score += 1
            food_spawn = False
        else:
            snake_body.pop()
        # AI
        if ai_snake_pos == food_pos:
            ai_score += 1
            food_spawn = False
        else:
            ai_snake_body.pop()

        # 음식 새로 생성
        if not food_spawn:
            used = snake_body + ai_snake_body + ([item_pos] if item_spawn else []) + ([star_pos] if star_spawn else [])
            food_pos = get_random_pos(used)
            food_spawn = True

        # --- 일반 아이템 관리 ---
        if not item_spawn:
            item_timer += 1
            if item_timer >= ITEM_RESPAWN_INTERVAL:
                used = snake_body + ai_snake_body + [food_pos] + ([star_pos] if star_spawn else [])
                item_pos = get_random_pos(used)
                item_spawn = True
                item_timer = 0

        # 플레이어가 아이템 먹음
        if item_spawn and snake_pos == item_pos:
            if not invincible:
                fps += 5
                normal_fps = fps
            item_spawn = False
            item_timer = 0
        # AI가 아이템 먹음
        if item_spawn and ai_snake_pos == item_pos:
            if not ai_invincible:
                fps += 5
                normal_fps = fps
            item_spawn = False
            item_timer = 0

        # --- 별(무적) 아이템 관리 ---
        if not star_spawn:
            star_timer += 1
            if star_timer >= STAR_RESPAWN_INTERVAL:
                used = snake_body + ai_snake_body + [food_pos] + ([item_pos] if item_spawn else [])
                star_pos = [random.randrange(0, frame[0] // 10) * 10, -16]
                star_spawn = True
                star_timer = 0

        if star_spawn:
            star_pos[1] += STAR_FALL_SPEED
            if star_pos[1] > frame[1]:
                star_spawn = False
                star_timer = 0

        snake_rect = pygame.Rect(snake_pos[0], snake_pos[1], 10, 10)
        ai_rect = pygame.Rect(ai_snake_pos[0], ai_snake_pos[1], 10, 10)
        star_rect = pygame.Rect(star_pos[0], star_pos[1], 16, 16)  # 별 크기와 맞게

        # 플레이어가 별 먹음
        if star_spawn and snake_rect.colliderect(star_rect):
            invincible = True
            invincible_timer = INVINCIBLE_DURATION
            star_spawn = False
            star_timer = 0
            fps = normal_fps + INVINCIBLE_FPS_BOOST

        # AI가 별 먹음
        if star_spawn and ai_rect.colliderect(star_rect):
            ai_invincible = True
            ai_invincible_timer = INVINCIBLE_DURATION
            star_spawn = False
            star_timer = 0
            fps = normal_fps + INVINCIBLE_FPS_BOOST


        # --- 무적 타이머 관리 ---
        if invincible:
            invincible_timer -= dt
            if invincible_timer <= 0:
                invincible = False
                fps = normal_fps
        if ai_invincible:
            ai_invincible_timer -= dt
            if ai_invincible_timer <= 0:
                ai_invincible = False
                fps = normal_fps

        # --- 그리기 ---
        main_window.fill(black)
        # 플레이어 뱀
        for i, pos in enumerate(snake_body):
            if invincible:
                color = (255, 255, 80) if (int(time.time()*8)%2==0 or i==0) else (255, 200, 60)
            else:
                color = (60, 240, 60)
            pygame.draw.rect(main_window, color, pygame.Rect(pos[0], pos[1], 10, 10))
        # AI 뱀
        for i, pos in enumerate(ai_snake_body):
            if ai_invincible:
                color = (255, 255, 80) if (int(time.time()*8)%2==0 or i==0) else (255, 180, 120)
            else:
                color = (60, 120, 220)
            pygame.draw.rect(main_window, color, pygame.Rect(pos[0], pos[1], 10, 10))
        # 음식
        # pygame.draw.rect(main_window, white, pygame.Rect(food_pos[0], food_pos[1], 10, 10))
        main_window.blit(apple_img, (food_pos[0], food_pos[1]))
        # 아이템
        if item_spawn:
            main_window.blit(item_img, (item_pos[0], item_pos[1]))
        # 별
        if star_spawn:
            main_window.blit(star_img, (star_pos[0], star_pos[1]))

        # --- 승패 판정 ---
        # 플레이어 벽 충돌
        hit_wall = (
            snake_pos[0] < 0 or snake_pos[0] > frame[0] - 10 or
            snake_pos[1] < 0 or snake_pos[1] > frame[1] - 10
        )
        if hit_wall:
            if invincible:
                # 반대편 순간이동
                if snake_pos[0] < 0: snake_pos[0] = frame[0] - 10
                elif snake_pos[0] > frame[0] - 10: snake_pos[0] = 0
                if snake_pos[1] < 0: snake_pos[1] = frame[1] - 10
                elif snake_pos[1] > frame[1] - 10: snake_pos[1] = 0
                snake_body[0] = list(snake_pos)
            else:
                last_player_score = score
                last_ai_score = ai_score
                last_result = "lose"
                show_ai_game_over(main_window, frame, "You Lose", score, ai_score)
                return

        # AI 벽 충돌
        ai_hit_wall = (
            ai_snake_pos[0] < 0 or ai_snake_pos[0] > frame[0] - 10 or
            ai_snake_pos[1] < 0 or ai_snake_pos[1] > frame[1] - 10
        )
        if ai_hit_wall:
            if ai_invincible:
                if ai_snake_pos[0] < 0: ai_snake_pos[0] = frame[0] - 10
                elif ai_snake_pos[0] > frame[0] - 10: ai_snake_pos[0] = 0
                if ai_snake_pos[1] < 0: ai_snake_pos[1] = frame[1] - 10
                elif ai_snake_pos[1] > frame[1] - 10: ai_snake_pos[1] = 0
                ai_snake_body[0] = list(ai_snake_pos)
            else:
                last_player_score = score
                last_ai_score = ai_score
                last_result = "win"
                show_ai_game_over(main_window, frame, "You Win", score, ai_score)
                return

        # 몸 충돌
        player_dead = (snake_pos in snake_body[1:] or (snake_pos in ai_snake_body and not invincible))
        ai_dead = (ai_snake_pos in ai_snake_body[1:] or (ai_snake_pos in snake_body and not ai_invincible))

        # 동시죽음: 플레이어 패배 우선
        if player_dead:
            last_player_score = score
            last_ai_score = ai_score
            last_result = "lose"
            show_ai_game_over(main_window, frame, "You Lose", score, ai_score)
            return
        elif ai_dead:
            last_player_score = score
            last_ai_score = ai_score
            last_result = "win"
            show_ai_game_over(main_window, frame, "You Win", score, ai_score)
            return

        show_score(main_window, frame, 1, white, 'consolas', 20, ai_score=ai_score)
        pygame.display.update()
        fps_controller.tick(fps)


def draw_gradient_background(surface, top_color, bottom_color):
    for y in range(frame[1]):
        ratio = y / frame[1]
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (frame[0], y))

def show_lobby(window, size, background_img):
    global game_mode, difficulty

    # 여러 뱀 초기화 (예: 5개)
    NUM_SNAKES = 5
    SNAKE_LEN = 5
    SNAKE_COLORS = [
        (60, 240, 60), (60, 120, 220), (240, 60, 60),
        (255, 160, 60), (210, 60, 180), (255, 255, 80), (80, 255, 255)
    ]
    snakes = []
    for i in range(NUM_SNAKES):
        start_x = random.randrange(10, size[0] - 100, 10)
        start_y = random.randrange(80, size[1] - 100, 10)
        direction = random.choice(['UP', 'DOWN', 'LEFT', 'RIGHT'])
        body = []
        for j in range(SNAKE_LEN):
            if direction == 'LEFT':
                body.append([start_x + j*10, start_y])
            elif direction == 'RIGHT':
                body.append([start_x - j*10, start_y])
            elif direction == 'UP':
                body.append([start_x, start_y + j*10])
            elif direction == 'DOWN':
                body.append([start_x, start_y - j*10])
        snakes.append({
            'body': body,
            'direction': direction,
            'color': SNAKE_COLORS[i % len(SNAKE_COLORS)],
            'move_cooldown': random.randint(0, 2),
            'straight_count': random.randint(8, 30)
        })

    # 버튼 UI
    button_width, button_height = 240, 80
    button_gap = 30
    # 버튼 Y 위치
    btn1_rect = pygame.Rect((size[0] - button_width) // 2, 160, button_width, button_height)
    btn2_rect = pygame.Rect((size[0] - button_width) // 2, 230 + button_gap, button_width, button_height)

    BUTTONS_TO_DIFFICULTY_GAP = 45
    difficulty_ui_y = btn2_rect.bottom + BUTTONS_TO_DIFFICULTY_GAP

    # 폰트
    title_font = pygame.font.Font(DEFAULT_FONT, 60)
    btn_font = pygame.font.Font(DEFAULT_FONT, 38)
    diff_font = pygame.font.Font(KOREAN_FONT, 35)
    info_font = pygame.font.Font(KOREAN_FONT, 19)  # 한글 설명용

    grad_top = (36, 198, 220)
    grad_bottom = (81, 74, 157)
    SAFE_MARGIN = 30

    # --- 난이도 UI ---
    diff_font = pygame.font.Font(KOREAN_FONT, 35)
    DIFFICULTY_COLORS = [(80, 200, 80), (240, 220, 60), (220, 70, 70)]
    DIFF_BTN_RECT = pygame.Rect(0, 0, 210, 60)
    DIFF_BTN_RECT.center = (size[0] // 2, difficulty_ui_y)
    LEFT_BTN = pygame.Rect(DIFF_BTN_RECT.left - 55, DIFF_BTN_RECT.centery - 22, 40, 44)
    RIGHT_BTN = pygame.Rect(DIFF_BTN_RECT.right + 15, DIFF_BTN_RECT.centery - 22, 40, 44)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    game_mode = "single"
                    return
                elif event.key == pygame.K_a:
                    game_mode = "ai"
                    return
                elif event.key == pygame.K_LEFT:
                    difficulty = (difficulty - 1) % len(DIFFICULTY_LEVELS)
                elif event.key == pygame.K_RIGHT:
                    difficulty = (difficulty + 1) % len(DIFFICULTY_LEVELS)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if btn1_rect.collidepoint(mx, my):
                    game_mode = "single"
                    return
                if btn2_rect.collidepoint(mx, my):
                    game_mode = "ai"
                    return
                if LEFT_BTN.collidepoint(mx, my):
                    difficulty = (difficulty - 1) % len(DIFFICULTY_LEVELS)
                if RIGHT_BTN.collidepoint(mx, my):
                    difficulty = (difficulty + 1) % len(DIFFICULTY_LEVELS)

        # --- 각 뱀 자연스럽게 이동 ---
        for snake in snakes:
            snake['move_cooldown'] += 1
            if snake['move_cooldown'] > 2:
                snake['move_cooldown'] = 0
                head = snake['body'][0][:]
                dir = snake['direction']
                x, y = head
                if snake['straight_count'] > 0:
                    snake['straight_count'] -= 1
                else:
                    possible_dirs = []
                    if y > SAFE_MARGIN: possible_dirs.append('UP')
                    if y < size[1] - SAFE_MARGIN - 10: possible_dirs.append('DOWN')
                    if x > SAFE_MARGIN: possible_dirs.append('LEFT')
                    if x < size[0] - SAFE_MARGIN - 10: possible_dirs.append('RIGHT')
                    if dir in possible_dirs and random.random() < 0.75:
                        new_dir = dir
                    else:
                        new_dir = random.choice(possible_dirs)
                    snake['direction'] = new_dir
                    snake['straight_count'] = random.randint(10, 30)
                dir = snake['direction']
                if dir == 'UP':
                    head[1] -= 10
                elif dir == 'DOWN':
                    head[1] += 10
                elif dir == 'LEFT':
                    head[0] -= 10
                elif dir == 'RIGHT':
                    head[0] += 10
                snake['body'].insert(0, head)
                snake['body'].pop()

        # --- 화면 그리기 ---
        draw_gradient_background(window, grad_top, grad_bottom)
        window.blit(background_img, (0, 0))
        # title_surface = title_font.render('Snake', True, (255, 255, 255))
        title_surface = title_font.render('Snake', True, (78, 165, 247))
        title_rect = title_surface.get_rect(center=(size[0] // 2, 90))
        window.blit(title_surface, title_rect)

        # 최고 점수 표시
        hs_font = pygame.font.Font(DEFAULT_FONT, 28)
        hs_surface = hs_font.render(f'High Score : {high_score}', True, (255, 220, 80))
        hs_rect = hs_surface.get_rect(center=(size[0] // 2, 135))
        window.blit(hs_surface, hs_rect)

        # 버튼 먼저
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_on_btn1 = btn1_rect.collidepoint(mouse_x, mouse_y)
        mouse_on_btn2 = btn2_rect.collidepoint(mouse_x, mouse_y)

        btn1_color = (120, 80, 255) if mouse_on_btn1 else (80, 60, 200)
        btn2_color = (80, 220, 120) if mouse_on_btn2 else (50, 140, 80)

        pygame.draw.rect(window, btn1_color, btn1_rect, border_radius=18)
        pygame.draw.rect(window, (255,255,255,40), btn1_rect, 4, border_radius=18)
        btn1_txt_color = (255, 255, 255) if mouse_on_btn1 else (220, 220, 255)
        btn1_surface = btn_font.render('Single', True, btn1_txt_color)
        btn1_rect_txt = btn1_surface.get_rect(center=btn1_rect.center)
        window.blit(btn1_surface, btn1_rect_txt)

        pygame.draw.rect(window, btn2_color, btn2_rect, border_radius=18)
        pygame.draw.rect(window, (255,255,255,40), btn2_rect, 4, border_radius=18)
        btn2_txt_color = (255, 255, 255) if mouse_on_btn2 else (220, 255, 220)
        btn2_surface = btn_font.render('AI Match', True, btn2_txt_color)
        btn2_rect_txt = btn2_surface.get_rect(center=btn2_rect.center)
        window.blit(btn2_surface, btn2_rect_txt)

        # 난이도 버튼
        pygame.draw.rect(window, (80, 80, 80), DIFF_BTN_RECT, border_radius=16)
        pygame.draw.rect(window, DIFFICULTY_COLORS[difficulty], DIFF_BTN_RECT, 4, border_radius=16)
        diff_txt = DIFFICULTY_LEVELS[difficulty]
        surf = diff_font.render(f"{diff_txt}", True, DIFFICULTY_COLORS[difficulty])
        rect = surf.get_rect(center=DIFF_BTN_RECT.center)
        window.blit(surf, rect)

        # 좌우 버튼
        pygame.draw.polygon(window, (220,220,255), [
            (LEFT_BTN.right, LEFT_BTN.top), (LEFT_BTN.left, LEFT_BTN.centery), (LEFT_BTN.right, LEFT_BTN.bottom)
        ])
        pygame.draw.polygon(window, (220,220,255), [
            (RIGHT_BTN.left, RIGHT_BTN.top), (RIGHT_BTN.right, RIGHT_BTN.centery), (RIGHT_BTN.left, RIGHT_BTN.bottom)
        ])
        # 난이도 설명
        food_num = FOOD_COUNT_BY_DIFFICULTY[difficulty]
        obs_num = OBSTACLE_COUNT_BY_DIFFICULTY[difficulty]
        info_txt = f"화면에 음식 {food_num}개, 장애물 {obs_num}개, 속도 {FPS_BY_DIFFICULTY[difficulty]}"
        # info_surf = info_font.render(info_txt, True, (240,240,255))
        info_surf = info_font.render(info_txt, True, (36, 36, 36))
        info_rect = info_surf.get_rect(center=(size[0]//2, DIFF_BTN_RECT.bottom + 25))
        window.blit(info_surf, info_rect)

        # 뱀을 제일 위에!
        for snake in snakes:
            for pos in snake['body']:
                pygame.draw.rect(window, snake['color'], pygame.Rect(pos[0], pos[1], 10, 10))

        # 크레딧 + 버전 정보
        credit_font = pygame.font.SysFont("Segoe UI", 15)
        credit_text = f"Made by {', '.join(DEVELOPERS)}  |  v{VERSION}"
        credit_surface = credit_font.render(credit_text, True, (220, 220, 220))
        credit_rect = credit_surface.get_rect()
        credit_rect.bottomright = (size[0] - 12, size[1] - 8)
        window.blit(credit_surface, credit_rect)

        pygame.display.flip()
        fps_controller.tick(65)


def game_over(window, size):
    global high_score, score
    if score > high_score:
        high_score = score
        save_high_score(high_score)

    my_font = pygame.font.Font(DEFAULT_FONT, 90)
    game_over_surface = my_font.render('Game Over', True, red)
    game_over_rect = game_over_surface.get_rect()
    game_over_rect.midtop = (size[0] / 2, size[1] / 4)
    window.fill(black)
    window.blit(game_over_surface, game_over_rect)
    show_score(window, size, 0, green, DEFAULT_FONT, 20)
    
    # 최고 점수 표시
    hs_font = pygame.font.Font(DEFAULT_FONT, 32)
    hs_surface = hs_font.render(f'High Score : {high_score}', True, (255, 220, 80))
    hs_rect = hs_surface.get_rect(center=(size[0] // 2, size[1] // 2 + 40))
    window.blit(hs_surface, hs_rect)

    pygame.display.flip()
    time.sleep(1)
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    waiting = False
        pygame.time.wait(20)
        
def show_ai_game_over(window, size, result, player_score, ai_score):
    my_font = pygame.font.Font(DEFAULT_FONT, 80)
    game_over_surface = my_font.render(result, True, (255, 220, 0) if result=="You Win" else red)
    game_over_rect = game_over_surface.get_rect()
    game_over_rect.midtop = (size[0] / 2, size[1] / 4)
    window.fill(black)
    window.blit(game_over_surface, game_over_rect)
    show_score(window, size, 0, green, DEFAULT_FONT, 28, ai_score=ai_score)
    pygame.display.flip()

    time.sleep(1)
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    waiting = False
        pygame.time.wait(20)

if __name__ == "__main__":
    initialize()
    high_score = load_high_score()
    main_window = Init(frame)

    star_img = pygame.image.load(STAR_IMG_PATH)
    star_img = pygame.transform.scale(star_img, (16, 16))

    apple_img = pygame.image.load(APPLE_PATH)
    apple_img = pygame.transform.scale(apple_img, (16, 16))

    # --- [추가] 배경 이미지 로드 ---
    background_img = pygame.image.load(BACKGROUND_IMG_PATH)
    background_img = pygame.transform.scale(background_img, frame)

    pygame.mixer.init()
    pygame.mixer.music.load(BGM_PATH)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)

    while True:
        show_lobby(main_window, frame, background_img)   # background_img 인자로 전달
        if game_mode == "single":
            reset_game()
            show_game()
        elif game_mode == "ai":
            reset_ai_game()
            show_ai_match()