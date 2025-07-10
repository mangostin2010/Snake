# ========== 필요한 라이브러리 임포트 ==========
import os
import random
import time
import sys
import requests
import pygame
import json

# ========== 개발자 & 버전 선언 (로비에서 사용됩니다) ==========

DEVELOPERS = [
    "Sam", 
    "Samuel", 
    "Ryan", 
    "Alice", 
    "Justin"
]
VERSION = '1.0.3'

# ========== 리소스 폴더 및 경로 선언 ==========
REQUIRED_RESOURCES_URL = "https://github.com/mangostin2010/Snake/raw/main/snake_resources.json"

RESOURCE_DIR = "snake_resources"
DEFAULT_FONT = os.path.join(RESOURCE_DIR, "Merriweather.ttf")
KOREAN_FONT = os.path.join(RESOURCE_DIR, 'ChironSungHK.ttf')

# IMAGES
BOLT_IMG_PATH = os.path.join(RESOURCE_DIR, "bolt.png")
STAR_IMG_PATH = os.path.join(RESOURCE_DIR, "star.png")

APPLE_PATH = os.path.join(RESOURCE_DIR, "apple.png")
BACKGROUND_IMG_PATH = os.path.join(RESOURCE_DIR, "background.png")
TROPY_IMG_PATH = os.path.join(RESOURCE_DIR, "tropy.png")
BACKGROUND2_IMG_PATH = os.path.join(RESOURCE_DIR, "background2.png")
GAME_OVER_PATH = os.path.join(RESOURCE_DIR, "gameover.png")

# SOUND EFFECT
BGM_PATH = os.path.join(RESOURCE_DIR, "bgm.mp3")
BGM2_PATH = os.path.join(RESOURCE_DIR, "bgm2.mp3")

APPLE_SOUNDEFFECT = os.path.join(RESOURCE_DIR, "apple.mp3")
BOLT_SOUNDEFFECT = os.path.join(RESOURCE_DIR, "bolt.mp3")
STAR_SOUNDEFFECT = os.path.join(RESOURCE_DIR, "star.mp3")
GAME_FINISH_SOUNDEFFECT = os.path.join(RESOURCE_DIR, "game_finish.mp3")

# ========== 필요한 리소스 다운로드 하는 부분 ==========
'''
아래 부분은 필요한 리소스를 인터넷에서 다운로드 하기 때문에
Github Repository 안에서 리소스를 이제 관리하므로 필요 없음.

하지만 snake.py(현재 이 파일)만 복사해서 실행한다면 필요할 것임.
'''

def download_file(url, save_path):
    if os.path.exists(save_path) and "snake_resources.json" not in url:
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

        if "updater" in save_path:
            os.startfile(r'.\snake_resources\updater.exe')
        return True
    except Exception as e:
        print(f"Failed to download {save_path}: {e}")
        return False

def get_required_resources():
    if not os.path.exists(RESOURCE_DIR):
        os.makedirs(RESOURCE_DIR)
    resources = download_file(REQUIRED_RESOURCES_URL, 'snake_resources.json')

    with open("snake_resources.json", encoding="UTF-8") as fp:
        resources = json.load(fp)

    for res in resources:
        success = download_file(res['url'], os.path.join(RESOURCE_DIR, res['save_file_name']))
        if not success:
            print(f"Warning: {res['save_file_name']} could not be downloaded.")

# ========== 게임 코드 시작 ==========
"""
Justin:
변수들 선언하는 것은 문제될 것이 없지만 지금 불필요하다고 생각되는 것은 이미지를 불러오는 것임.
어디서는 아래와 같이 (star_img = None) 그냥 먼저 None type으로 선언하지만
어떤 이미지는 함수 안에서 따로 불러와짐.
마지막으로는 이미지들이 if __name__ == "__main__" 여기서도 따로 불러지는 것이 문제임.
이미지를 모두 한꺼번에 불러오는 함수를 만들거나, 함수 안에서 필요할때만 불러오는 통일성이 필요함.
"""

# 기본 변수들
fps = 30  # 게임 속도
frame = (1024, 576)
frame = (1280, 720)
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
# last_ai_score, last_player_score, last_result들은 사실 필요는 없는 듯? 현재 로비 UI전에 필요했었지만 지금은 사용되지 않고 있음.

# --- 별(무적) 아이템 관련 ---
star_img = None
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

bg_imgs = [
    f"{RESOURCE_DIR},background2.png"
]
go_imgs = [
    f"{RESOURCE_DIR},gameover.png"
]
is_fullscreen = False
bgm_volume = 0.5
sfx_volume = 0.5

