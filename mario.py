import os
import sys
import pygame as pg
import threading
import random



WIDTH, HEIGHT = 900, 600
FPS = 60
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Colors
BG = (135, 206, 235)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (50, 205, 50)
BROWN = (139, 69, 19)
GOLD = (255, 215, 0)
RED = (220, 20, 60)

Player_base_height = 50  # 基準となるキャラクターの高さ
Enemy_base_height = 60  # 基準となるキャラクターの高さ

# ... (Player クラスの定義はそのまま。画像ロードもそのまま利用) ...
class Player:
    def __init__(self, x, y):
        self.rect = pg.Rect(x, y, 50, Player_base_height) # 当たり判定の初期サイズ
        self.vx = 0.0
        self.vy = 0.0
        self.speed = 5
        self.jump_power = 14
        self.on_ground = False
        self.direction = "right"  # "right" or "left"
        self.power = None  # 現在の能力
        self.facing = 1  # 追加機能3(近藤): 向き（弾発射時に使用）


        def load_and_resize_image(path, Player_base_height):
            """画像を読み込み、アスペクト比を維持してリサイズする"""
            img = pg.image.load(path).convert_alpha()
            orig_w, orig_h = img.get_size()
            aspect_ratio = orig_w / orig_h
            new_width = int(Player_base_height * aspect_ratio)
            return pg.transform.scale(img, (new_width, Player_base_height))


        # 画像の読み込みとリサイズを効率化
        # (画像パス, 高さ) のタプルで指定
        image_paths = {
            'normal': ("img/penguin_right.png", 70),
            'fire':   ("img/power/penguin_honoo.png", 90),
            'ice':    ("img/power/penguin_koori.png", 90),
            'jump':   ("img/power/penguin_usagi.png", 90),
            'speed':  ("img/power/penguin_speed.png", 50),
            'muteki': ("img/power/penguin_muteki.png", 70),
        }
       
        # 能力名と画像のペアを辞書にまとめる
        self.power_images = {
            key: {'right': load_and_resize_image(path, height),
                  'left': pg.transform.flip(load_and_resize_image(path, height), True, False)}
            for key, (path, height) in image_paths.items()
        }
        self.power_images[None] = self.power_images.pop('normal') # 通常状態のキーをNoneに
        self.image = self.power_images[None]['right'] # 初期画像を設定
       

    def handle_input(self, keys):
        self.vx = 0
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            self.vx = -self.speed
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.vx = self.speed
        if self.vx > 0:
            self.direction = "right"
            self.facing = 1
        if self.vx < 0:
            self.direction = "left"
            self.facing = -1
        if (keys[pg.K_SPACE]) and self.on_ground:
            self.vy = -self.jump_power
            self.on_ground = False
       
        # 後で消す: デバッグ用に数字キーで能力変更
        if keys[pg.K_1]:
            self.power = 'fire'
        if keys[pg.K_2]:
            self.power = 'ice'
        if keys[pg.K_3]:
            self.power = 'jump'
        if keys[pg.K_4]:
            self.power = 'speed'
        if keys[pg.K_5]:
            self.power = 'muteki'
        if keys[pg.K_0]:
            self.power = None
       

    def apply_gravity(self):
        self.vy += 0.8  # gravity
        if self.vy > 20:
            self.vy = 20


    def update(self, platforms):
        # horizontal movement
        self.rect.x += int(self.vx)

        # 画面の左端から出ないようにする
        if self.rect.left < 0:
            self.rect.left = 0

        self.collide(self.vx, 0, platforms)
        # vertical movement
        self.apply_gravity()
        self.rect.y += int(self.vy)
        self.on_ground = False
        self.collide(0, self.vy, platforms)

    #
    def collide(self, vx, vy, platforms): #
        for p in platforms:
            if self.rect.colliderect(p):
                if vx > 0:  # moving right
                    self.rect.right = p.left
                if vx < 0:  # moving left
                    self.rect.left = p.right
                if vy > 0:  # falling
                    self.rect.bottom = p.top
                    self.vy = 0
                    self.on_ground = True
                if vy < 0:  # jumping
                    self.rect.top = p.bottom
                    self.vy = 0


    def draw(self, surf):
        # 辞書を使って、現在の能力と向きに応じた画像を効率的に選択
        image_set = self.power_images.get(self.power, self.power_images[None])
        self.image = image_set[self.direction]
        # 画像の足元中央を、当たり判定(rect)の足元中央に合わせる

        draw_rect = self.image.get_rect()
        draw_rect.midbottom = self.rect.midbottom
        surf.blit(self.image, draw_rect)


