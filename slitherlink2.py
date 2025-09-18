import tkinter as tk
import json
import random

SIZE = 5  # 盤面サイズ
CELL = 48
MARGIN = 60

# --- クラス・関数定義 ---
class Grid:
    def __init__(self, size):
        self.size = size
        self.numbers = [[None for _ in range(size)] for _ in range(size)]
    def set_numbers(self, nums):
        self.numbers = nums

class Edge:
    def __init__(self, size):
        self.size = size
        self.h_edges = [[0]*(size) for _ in range(size+1)]  # 横線
        self.v_edges = [[0]*(size+1) for _ in range(size)]  # 縦線
    def toggle_h(self, y, x):
        self.h_edges[y][x] = (self.h_edges[y][x]+1)%2
    def toggle_v(self, y, x):
        self.v_edges[y][x] = (self.v_edges[y][x]+1)%2
    def clear(self):
        self.h_edges = [[0]*(self.size) for _ in range(self.size+1)]
        self.v_edges = [[0]*(self.size+1) for _ in range(self.size)]

class GameState:
    def __init__(self, grid, edge):
        self.grid = grid
        self.edge = edge
        self.undo_stack = []
        self.redo_stack = []
    def save(self):
        state = json.dumps({
            'h': self.edge.h_edges,
            'v': self.edge.v_edges
        })
        self.undo_stack.append(state)
        self.redo_stack.clear()
    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.undo_stack.pop())
            if self.undo_stack:
                self.load(self.undo_stack[-1])
    def redo(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.load(state)
            self.undo_stack.append(state)
    def load(self, state):
        data = json.loads(state)
        self.edge.h_edges = data['h']
        self.edge.v_edges = data['v']

class Renderer:
    def __init__(self, root, grid, edge, controller):
        self.root = root
        self.grid = grid
        self.edge = edge
        self.controller = controller
        w = CELL*(SIZE)+MARGIN*2
        h = CELL*(SIZE)+MARGIN*2+60
        self.canvas = tk.Canvas(root, width=w, height=h)
        self.canvas.pack()
        self.canvas.bind('<Button-1>', self.on_click)
        self.draw()
    def draw(self):
        self.canvas.delete('all')
        # 点（交点）
        for y in range(SIZE+1):
            for x in range(SIZE+1):
                self.canvas.create_oval(
                    MARGIN+x*CELL-4, MARGIN+y*CELL-4,
                    MARGIN+x*CELL+4, MARGIN+y*CELL+4,
                    fill='#333')
        # 数字（グリッド中央）
        for y in range(SIZE):
            for x in range(SIZE):
                num = self.grid.numbers[y][x]
                if num is not None:
                    self.canvas.create_text(
                        MARGIN+x*CELL+CELL//2,
                        MARGIN+y*CELL+CELL//2,
                        text=str(num),
                        font=("MS Gothic", 20),
                        tags="number"
                    )
        # 線（交点同士）
        for y in range(SIZE+1):
            for x in range(SIZE):
                if self.edge.h_edges[y][x] == 1:
                    self.canvas.create_line(
                        MARGIN+x*CELL, MARGIN+y*CELL,
                        MARGIN+(x+1)*CELL, MARGIN+y*CELL,
                        width=4, fill="blue", tags="edge")
        for y in range(SIZE):
            for x in range(SIZE+1):
                if self.edge.v_edges[y][x] == 1:
                    self.canvas.create_line(
                        MARGIN+x*CELL, MARGIN+y*CELL,
                        MARGIN+x*CELL, MARGIN+(y+1)*CELL,
                        width=4, fill="blue", tags="edge")
        # NG判定
        if self.controller.gameover and self.controller.is_ng():
            self.canvas.create_text(self.canvas.winfo_width()//2, MARGIN+SIZE*CELL+30, text='NG', font=('MS Gothic', 24), fill='red')
        # ゴール判定（全ての数値の周囲の線が一致＆一筆書き）
        elif self.controller.is_goal() and self.controller.is_all_numbers_ok():
            self.canvas.create_text(self.canvas.winfo_width()//2, MARGIN+SIZE*CELL+30, text='ゴール', font=('MS Gothic', 24), fill='green')
    def on_click(self, event):
        # 線の近くを判定
        x = (event.x - MARGIN) // CELL
        y = (event.y - MARGIN) // CELL
        if event.x < MARGIN or event.y < MARGIN or x > SIZE or y > SIZE:
            return
        # 横線
        for yy in range(SIZE+1):
            for xx in range(SIZE):
                x0 = MARGIN+xx*CELL
                y0 = MARGIN+yy*CELL-8
                x1 = MARGIN+(xx+1)*CELL
                y1 = MARGIN+yy*CELL+8
                if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                    self.controller.toggle_h(yy, xx)
                    self.draw()
                    return
        # 縦線
        for yy in range(SIZE):
            for xx in range(SIZE+1):
                x0 = MARGIN+xx*CELL-8
                y0 = MARGIN+yy*CELL
                x1 = MARGIN+xx*CELL+8
                y1 = MARGIN+(yy+1)*CELL
                if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                    self.controller.toggle_v(yy, xx)
                    self.draw()
                    return

class Controller:
    def __init__(self, grid, edge, state, renderer):
        self.grid = grid
        self.edge = edge
        self.state = state
        self.renderer = renderer
        self.gameover = False
    def toggle_h(self, y, x):
        if self.gameover:
            return
        self.edge.toggle_h(y, x)
        self.state.save()
        if self.is_ng():
            self.gameover = True
    def toggle_v(self, y, x):
        if self.gameover:
            return
        self.edge.toggle_v(y, x)
        self.state.save()
        if self.is_ng():
            self.gameover = True
    def is_ng(self):
        # 各マスの数字より線が多い場合NG
        for y in range(SIZE):
            for x in range(SIZE):
                num = self.grid.numbers[y][x]
                if num is not None:
                    cnt = 0
                    if self.edge.h_edges[y][x]:
                        cnt += 1
                    if self.edge.h_edges[y+1][x]:
                        cnt += 1
                    if self.edge.v_edges[y][x]:
                        cnt += 1
                    if self.edge.v_edges[y][x+1]:
                        cnt += 1
                    if cnt > num:
                        return True
        return False
    def is_goal(self):
        # 線が一筆書きで全てつながっているか判定（BFS）
        points = set()
        edges = set()
        for y in range(SIZE+1):
            for x in range(SIZE+1):
                # 横線
                if x<SIZE and self.edge.h_edges[y][x]:
                    edges.add(((x,y),(x+1,y)))
                    points.add((x,y))
                    points.add((x+1,y))
                # 縦線
                if y<SIZE and self.edge.v_edges[y][x]:
                    edges.add(((x,y),(x,y+1)))
                    points.add((x,y))
                    points.add((x,y+1))
        if not edges:
            return False
        # BFSで連結判定
        visited = set()
        start = next(iter(points))
        queue = [start]
        while queue:
            p = queue.pop()
            if p in visited:
                continue
            visited.add(p)
            for e in edges:
                if p == e[0] and e[1] not in visited:
                    queue.append(e[1])
                elif p == e[1] and e[0] not in visited:
                    queue.append(e[0])
        # 線がある全ての点が訪問済みなら一筆書き
        return visited == points
    def is_all_numbers_ok(self):
        # 全ての数値の周囲の線が一致しているか判定
        for y in range(SIZE):
            for x in range(SIZE):
                num = self.grid.numbers[y][x]
                if num is not None:
                    cnt = 0
                    if self.edge.h_edges[y][x]:
                        cnt += 1
                    if self.edge.h_edges[y+1][x]:
                        cnt += 1
                    if self.edge.v_edges[y][x]:
                        cnt += 1
                    if self.edge.v_edges[y][x+1]:
                        cnt += 1
                    if cnt != num:
                        return False
        return True
    def is_solved(self):
        # 仮実装: 盤面が外周ループなら解決
        # 本格実装は一意解チェック
        return True

def make_random_grid(size):
    return [[random.randint(0,3) for _ in range(size)] for _ in range(size)]

def set_edge_from_loop(edge, L):
    (x1,y1),(x2,y2) = L
    if y1==y2:
        y = y1
        x = min(x1,x2)
        edge.h_edges[y][x] = 1
    elif x1==x2:
        x = x1
        y = min(y1,y2)
        edge.v_edges[y][x] = 1

# --- ループ生成・数字配置・検証・保存 ---
class LoopGenerator:
    def __init__(self, size):
        self.size = size
    def generate(self):
        # DFSでランダムな一筆書きループ（多角形）を生成
        size = self.size
        visited = set()
        edges = set()
        # グリッド上の点
        points = [(x, y) for y in range(size+1) for x in range(size+1)]
        # スタート点をランダムに選ぶ
        start = random.choice(points)
        path = [start]
        def neighbors(p):
            x, y = p
            result = []
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx <= size and 0 <= ny <= size:
                    result.append((nx, ny))
            return result
        def dfs(p, prev):
            visited.add(p)
            nbs = neighbors(p)
            random.shuffle(nbs)
            for nb in nbs:
                if nb == prev:
                    continue
                if nb == start and len(path) > 3:
                    # 閉ループ完成
                    edges.add((p, nb))
                    path.append(nb)
                    return True
                if nb not in visited:
                    edges.add((p, nb))
                    path.append(nb)
                    if dfs(nb, p):
                        return True
                    # 戻る
                    edges.remove((p, nb))
                    path.pop()
            visited.remove(p)
            return False
        dfs(start, None)
        # ループとしてedgesを返す
        # 方向を揃える
        loop = set()
        for e in edges:
            loop.add(tuple(sorted(e)))
        return loop

class NumberAssigner:
    def __init__(self, loop):
        self.loop = loop
    def assign(self):
        return self.assign_with_none_rate(0.2)
    def assign_with_none_rate(self, none_rate):
        numbers = [[None for _ in range(SIZE)] for _ in range(SIZE)]
        for y in range(SIZE):
            for x in range(SIZE):
                cnt = 0
                # 周囲4辺のうちループに含まれる数
                if (((x,y),(x+1,y)) in self.loop) or (((x+1,y),(x,y)) in self.loop):
                    cnt += 1
                if (((x,y+1),(x+1,y+1)) in self.loop) or (((x+1,y+1),(x,y+1)) in self.loop):
                    cnt += 1
                if (((x,y),(x,y+1)) in self.loop) or (((x,y+1),(x,y)) in self.loop):
                    cnt += 1
                if (((x+1,y),(x+1,y+1)) in self.loop) or (((x+1,y+1),(x+1,y)) in self.loop):
                    cnt += 1
                numbers[y][x] = cnt
        # 難易度調整: none_rateのマスをNoneに
        for _ in range(int(SIZE*SIZE*none_rate)):
            y = random.randint(0,SIZE-1)
            x = random.randint(0,SIZE-1)
            numbers[y][x] = None
        return numbers

class Validator:
    def __init__(self, numbers):
        self.numbers = numbers
    def has_unique_solution(self):
        # 仮実装: 盤面が外周ループなら一意解
        # 本格実装は全探索やSATソルバー推奨
        return True

class SeedManager:
    @staticmethod
    def set_seed(seed):
        random.seed(seed)

class DifficultyEstimator:
    @staticmethod
    def estimate(numbers):
        # 難易度推定（仮）: 3や0の数で判定
        cnt3 = sum(row.count(3) for row in numbers)
        cnt0 = sum(row.count(0) for row in numbers)
        return f"3:{cnt3}, 0:{cnt0}"

# --- ファイル保存 ---
def save_to_file(numbers, seed):
    with open(f"slitherlink_{seed}.json", "w", encoding="utf-8") as f:
        json.dump({"seed": seed, "numbers": numbers}, f, ensure_ascii=False, indent=2)

# --- 盤面生成（必ずクリアできる盤面のみ） ---
def is_clearable(numbers, loop):
    # 盤面の数字がループ構造と一致するか判定
    for y in range(SIZE):
        for x in range(SIZE):
            num = numbers[y][x]
            if num is not None:
                cnt = 0
                if (((x,y),(x+1,y)) in loop) or (((x+1,y),(x,y)) in loop):
                    cnt += 1
                if (((x,y+1),(x+1,y+1)) in loop) or (((x+1,y+1),(x,y+1)) in loop):
                    cnt += 1
                if (((x,y),(x,y+1)) in loop) or (((x,y+1),(x,y)) in loop):
                    cnt += 1
                if (((x+1,y),(x+1,y+1)) in loop) or (((x+1,y+1),(x+1,y)) in loop):
                    cnt += 1
                if cnt != num:
                    return False
    return True

seed = 42
SeedManager.set_seed(seed)

# 盤面生成（グローバルloop/numbers）
def generate_board():
    global loop, numbers
    while True:
        loop = LoopGenerator(size=SIZE).generate()
        numbers = NumberAssigner(loop).assign_with_none_rate(0.2)
        if is_clearable(numbers, loop) and Validator(numbers).has_unique_solution():
            save_to_file(numbers, seed)
            break

generate_board()

# --- サンプル盤面 ---
grid = Grid(SIZE)
grid.set_numbers(numbers)
edge = Edge(SIZE)
state = GameState(grid, edge)
controller = Controller(grid, edge, state, None)

root = tk.Tk()
root.title("スリザーリンク風パズル")

renderer = Renderer(root, grid, edge, controller)
controller.renderer = renderer

# ゲームスタートボタン
btn_frame = tk.Frame(root)
btn_frame.pack()
def start_game():
    edge.clear()
    controller.gameover = False
    renderer.draw()
start_btn = tk.Button(btn_frame, text="ゲームスタート（線リセット）", font=("MS Gothic", 14), command=start_game)
start_btn.pack(side=tk.LEFT, padx=8)
def reset_game():
    generate_board()
    grid.set_numbers(numbers)
    edge.clear()
    controller.gameover = False
    renderer.draw()
reset_btn = tk.Button(btn_frame, text="ゲームリセット（盤面変更）", font=("MS Gothic", 14), command=reset_game)
reset_btn.pack(side=tk.LEFT, padx=8)
def auto_solve():
    edge.clear()
    for L in loop:
        set_edge_from_loop(edge, L)
    controller.gameover = False
    renderer.draw()
answer_btn = tk.Button(btn_frame, text="回答（自動クリア）", font=("MS Gothic", 14), command=auto_solve)
answer_btn.pack(side=tk.LEFT, padx=8)

# Undo/Redo キー
root.bind('<Control-z>', lambda e: (state.undo(), renderer.draw()))
root.bind('<Control-y>', lambda e: (state.redo(), renderer.draw()))
# スタート時線クリア
edge.clear()
renderer.draw()

root.mainloop()