# 방패 관련
SHIELD_RESPAWN_INTERVAL = 350  # 프레임 단위. 원하는 대로 조정 ㄱㄴ
shield_pos = [0, 0]
shield_spawn = False
shield_timer = 0
has_shield = False

API_URL = "https://snakeranking.pythonanywhere.com"
USER_DATA_PATH = os.path.join(RESOURCE_DIR, "user_data.json")

# =============== 필요한 함수 정의 ===============

def load_resources():
    global star_img, apple_img, background_img, tropy_img, item_img, background_img, background2_img, game_over_img
    global default_font, korean_font
    global APPLE_SOUND, BOLT_SOUND, STAR_SOUND, GAME_FINISH_SOUND

    # ===== 이미지 =====
    star_img = pygame.image.load(STAR_IMG_PATH)
    star_img = pygame.transform.scale(star_img, (16, 16))

    apple_img = pygame.image.load(APPLE_PATH)
    apple_img = pygame.transform.scale(apple_img, (12, 12))

    background_img = pygame.image.load(BACKGROUND_IMG_PATH)
    background_img = pygame.transform.scale(background_img, frame)

    background2_img = pygame.image.load(BACKGROUND2_IMG_PATH)
    background2_img = pygame.transform.scale(background2_img, frame)

    tropy_img = pygame.image.load(TROPY_IMG_PATH)
    tropy_img = pygame.transform.smoothscale(tropy_img, (38, 38))

    item_img = pygame.image.load(BOLT_IMG_PATH)
    item_img = pygame.transform.scale(item_img, (15, 15))

    background_img = pygame.image.load(BACKGROUND_IMG_PATH)
    background_img = pygame.transform.scale(background_img, frame)

    game_over_img = pygame.image.load(GAME_OVER_PATH)
    game_over_img = pygame.transform.scale(game_over_img, frame)

    # ===== 폰트(경로만 저장, 실제 객체는 사용할 때 크기별로 생성 권장) =====
    default_font = DEFAULT_FONT
    korean_font = KOREAN_FONT

    # ===== 사운드(효과음) =====
    APPLE_SOUND = pygame.mixer.Sound(APPLE_SOUNDEFFECT)
    BOLT_SOUND = pygame.mixer.Sound(BOLT_SOUNDEFFECT)
    STAR_SOUND = pygame.mixer.Sound(STAR_SOUNDEFFECT)
    GAME_FINISH_SOUND = pygame.mixer.Sound(GAME_FINISH_SOUNDEFFECT)

    STAR_SOUND.set_volume(0.4)
    GAME_FINISH_SOUND.set_volume(0.4)

def Init(size):
    check_errors = pygame.init()
    pygame.mixer.init()

    # 리소스 통합 로드
    load_resources()

    if check_errors[1] > 0:
        print(f'[!] Had {check_errors[1]} errors when initialising game, exiting...')
        sys.exit(-1)
    else:
        print('[+] Game successfully initialised')

    pygame.display.set_caption('Snake')
    game_window = pygame.display.set_mode(size)
    return game_window

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
    global shield_pos, shield_spawn, shield_timer, has_shield
    global health, max_health, health_decrease_timer

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

    # 방패
    shield_pos = get_random_pos(snake_body + food_pos_list + obstacles)
    shield_spawn = False
    shield_timer = 0
    has_shield = False

    # HP바
    health = 100
    max_health = 100
    health_decrease_timer = 0

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

def draw_health_bar(surface, x, y, health, max_health, width=200, height=18):
    # 배경
    pygame.draw.rect(surface, (80, 80, 80), (x, y, width, height), border_radius=8)
    # 체력
    ratio = max(0, health) / max_health
    if ratio > 0.5:
        color = (60, 220, 80)
    elif ratio > 0.2:
        color = (240, 200, 50)
    else:
        color = (230, 60, 40)
    pygame.draw.rect(surface, color, (x, y, int(width * ratio), height), border_radius=8)
    # 테두리
    pygame.draw.rect(surface, (240, 240, 240), (x, y, width, height), 2, border_radius=8)

def reset_ai_game():
    """AI 모드용: 플레이어·AI 뱀 동시에 초기화"""
    global snake_pos, snake_body, direction, score
    global ai_snake_pos, ai_snake_body, ai_direction, ai_score
    global food_pos, food_spawn, fps, item_pos, item_spawn, item_timer
    global ai_has_shield, shield_pos, shield_timer, shield_spawn, food_pos_list
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
    # 방패
    shield_pos = get_random_pos(snake_body + ai_snake_body + [food_pos])
    shield_spawn = False
    shield_timer = 0
    ai_has_shield = False