class Enemy:
    def __init__(self, x, y, w=40, h=40, left_bound=None, right_bound=None):
        # 元画像を2つロードランダムでどちらか選ぶ
        img_sirokuma = pg.image.load("img/sirokuma.png").convert_alpha()
        img_kame = pg.image.load("img/kame.png").convert_alpha()
        img_koura = pg.image.load("img/koura.png").convert_alpha()
        import random
        img_right_orig = random.choice([img_sirokuma, img_kame,img_koura])

        # 元画像の比率を計算し、ペンギンの高さを基準に新しいサイズを算出
        orig_w, orig_h = img_right_orig.get_size()
        size = (int(Enemy_base_height * orig_w / orig_h), Enemy_base_height)

        self.rect = pg.Rect(x,y, size[0], size[1]) # y座標（足元）を基準に配置
        self.vx = -2
        self.left_bound = left_bound
        self.right_bound = right_bound

        self.image_right = pg.transform.scale(img_right_orig, size) # 計算後のサイズでリサイズ
        self.image_left = pg.transform.flip(self.image_right, True, False)
        self.image = self.image_left
       
    def update(self, platforms):
        # 水平移動
        self.rect.x += self.vx

        # 進行方向の足元に地面があるかチェック
        # 崖っぷちで反転するための処理
        ground_check_pos = self.rect.midbottom
        if self.vx > 0: # 右向き
            ground_check_pos = (self.rect.right, self.rect.bottom + 1)
        elif self.vx < 0: # 左向き
            ground_check_pos = (self.rect.left, self.rect.bottom + 1)

        on_ground = any(p.collidepoint(ground_check_pos) for p in platforms)

        # 壁との衝突チェック
        collided_wall = False
        # gole_platformsを渡す必要はないので削除
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vx > 0 and self.rect.right > p.left and self.rect.left < p.left: # 右の壁
                    self.rect.right = p.left
                    collided_wall = True
                elif self.vx < 0 and self.rect.left < p.right and self.rect.right > p.right: # 左の壁
                    self.rect.left = p.right
                    collided_wall = True
        # 崖っぷちまたは壁に衝突したまたは画面外の場合
        if not on_ground or collided_wall or self.rect.left < 0 or self.rect.right > WIDTH:
               
                self.vx *= -1 # 進行方向を反転
                self.image = self.image_right if self.vx > 0 else self.image_left
    
    def draw(self, surf):
        draw_rect = self.image.get_rect()
        draw_rect.midbottom = self.rect.midbottom
        surf.blit(self.image, draw_rect)

class Item:
    def __init__(self, x, y, kind, duration=10, w=40, h=40):
        self.rect = pg.Rect(x, y, w, h) #
        self.kind = kind  # 'fire','ice','jump','suberu','muteki'
        self.duration = duration

        # アイテムの種類に応じた画像を辞書に格納
        self.image_map = {
            'fire': pg.transform.scale(pg.image.load("img/item/honoo-item.png").convert_alpha(), (w, h)),
            'ice': pg.transform.scale(pg.image.load("img/item/koori-item.png").convert_alpha(), (w, h)),
            'jump': pg.transform.scale(pg.image.load("img/item/jamp-item.png").convert_alpha(), (w, h)),
            'speed': pg.transform.scale(pg.image.load("img/item/speedup-item.png").convert_alpha(), (w, h)),
            'muteki': pg.transform.scale(pg.image.load("img/item/muteki-item.png").convert_alpha(), (w, h))
        }
        # 現在のアイテム画像を設定
        self.image = self.image_map.get(self.kind)

    def draw(self, surf):
        surf.blit(self.image, self.rect)

class PowerUpDisplay: #後で消す
    """
    現在のパワーアップ状態を画面右上に表示するクラス
    アイテムを表示するために仮で作ったクラス
    """
    def __init__(self, pos: tuple[int, int], size: tuple[int, int]=(40, 40)):
        self.pos = pos
        self.size = size
        # アイテムの種類に応じた画像を辞書に格納
        self.image_map = {
            'fire': pg.transform.scale(pg.image.load("img/item/honoo-item.png").convert_alpha(), self.size),
            'ice': pg.transform.scale(pg.image.load("img/item/koori-item.png").convert_alpha(), self.size),
            'jump': pg.transform.scale(pg.image.load("img/item/jamp-item.png").convert_alpha(), self.size),
            'speed': pg.transform.scale(pg.image.load("img/item/speedup-item.png").convert_alpha(), self.size),
            'muteki': pg.transform.scale(pg.image.load("img/item/muteki-item.png").convert_alpha(), self.size)
        }

    def draw(self, surf, current_power):
        image = self.image_map.get(current_power)
        if image:
            surf.blit(image, self.pos)

