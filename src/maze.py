import random
from time import sleep, strftime
from .solve import astar
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import os


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def conv_ind(value):
    return 2 * value + 1


def alg_Prim(maze_cls):
    walls = []
    cell = random.choice(random.choice(maze_cls.cells))
    cell.visited = True
    walls.extend(maze_cls.get_walls(cell))
    while walls:
        wall = random.choice(walls)
        match wall[2]:
            case "h":
                cell_1 = maze_cls.cells[wall[0] // 2][(wall[1] - 2) // 2]
                cell_2 = maze_cls.cells[wall[0] // 2][wall[1] // 2]
            case "v":
                cell_1 = maze_cls.cells[(wall[0] - 2) // 2][wall[1] // 2]
                cell_2 = maze_cls.cells[wall[0] // 2][wall[1] // 2]
        if cell_1.visited + cell_2.visited == 1:
            maze_cls.maze[wall[0]][wall[1]] = 0
            if not cell_1.visited:
                walls.extend(maze_cls.get_walls(cell_1))
                cell_1.visited = True
            else:
                walls.extend(maze_cls.get_walls(cell_2))
                cell_2.visited = True
        walls.remove(wall)


def alg_DFS(maze_cls):
    stack = []
    cell = maze_cls.cells[0][0]
    cell.visited = True
    stack.append(cell)
    while stack:
        next_cell = maze_cls.get_neighbor(cell.x, cell.y)
        if next_cell:
            next_cell.visited = True
            
            maze_cls.maze[next_cell.y + cell.y + 1]\
                [next_cell.x + cell.x + 1] = 0
            
            cell = next_cell
            stack.append(cell)
        elif stack:
            cell = stack.pop()


def log_maze_to_file(maze_cls, step_name, file_name="maze_log.txt"):
    with open(file_name, "a") as file:
        file.write(f"Step: {step_name}\n")
        formatted_maze = maze_cls.get_pretty_maze()  # Получаем красиво отформатированный лабиринт
        for row in formatted_maze:
            file.write(row + "\n")
        file.write("\n" + "-" * 40 + "\n")


def agent(seed_x, seed_y, maze_cls, step_name, destroyed_walls):
    stack = []
    cell = maze_cls.cells[seed_y][seed_x]

    with cell.lock:
        if not cell.visited:
            cell.visited = True
            stack.append(cell)

    while stack:
        current = stack[-1]
        next_cell = maze_cls.get_neighbor(current.x, current.y)
        if next_cell:
            with next_cell.lock:
                if not next_cell.visited:
                    next_cell.visited = True
                    maze_cls.maze[next_cell.y + current.y + 1][next_cell.x + current.x + 1] = 0
                    
                    # Определяем координаты стены между текущей и следующей клеткой
                    if current.x == next_cell.x:
                        wall = (min(current.y, next_cell.y), current.x, 'v')
                    else:
                        wall = (current.y, min(current.x, next_cell.x), 'h')

                    # Проверяем, разрушалась ли эта стена ранее
                    if wall not in destroyed_walls:
                        # Если не разрушалась, добавляем её в множество
                        destroyed_walls.add(wall)
                    else:
                        # Восстанавливаем стену, если она была разрушена ранее
                        maze_cls.maze[next_cell.y + current.y + 1][next_cell.x + current.x + 1] = 1
                        stack.pop() 
                        continue
                    
                    stack.append(next_cell)
                else:
                    stack.pop()
        else:
            stack.pop() 

        # log_maze_to_file(maze_cls, f"{step_name}_step_{len(stack)}")


def alg_DFS_parallel(maze_cls, num_agents=8):
    seeds = []
    destroyed_walls = set()  # Множество для отслеживания разрушенных стен
    
    # Выбираем стартовые точки
    for _ in range(num_agents):
        while True:
            x = random.randint(0, maze_cls.width - 1)
            y = random.randint(0, maze_cls.height - 1)
            if not maze_cls.cells[y][x].visited:
                seeds.append((x, y))
                break

    with ThreadPoolExecutor(max_workers=num_agents) as executor:
        for i, (x, y) in enumerate(seeds):
            # Каждый агент будет выполнять свою задачу с уникальным именем шага
            executor.submit(agent, x, y, maze_cls, f"agent_{i + 1}", destroyed_walls)



class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.visited = False
        self.lock = Lock()



class Maze:
    def __init__(self, algorithm, size, run_alg=True):
        self.width, self.height = size
        self.maze = [[0 if i % 2 and j % 2 else 1 
                        for i in range(conv_ind(self.width))] 
                            for j in range(conv_ind(self.height))]
        self.cells = [[Cell(i, j) 
                         for i in range(self.width)] 
                             for j in range(self.height)]
        if run_alg:
            algorithm(self)


    def set_zeros(self):
        for j in range(conv_ind(self.height)):
            for i in range(conv_ind(self.width)):
                self.maze[j][i] = 0


    def get_random_cell(self):
        while self.maze[y := conv_ind(random.randint(1, self.height - 1))]\
            [x := conv_ind(random.randint(1, self.width - 1))] != 0:
            pass

        self.maze[y][x] = -1
        return x, y
    

    def set_elems(self, elems, type):
        for i, j in elems:
            self.maze[j][i] = type


    def get_elems(self, type):
        res = []
        for j in range(conv_ind(self.height)):
            for i in range(conv_ind(self.width)):
                if self.maze[j][i] == type:
                    res.append((i, j))
        return res


    def get_walls(self, cell):
        walls = []
        if cell.x > 0 and self.maze[conv_ind(cell.y)][conv_ind(cell.x) - 1]:
            walls.append((conv_ind(cell.y), conv_ind(cell.x) - 1, "h"))

        if cell.x < self.width - 1 and self.maze[conv_ind(cell.y)]\
                                           [conv_ind(cell.x) + 1]:
            walls.append((conv_ind(cell.y), conv_ind(cell.x) + 1, "h"))

        if cell.y > 0 and self.maze[conv_ind(cell.y) - 1]\
                              [conv_ind(cell.x)]:
            walls.append((conv_ind(cell.y) - 1, conv_ind(cell.x), "v"))

        if cell.y < self.height - 1 and self.maze[conv_ind(cell.y) + 1]\
                                            [conv_ind(cell.x)]:
            walls.append((conv_ind(cell.y) + 1, conv_ind(cell.x), "v"))

        return walls
        
    
    def get_neighbor(self, x, y):
        neighbors = []

        if x > 0 and not self.cells[y][x - 1].visited:
            neighbors.append(self.cells[y][x - 1])

        if x < self.width - 1 and not self.cells[y][x + 1].visited:
            neighbors.append(self.cells[y][x + 1])

        if y > 0 and not self.cells[y - 1][x].visited:
            neighbors.append(self.cells[y - 1][x])

        if y < self.height - 1 and not self.cells[y + 1][x].visited:
            neighbors.append(self.cells[y + 1][x])
        
        return random.choice(neighbors) if neighbors else False


    def save(self):
        timestr = strftime("%H_%M_%S-%d_%m_%Y")

        with open("maze_"+timestr+".txt", "w") as file:
            file.writelines(["".join(row) + '\n' for row in self.maze])
    

    def pretty_maze(self):
        for i in range(conv_ind(self.height)):
            for j in range(conv_ind(self.width)):

                if (i + j) % 2 == 0 and self.maze[i][j] == 1:
                    self.maze[i][j] = '+'
                elif j % 2 and self.maze[i][j] == 1:
                    self.maze[i][j] = '---'
                elif i % 2 and self.maze[i][j] == 1:
                    self.maze[i][j] = '|'
                elif j % 2 == 0 and self.maze[i][j] == 2:
                    self.maze[i][j] = '@'
                elif j % 2 != 0 and self.maze[i][j] == 2:
                    self.maze[i][j] = '@@@'    
                elif j % 2 == 0:
                    self.maze[i][j] = ' '
                else:
                    self.maze[i][j] = '   '

                    
    def get_pretty_maze(self):
        formatted_maze = []
        for i in range(conv_ind(self.height)):
            row = ""
            for j in range(conv_ind(self.width)):

                if (i + j) % 2 == 0 and self.maze[i][j] == 1:
                    row += "+"
                elif j % 2 and self.maze[i][j] == 1:
                    row += "---"
                elif i % 2 and self.maze[i][j] == 1:
                    row += "|"
                elif j % 2 == 0 and self.maze[i][j] == 2:
                    row += "@"
                elif j % 2 != 0 and self.maze[i][j] == 2:
                    row += "@@@"
                elif j % 2 == 0:
                    row += " "
                else:
                    row += "   "
            formatted_maze.append(row)
        return formatted_maze

        
    @classmethod        
    def upload(cls, path, algorithm):
        lines = []
        
        with open(path, "r", encoding="UTF-8") as file:
            for line in file:
                buf = []
                for line in line.rstrip("\n"):
                    buf.append(line)
                lines.append(buf)
        
        width = (len(lines[0]) - 1) // 2 + 1
        height = len(lines)

        new = cls(algorithm, 
                  ((width - 1) // 2, (height - 1) // 2),
                  run_alg=False)
        
        for i in range(len(lines)):
            for j in range((len(lines[i]) - 1) // 2 + 1):
                if lines[i][2 * j] == "+" or lines[i][2 * j] == "|":
                    new.maze[i][j] = 1
                elif j % 2 and lines[i][2 * j] == "-":
                    new.maze[i][j] = 1
                else:
                    new.maze[i][j] = 0

        return new
        
                    
    def solve(self):

        solution = astar((1, 1), 
                         (conv_ind(self.height) - 2, 
                          conv_ind(self.width) - 2), 
                         self.maze)
        
        for coord in solution:
            self.maze[coord[0]][coord[1]] = 2
            

    def display(self):
        for i in range(conv_ind(self.height)):
            for j in range(conv_ind(self.width)):
                print(self.maze[i][j], end='')
            print()


def start_generator(alg, width, height, 
                    solution, filename, save_maze):
    if filename:
        my_maze = Maze.upload(filename, alg)
    else:
        my_maze = Maze(alg, (width, height))
    
    if solution:
        my_maze.solve()

    my_maze.pretty_maze()
    my_maze.display()

    if save_maze:
        my_maze.save()
    