def reset_ai_game():
    """AI 모드용: 플레이어·AI 뱀 동시에 초기화"""
    global snake_pos, snake_body, direction, score
    global ai_snake_pos, ai_snake_body, ai_direction, ai_score
    global food_pos, food_spawn, fps, item_pos, item_spawn, item_timer
    global ai_has_shield, shield_pos, shield_timer, shield_spawn, food_pos_list
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
    # 방패
    shield_pos = get_random_pos(snake_body + ai_snake_body + [food_pos])
    shield_spawn = False
    shield_timer = 0
    ai_has_shield = False

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

def show_settings(window, size):
    global is_fullscreen, bgm_volume, sfx_volume
    running = True

    # 버튼들의 위치 및 크기 정의
    margin_x = size[0] // 2 - 220
    cur_y = 170
    row_h = 76
    btn_w = 84
    btn_h = 52

    # 볼륨 조정용
    bgm_minus = pygame.Rect(margin_x, cur_y, btn_w, btn_h)
    bgm_plus  = pygame.Rect(margin_x + 280, cur_y, btn_w, btn_h)
    sfx_minus = pygame.Rect(margin_x, cur_y + row_h, btn_w, btn_h)
    sfx_plus  = pygame.Rect(margin_x + 280, cur_y + row_h, btn_w, btn_h)
    # 전체화면 토글 버튼
    fullscreen_btn = pygame.Rect(margin_x, cur_y + 2 * row_h, 170, btn_h)
    # 닫기 버튼
    close_btn = pygame.Rect(size[0]//2 - 70, cur_y + 3 * row_h + 15, 140, 50)

    font_big = pygame.font.Font(KOREAN_FONT, 44)
    font = pygame.font.Font(KOREAN_FONT, 28)
    small = pygame.font.Font(KOREAN_FONT, 20)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # 배경음 -/+
                if bgm_minus.collidepoint(mx, my):
                    bgm_volume = max(0, bgm_volume - 0.05)
                    pygame.mixer.music.set_volume(bgm_volume)
                if bgm_plus.collidepoint(mx, my):
                    bgm_volume = min(1, bgm_volume + 0.05)
                    pygame.mixer.music.set_volume(bgm_volume)
                # 효과음 -/+
                if sfx_minus.collidepoint(mx, my):
                    sfx_volume = max(0, sfx_volume - 0.05)
                    update_sfx_volume()
                if sfx_plus.collidepoint(mx, my):
                    sfx_volume = min(1, sfx_volume + 0.05)
                    update_sfx_volume()
                # 전체화면 ON/OFF
                if fullscreen_btn.collidepoint(mx, my):
                    is_fullscreen = not is_fullscreen
                    toggle_fullscreen(window)
                # 닫기
                if close_btn.collidepoint(mx, my):
                    running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # ---- 그리기 ----
        window.fill((42, 46, 68))
        t = font_big.render("Settings", True, (255, 255, 95))
        window.blit(t, (size[0]//2 - t.get_width()//2, 70))

        # 배경음 볼륨
        pygame.draw.rect(window, (210,210,255), bgm_minus, border_radius=14)
        pygame.draw.rect(window, (230,230,255), bgm_plus, border_radius=14)
        pygame.draw.polygon(window, (20,80,180), [
            (bgm_minus.centerx+14, bgm_minus.bottom-14), (bgm_minus.centerx-14, bgm_minus.centery), (bgm_minus.centerx+14, bgm_minus.top+14)
        ])
        pygame.draw.polygon(window, (20,80,180), [
            (bgm_plus.centerx-14, bgm_plus.top+14), (bgm_plus.centerx+14, bgm_plus.centery), (bgm_plus.centerx-14, bgm_plus.bottom-14)
        ])
        txt = font.render(f"BGM", True, (250, 235, 130))
        window.blit(txt, (margin_x + 110, cur_y+12))
        perc = font.render(f"{int(bgm_volume*100)}%", True, (255,255,255))
        window.blit(perc, (margin_x + 218, cur_y+12))

        # 효과음 볼륨
        pygame.draw.rect(window, (220,220,255), sfx_minus, border_radius=14)
        pygame.draw.rect(window, (240,240,255), sfx_plus, border_radius=14)
        pygame.draw.polygon(window, (30,140,120), [
            (sfx_minus.centerx+14, sfx_minus.bottom-14), (sfx_minus.centerx-14, sfx_minus.centery), (sfx_minus.centerx+14, sfx_minus.top+14)
        ])
        pygame.draw.polygon(window, (30,140,120), [
            (sfx_plus.centerx-14, sfx_plus.top+14), (sfx_plus.centerx+14, sfx_plus.centery), (sfx_plus.centerx-14, sfx_plus.bottom-14)
        ])
        txt = font.render(f"SFX", True, (150,235,250))
        window.blit(txt, (margin_x + 110, cur_y+row_h+12))
        perc = font.render(f"{int(sfx_volume*100)}%", True, (255,255,255))
        window.blit(perc, (margin_x + 218, cur_y+row_h+12))

        # 전체화면 토글
        pygame.draw.rect(window, (188,160,255) if is_fullscreen else (85,68,140), fullscreen_btn, border_radius=16)
        fs_txt = "전체화면 ON" if is_fullscreen else "전체화면 OFF"
        fs_color = (60,15,60) if is_fullscreen else (220,220,255)
        ftxt = font.render(fs_txt, True, fs_color)
        window.blit(ftxt, (fullscreen_btn.centerx - ftxt.get_width()//2, fullscreen_btn.centery-ftxt.get_height()//2+2))

        # 닫기 버튼
        pygame.draw.rect(window, (230,100,90), close_btn, border_radius=18)
        ctxt = font.render("CLOSE", True, (255,255,255))
        window.blit(ctxt, (close_btn.centerx - ctxt.get_width()//2, close_btn.centery - ctxt.get_height()//2 + 4))

        notice = small.render("조작: 버튼 클릭 또는 ESC", True, (210,210,255))
        window.blit(notice, (size[0]//2 - notice.get_width()//2, size[1]-45))

        pygame.display.flip()
        fps_controller.tick(30) #추가 함수 (효과음 반영):

def update_sfx_volume():
    APPLE_SOUND.set_volume(sfx_volume)
    BOLT_SOUND.set_volume(sfx_volume)
    STAR_SOUND.set_volume(sfx_volume)
    GAME_FINISH_SOUND.set_volume(sfx_volume)

def toggle_fullscreen(window):
    global main_window, frame
    if is_fullscreen:
        main_window = pygame.display.set_mode(frame, pygame.FULLSCREEN)
    else:
        main_window = pygame.display.set_mode(frame)

def update_sfx_volume():
    # 효과음 볼륨 전체 반영
    APPLE_SOUND.set_volume(sfx_volume)
    BOLT_SOUND.set_volume(sfx_volume)
    STAR_SOUND.set_volume(sfx_volume)
    GAME_FINISH_SOUND.set_volume(sfx_volume)

def toggle_fullscreen(current_window):
    global main_window, frame
    if is_fullscreen:
        main_window = pygame.display.set_mode(frame, pygame.FULLSCREEN)
    else:
        main_window = pygame.display.set_mode(frame)    

def show_game():
    global snake_pos, snake_body, direction, score, fps, main_window
    global item_pos, item_spawn, item_timer
    global star_img, star_pos, star_spawn, star_timer
    global invincible, invincible_timer, normal_fps
    global food_pos_list, food_spawn_list, obstacles
    global item_img
    global shield_pos, shield_spawn, shield_timer, has_shield
    global health, max_health, health_decrease_timer

    ITEM_RESPAWN_INTERVAL = 150

    last_time = time.time()

    while True:
        now = time.time()
        dt = now - last_time
        last_time = now

        health_decrease_timer += dt
        if health_decrease_timer >= 2.0:   
            health -= 10                   
            health_decrease_timer = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.USEREVENT + 1:
                pygame.mixer.music.set_volume(bgm_volume)  # BGM 볼륨 원래대로
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)  # 타이머 해제
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
                health = min(health + 20, max_health)
                if score % 3 == 0 and not invincible:
                    fps += 5
                    normal_fps = fps
                food_spawn_list[i] = False
                ate_food = True
                APPLE_SOUND.play()
        if not ate_food:
            snake_body.pop()
        if health <= 0:
            game_over(main_window, frame)
            return
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
            BOLT_SOUND.play()

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

        if not shield_spawn:
            shield_timer += 1
            if shield_timer >= SHIELD_RESPAWN_INTERVAL:
                used = snake_body + food_pos_list + obstacles + ([item_pos] if item_spawn else []) + ([star_pos] if star_spawn else [])
                shield_pos = get_random_pos(used)
                shield_spawn = True
                shield_timer = 0

        if shield_spawn and snake_pos == shield_pos:
            has_shield = True
            shield_spawn = False
            shield_timer = 0

        snake_rect = pygame.Rect(snake_pos[0], snake_pos[1], 10, 10)
        star_rect = pygame.Rect(star_pos[0], star_pos[1], 16, 16)
        if star_spawn and snake_rect.colliderect(star_rect):
            invincible = True
            invincible_timer = INVINCIBLE_DURATION
            star_spawn = False
            star_timer = 0
            fps = normal_fps + INVINCIBLE_FPS_BOOST

            pygame.mixer.music.set_volume(bgm_volume * 0.15)  # BGM 볼륨 줄이기
            STAR_SOUND.stop()
            STAR_SOUND.play()

            # 5초 후에 볼륨 복구 예약
            pygame.time.set_timer(pygame.USEREVENT + 1, 5000)

        # --- 무적 상태 관리 ---
        if invincible:
            invincible_timer -= dt
            if invincible_timer <= 0:
                invincible = False
                fps = normal_fps

        # --- 그리기 ---
        main_window.blit(background2_img, (0, 0))
        for i, pos in enumerate(snake_body):
            if invincible:
                color = (255, 255, 80) if (int(time.time()*8)%2==0 or i==0) else (255, 200, 60)
            elif has_shield:
                color = (80, 170, 250) if (int(time.time()*8)%2==0 or i==0) else (50, 110, 200)
            else:
                color = green
            pygame.draw.rect(main_window, color, pygame.Rect(pos[0], pos[1], 10, 10))

            bar_width = 200
            bar_height = 18
            margin_x = 20      # 화면 오른쪽 끝에서부터의 마진
            margin_y = 15

            x = frame[0] - bar_width - margin_x
            y = margin_y

            draw_health_bar(main_window, x, y, health, max_health, width=bar_width, height=bar_height)

            font = pygame.font.Font(DEFAULT_FONT, 22)
            htext = font.render(f"HP: {health}", True, (240, 240, 240))
            htext_rect = htext.get_rect()
            htext_rect.centerx = x + bar_width // 2  # bar의 중앙 정렬
            htext_rect.top = y + bar_height + 6      # bar 아래쪽에 6픽셀 띄움

            main_window.blit(htext, htext_rect)

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
        if shield_spawn:
            pygame.draw.rect(main_window, (80, 170, 250), pygame.Rect(shield_pos[0], shield_pos[1], 12, 12))
            pygame.draw.rect(main_window, (40, 110, 220), pygame.Rect(shield_pos[0]+3, shield_pos[1]+3, 6, 6))

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
            elif has_shield:
                snake_pos[:] = [100, 50]
                snake_body[:] = [list(snake_pos), [90, 50], [80, 50]]
                direction = 'RIGHT'
                has_shield = False
            else:
                game_over(main_window, frame)
                return

        for block in snake_body[1:]:
            if snake_pos == block:
                game_over(main_window, frame)
                return

        # --- 장애물 충돌 ---
        if snake_pos in obstacles:
            if invincible:
                pass # 무적이면 통과 ㅆㄱㄴ
            elif has_shield:
                snake_pos[:] = [100, 50]
                snake_body[:] = [list(snake_pos), [90, 50], [80, 50]]
                direction = 'RIGHT'
                has_shield = False
            else:
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
    """
    Justin: 현재 이 함수(AI와 대결하는)에 버그가 있다고 들음.
    한서가 말해줬는데 다음과 같은 버그들이 있음. 앞으로 고쳐야 함.
        1. AI가 별을 먹은 상태에서 플레이어가 죽고 다음 판을 시작했을때 AI가 무적 상태임.
        2. 플레이어가 번개를 먹은 상태에서 죽고 다음 판에 별을 먹었을시 전판에 속도가 그대로 적용됨. 
            - 확인해보진 못했지만 아마 fps가 초기화되지 않아서 일 것임.
        3. 플레이어 혹은 AI가 별을 먹을시 fps가 모두 동일하게 적용됨.
            - 이거는 그냥 냅둬도 될 듯 하다ㅋㅋ.. 별을 먹지 못한 상대의 잘못?
    """
    global snake_pos, snake_body, direction, score
    global ai_snake_pos, ai_snake_body, ai_direction, ai_score
    global food_pos, food_spawn, fps, main_window
    global item_pos, item_spawn, item_timer
    global last_ai_score, last_player_score, last_result
    global star_img, star_pos, star_spawn, star_timer
    global invincible, invincible_timer, ai_invincible, ai_invincible_timer, normal_fps
    global item_img
    global shield_pos, shield_spawn, shield_timer, has_shield
    global health, max_health, health_decrease_timer, ai_has_shield, ai_color

    ITEM_RESPAWN_INTERVAL = 150

    reset_game()

    last_time = time.time()
    while True:
        now = time.time()
        dt = now - last_time
        last_time = now

        health_decrease_timer += dt

        if health_decrease_timer >= 2.0:   
            health -= 10                   
            health_decrease_timer = 0

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
            health = min(health + 20, max_health)
            food_spawn = False
            APPLE_SOUND.play()
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
            BOLT_SOUND.play()

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

            pygame.mixer.music.set_volume(bgm_volume * 0.15)  # BGM 볼륨 줄이기
            STAR_SOUND.stop()
            STAR_SOUND.play()

            # 5초 후에 볼륨 복구 예약
            pygame.time.set_timer(pygame.USEREVENT + 1, 5000)

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

        # --- 방패 아이템 관리 ---
        if not shield_spawn:
            shield_timer += 1
            if shield_timer >= SHIELD_RESPAWN_INTERVAL:
                used = snake_body + food_pos_list + obstacles + ([item_pos] if item_spawn else []) + ([star_pos] if star_spawn else [])
                shield_pos = get_random_pos(used)
                shield_spawn = True
                shield_timer = 0

        # 플레이어가 방패 먹음
        if shield_spawn and snake_pos == shield_pos:
            has_shield = True
            shield_spawn = False
            shield_timer = 0

        # AI가 방패 먹음
        if shield_spawn and ai_snake_pos == shield_pos:
            ai_has_shield = True
            shield_spawn = False
            shield_timer = 0


        # --- 그리기 ---
        main_window.blit(background2_img, (0, 0))
        if shield_spawn:
            pygame.draw.rect(main_window, (80, 170, 250), pygame.Rect(shield_pos[0], shield_pos[1], 12, 12))
            pygame.draw.rect(main_window, (40, 110, 220), pygame.Rect(shield_pos[0]+3, shield_pos[1]+3, 6, 6))


        bar_width = 200
        bar_height = 18
        margin_x = 20      # 화면 오른쪽 끝에서부터의 마진
        margin_y = 15

        x = frame[0] - bar_width - margin_x
        y = margin_y

        draw_health_bar(main_window, x, y, health, max_health, width=bar_width, height=bar_height)

        font = pygame.font.Font(DEFAULT_FONT, 22)
        htext = font.render(f"HP: {health}", True, (240, 240, 240))
        htext_rect = htext.get_rect()
        htext_rect.centerx = x + bar_width // 2  # bar의 중앙 정렬
        htext_rect.top = y + bar_height + 6      # bar 아래쪽에 6픽셀 띄움

        main_window.blit(htext, htext_rect)
        # 플레이어 뱀
        for i, pos in enumerate(snake_body):
            if invincible:
                color = (255, 255, 80) if (int(time.time()*8)%2==0 or i==0) else (255, 200, 60)
            elif has_shield:
                color = (80, 170, 250) if (int(time.time()*8)%2==0 or i==0) else (50, 110, 200)
            else:
                color = green
            pygame.draw.rect(main_window, color, pygame.Rect(pos[0], pos[1], 10, 10))
        # AI 뱀
        for i, pos in enumerate(ai_snake_body):
            if ai_invincible:
                color = (255, 255, 80) if (int(time.time()*8)%2==0 or i==0) else (255, 180, 120)
            elif ai_has_shield:
                color = (80, 170, 250) if (int(time.time()*8)%2==0 or i==0) else (50, 110, 200)
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
            elif has_shield:
                snake_pos[:] = [100, 50]
                snake_body[:] = [list(snake_pos), [90, 50], [80, 50]]
                direction = 'RIGHT'
                has_shield = False
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
            elif ai_has_shield:
                ai_snake_pos[:] = [100, 50]
                ai_snake_body[:] = [list(snake_pos), [90, 50], [80, 50]]
                ai_direction = 'RIGHT'
                ai_has_shield = False
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

    button_width, button_height = 240, 80
    button_gap = 30
    btn1_rect = pygame.Rect((size[0] - button_width) // 2, 160, button_width, button_height)
    btn2_rect = pygame.Rect((size[0] - button_width) // 2, 230 + button_gap, button_width, button_height)
    setting_btn_rect = pygame.Rect(size[0]-170, 28, 140, 52)
    setting_font = pygame.font.Font(KOREAN_FONT, 27)

    BUTTONS_TO_DIFFICULTY_GAP = 45
    difficulty_ui_y = btn2_rect.bottom + BUTTONS_TO_DIFFICULTY_GAP

    title_font = pygame.font.Font(DEFAULT_FONT, 60) # +20 (font: pixelpurl 일때)
    btn_font = pygame.font.Font(DEFAULT_FONT, 38) # +15 (font: pixelpurl 일때)
    diff_font = pygame.font.Font(KOREAN_FONT, 35)
    info_font = pygame.font.Font(KOREAN_FONT, 19)

    grad_top = (36, 198, 220)
    grad_bottom = (81, 74, 157)

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
                elif event.key in (pygame.K_s, pygame.K_F1):
                    show_settings(window, size)
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
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if setting_btn_rect.collidepoint(mx, my):
                        show_settings(window, size)

        # --- 화면 그리기 ---
        draw_gradient_background(window, grad_top, grad_bottom)
        window.blit(background_img, (0, 0))

        title_surface = title_font.render('Snake', True, (78, 165, 247))
        title_rect = title_surface.get_rect(center=(size[0] // 2, 90))
        window.blit(title_surface, title_rect)

        pygame.draw.rect(window, (76, 120, 255), setting_btn_rect, border_radius=16)
        btxt = setting_font.render("설정", True, (255,255,255))
        window.blit(btxt,(setting_btn_rect.centerx-btxt.get_width()//2, setting_btn_rect.centery-btxt.get_height()//2))

        # ---- 트로피 + 최고 점수 ----
        tropy_margin = 20
        score_gap = 10
        score_font = pygame.font.Font(DEFAULT_FONT, 28)
        score_surface = score_font.render(str(high_score), True, (255, 220, 80))
        tropy_x = tropy_margin
        tropy_y = size[1] - tropy_img.get_height() - tropy_margin
        score_x = tropy_x + tropy_img.get_width() + score_gap
        score_y = tropy_y + (tropy_img.get_height() - score_surface.get_height()) // 2
        window.blit(tropy_img, (tropy_x, tropy_y))
        window.blit(score_surface, (score_x, score_y))
        # -----------------------------------------

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
        info_surf = info_font.render(info_txt, True, (36, 36, 36))
        info_rect = info_surf.get_rect(center=(size[0]//2, DIFF_BTN_RECT.bottom + 25))
        # window.blit(info_surf, info_rect)

        # 크레딧 + 버전 정보
        credit_font = pygame.font.SysFont("Segoe UI", 15)
        credit_text = f"Made by {', '.join(DEVELOPERS)}  |  v{VERSION}"
        credit_surface = credit_font.render(credit_text, True, (220, 220, 220))
        credit_rect = credit_surface.get_rect()
        credit_rect.bottomright = (size[0] - 12, size[1] - 8)
        window.blit(credit_surface, credit_rect)

        pygame.display.flip()
        fps_controller.tick(65)

def save_username(username):
    with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump({"username": username}, f)

def ask_username(window, size):
    font = pygame.font.Font(KOREAN_FONT, 32)
    input_box = pygame.Rect(size[0]//2 - 100, size[1]//2, 200, 40)
    username = ""
    message = "닉네임 입력 후 Enter"
    active = True
    clock = pygame.time.Clock()
    while active:
        window.fill((50, 50, 80))
        txt_surface = font.render(username, True, (255,255,255))
        pygame.draw.rect(window, (255,255,255), input_box, 2)
        window.blit(txt_surface, (input_box.x+5, input_box.y+5))
        msg_surface = font.render(message, True, (200,220,255))
        window.blit(msg_surface, (size[0]//2 - msg_surface.get_width()//2, input_box.y - 50))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and username.strip():
                    save_username(username.strip())
                    return username.strip()
                elif event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                elif len(username) < 16 and event.unicode.isprintable():
                    username += event.unicode
        clock.tick(30)


def load_username():
    try:
        with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("username", "")
    except Exception:
        return ""

def fetch_top10():
    try:
        r = requests.get(f"{API_URL}/top10", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print("Top10 fetch error:", e)
    return []

def submit_score(username, score):
    try:
        r = requests.post(f"{API_URL}/submit", json={"username": username, "score": score}, timeout=3)
        return r.status_code == 200
    except Exception as e:
        print("Score submit error:", e)
    return False
    
def game_over(window, size):
    global high_score, score, go_imgs, DEFAULT_FONT, red, green, bgm_volume, GAME_FINISH_SOUND, game_over_img
    global username  # 반드시 global로 지정해야 함

    import pygame, sys, time

    if difficulty == 2:
        # 1. 최고 점수 갱신
        if score > high_score:
            high_score = score
            save_high_score(high_score)

        # 2. 닉네임 없으면 받기
        if not username:
            username = ask_username(window, size)
            save_username(username)

        # 3. 무조건 서버에 high_score 전송
        submit_score(username, high_score)

    # 4. 배경 이미지 출력
    if 'game_over_img' in globals():
        window.blit(game_over_img, (0, 0))

    # 5. UI 출력(이전과 동일)
    my_font = pygame.font.Font(DEFAULT_FONT, 90)
    hs_font = pygame.font.Font(DEFAULT_FONT, 32)
    t10_font = pygame.font.Font(DEFAULT_FONT, 24)
    score_font = pygame.font.Font(DEFAULT_FONT, 36)

    text_color = (240, 240, 240)
    hs_color = (255, 220, 80)

    margin = 28
    line_height = t10_font.get_height() + 4

    game_over_surface = my_font.render('Game Over', True, red)
    game_over_rect = game_over_surface.get_rect(center=(size[0] // 2, size[1] // 6))
    window.blit(game_over_surface, game_over_rect)

    score_y = game_over_rect.bottom + margin
    score_surface = score_font.render(f'Score : {score}', True, green)
    score_rect = score_surface.get_rect(center=(size[0] // 2, score_y))
    window.blit(score_surface, score_rect)

    hs_y = score_rect.bottom + margin
    hs_surface = hs_font.render(f'High Score : {high_score}', True, hs_color)
    hs_rect = hs_surface.get_rect(center=(size[0] // 2, hs_y))
    window.blit(hs_surface, hs_rect)

    try:
        top10 = fetch_top10()
    except:
        top10 = []
    t10_title_y = hs_rect.bottom + margin
    t10_title = t10_font.render('=== TOP 10 ===', True, text_color)
    window.blit(t10_title, (size[0] // 2 - t10_title.get_width() // 2, t10_title_y))

    t10_start_y = t10_title_y + t10_title.get_height() + 8
    for i, entry in enumerate(top10):
        line = f"{i+1:2d}. {entry['username'][:12]:12} : {entry['score']}"
        line_surf = t10_font.render(line, True, text_color)
        window.blit(line_surf, (size[0] // 2 - 120, t10_start_y + i * line_height))

    pygame.mixer.music.set_volume(bgm_volume * 0.15)
    GAME_FINISH_SOUND.play()
    pygame.time.set_timer(pygame.USEREVENT + 2, 1000)
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
            elif event.type == pygame.USEREVENT + 2:
                pygame.mixer.music.set_volume(bgm_volume)
                pygame.time.set_timer(pygame.USEREVENT + 2, 0)
        pygame.time.wait(20)

        
def show_ai_game_over(window, size, result, player_score, ai_score):
    my_font = pygame.font.Font(DEFAULT_FONT, 80)
    game_over_surface = my_font.render(result, True, (255, 220, 0) if result=="You Win" else red)
    game_over_rect = game_over_surface.get_rect()
    game_over_rect.midtop = (size[0] / 2, size[1] / 4)
    window.fill(black)
    if 'game_over_img' in globals():
        window.blit(game_over_img, (0, 0))
    window.blit(game_over_surface, game_over_rect)
    show_score(window, size, 0, green, DEFAULT_FONT, 28, ai_score=ai_score)

    # === High Score 표시 추가 ===
    hs_font = pygame.font.Font(DEFAULT_FONT, 32)
    hs_surface = hs_font.render(f'High Score : {high_score}', True, (255, 220, 80))
    hs_rect = hs_surface.get_rect(center=(size[0] // 2, size[1] // 2 + 40))
    window.blit(hs_surface, hs_rect)
    # ============================

    pygame.display.flip()

    # 게임 오버 소리 출력 + BGM 볼륨 줄이기
    pygame.mixer.music.set_volume(bgm_volume * 0.15)
    GAME_FINISH_SOUND.play()
    pygame.time.set_timer(pygame.USEREVENT + 2, 1000)  # 1초 후 복구

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
            elif event.type == pygame.USEREVENT + 2:
                pygame.mixer.music.set_volume(bgm_volume)  # BGM 볼륨 원래대로
                pygame.time.set_timer(pygame.USEREVENT + 2, 0)
        pygame.time.wait(20)

if __name__ == "__main__":
    get_required_resources()
    high_score = load_high_score()
    main_window = Init(frame)
    pygame.mixer.music.load(BGM2_PATH)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)

    # --- 닉네임 먼저 물어보기 ---
    username = load_username()
    if not username:
        username = ask_username(main_window, frame)
        save_username(username)

    while True:
        show_lobby(main_window, frame, background_img)
        if game_mode == "single":
            reset_game()
            show_game()
        elif game_mode == "ai":
            reset_ai_game()
            show_ai_match()