class Projectile:
    def __init__(self, x, y, kind: str, direction: int, speed: float = 5.0):
        self.rect = pg.Rect(int(x), int(y), 10, 10)
        self.kind = kind
        self.vx = speed * (1 if direction >= 0 else -1)

        if self.kind == 'fire':
            self.image = pg.image.load("img/fireball.png").convert_alpha()
        elif self.kind == 'ice':
            self.image = pg.image.load("img/iceball.png").convert_alpha()
        # 画像の元の比率でリサイズ
        orig_w, orig_h = self.image.get_size()
        self.image = pg.transform.scale(self.image, (50, int(50 * orig_h / orig_w)))
        # 左向きに発射される場合のみ画像を反転させる
        if self.vx > 0:
            self.image = pg.transform.flip(self.image, True, False)

    def update(self):
        self.rect.x += int(self.vx)

    def draw(self, surf):
        surf.blit(self.image, self.rect)


# ... (build_level 関数はそのまま利用) ...
def build_level():
    # Simple static level: platforms as Rects
    ground_platforms = []
    floating_platforms = []
    hatena_platforms = []
    hatena_emp_platforms = []
    goal_platforms = []
    ground_y = HEIGHT - 40
    # ground
    ground_platforms = [
        pg.Rect(0, ground_y, 200, 40),
        pg.Rect(250, ground_y, 50, 40),
        pg.Rect(350, ground_y, 50, 40),
        pg.Rect(500, ground_y, 50, 40),
        pg.Rect(600, ground_y, 50, 40),
        pg.Rect(700, ground_y, 200, 40)
    ]
    # some ledges
    # 浮遊ブロックのサイズ指定（x座標, y座標, width, height）
    floating_platforms.append(pg.Rect(100, 450, 200, 20))
    floating_platforms.append(pg.Rect(380, 360, 180, 20))
    floating_platforms.append(pg.Rect(600, 280, 220, 20))
    floating_platforms.append(pg.Rect(250, 520, 120, 20))
    floating_platforms.append(pg.Rect(480, 520, 80, 20))
   
    # はてなブロック
    hatena_platforms.append(pg.Rect(480, 120, 40, 40))

    hatena_emp_platforms.append(pg.Rect(200, 120, 40, 40))
    # ゴール
    goal_platforms.append(pg.Rect(800, HEIGHT - 40 - 180, 40, 80))
    return ground_platforms, floating_platforms, hatena_platforms, goal_platforms,hatena_emp_platforms

def draw_text(surf, text, size, x, y, color=BLACK, center=True):
    """画面にテキストを描画する"""
    font = pg.font.Font(None, size)
    txt = font.render(text, True, color)
    rect = txt.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surf.blit(txt, rect)


def main():
    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    pg.display.set_caption('Mini Mario')
    clock = pg.time.Clock()

        #背景画像を読み込む
    bg_img = pg.transform.scale(pg.image.load("img/haikei.png").convert(), (WIDTH, HEIGHT))
        #地面用の画像を読み込む
    ground_img = pg.image.load("img/ground.png").convert_alpha()
        # 浮遊ブロック用の画像 (icy_block.png)
    block_img = pg.image.load("img/huyuu.png").convert_alpha()
        # ゴール画像
    goal_img = pg.image.load("img/goal_pole.png").convert_alpha()
        # はてな画像
    hatena_img = pg.image.load("img/hatena.png").convert_alpha()
        # はてな空画像
    hatena_img_emp = pg.image.load("img/hatena_empty.png").convert_alpha()
    
    player = Player(50, HEIGHT - 90)
    ground_platforms, floating_platforms, hatena_platforms, goal_platforms , hatena_emp_platforms= build_level()

    platforms = ground_platforms + floating_platforms + hatena_platforms + goal_platforms + hatena_emp_platforms

    # Enemy の初期Y座標を修正: 足元を基準に配置
    import random
    enemies = [Enemy(WIDTH-100, HEIGHT - 40 - Enemy_base_height)]

#ステージごとに敵をランダムに出現させる場合のコード例
    # import random
    # enemies = []
    # if random.random() < 0.5:
    #     enemies.append(Enemy(420, HEIGHT - 40, left_bound=400, right_bound=760))

    projectiles = []

    # 右上に能力を表示するインスタンスを作成
    power_display = PowerUpDisplay(pos=(WIDTH - 80, 30))

    font = pg.font.Font(None, 36)
    play_time = 0.0

    running = True
    while running:
        # ... (イベント処理、更新処理は省略) ...
        dt = clock.tick(FPS) / 1000.0
        play_time += dt
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYDOWN and event.key == pg.K_x:
                # プレイヤーが火または氷の力を持っている場合にのみ発射物を生成します
                if player.power in ('fire', 'ice'):
                    # プレイヤーの前方に出現
                    px = player.rect.centerx + player.facing * (player.rect.width//2 + 5)
                    py = player.rect.centery
                    projectiles.append(Projectile(px, py, player.power, player.facing))
        keys = pg.key.get_pressed()
        player.handle_input(keys)
        player.update(platforms)
        # 新しい敵の出現処理をここに追加（10秒ごとに出現させるなど）
        for e in enemies:
            e.update(platforms)


        for p in projectiles[:]:
            p.update()
            # 画面外の場合は削除
            if p.rect.right < 0 or p.rect.left > WIDTH:
                try:
                    projectiles.remove(p)
                except ValueError:
                    pass
            else:
                # 発射物と敵の衝突
                for e in enemies[:]:
                    if p.rect.colliderect(e.rect):
                        try:
                            enemies.remove(e)

                        except ValueError:
                            pass
                        try:
                            projectiles.remove(p)
                        except ValueError:
                            pass
                        break

        # プレイヤーと敵の衝突判定
        dead = False
        for e in enemies:
            if player.rect.colliderect(e.rect):
                # if player is falling and hits top of enemy, kill enemy
                if player.vy > 0 and player.rect.bottom - e.rect.top < 20:
                    try:
                        enemies.remove(e)
                    except ValueError:
                        pass
                    player.vy = -8
                else:
                    dead = True

        # 画面下に落ちたら死亡
        if player.rect.top > HEIGHT:
            player = Player(50, HEIGHT - 90)    
            dead = True

        # リスポーン
        if dead:
            # simple respawn
            player = Player(50, HEIGHT - 90)
            enemies_x = random.choice([WIDTH // 2, WIDTH-100])
            #　敵は地面がある位置に出現
            enemies = [Enemy(enemies_x, HEIGHT - 40 - Enemy_base_height)]
            play_time = 0.0
   
        # draw
        screen.blit(bg_img, (0, 0)) # 背景描画

        # 地面を描画
        for p in ground_platforms:
            # 地面はタイル状に描画
            # 元画像の縦横比を維持し、p.heightを基準にリサイズ
            orig_w, orig_h = ground_img.get_size()
            scaled_img = pg.transform.scale(ground_img, (p.width, p.height))
            screen.blit(scaled_img, p)
        # 浮遊ブロックを描画 (ice_block.png)
        for p in floating_platforms:
            # 元画像の縦横比を維持し、p.heightを基準にリサイズ
            orig_w, orig_h = block_img.get_size()
            scaled_img = pg.transform.scale(block_img, (p.width, p.height))
            # 当たり判定pを、リサイズ後の画像に合わせて更新
            p.size = scaled_img.get_size()
            p.center = p.center # 元の中心位置を維持
            screen.blit(scaled_img, p)
        # はてなブロックを描画 (hatena_block.png)
        for p in hatena_platforms:
            # 元画像の縦横比を維持し、p.heightを基準にリサイズ
            scaled_img = pg.transform.scale(hatena_img,(p.width, p.height))
            p.size = scaled_img.get_size()
            p.center = p.center
            screen.blit(scaled_img, p)
        #はてなemptyを描画
        for p in hatena_emp_platforms:
            # 元画像の縦横比を維持し、p.heightを基準にリサイズ
            scaled_img = pg.transform.scale(hatena_img_emp,(p.width, p.height))
            p.size = scaled_img.get_size()
            p.center = p.center
            screen.blit(scaled_img, p)
        # ゴールを描画 (goal_pole.png)
        for p in goal_platforms:
            # ゴールはp.size(40,80)に合わせて描画
            scaled_img = pg.transform.scale(goal_img, p.size)
            # p.sizeを変更しないように修正
            screen.blit(scaled_img, p)

        for e in enemies:
            e.draw(screen)
        for p in projectiles:
            p.draw(screen)
        player.draw(screen)

        # 現在の能力を右上に表示
        power_display.draw(screen, player.power)
        # タイムを左上に表示(黒い四角の上に白文字)
        draw_text(screen, f"Time: {play_time:.2f}", 30, 80, 50, WHITE)

        pg.display.flip()

    pg.quit()




if __name__ == '__main__':
    main()
