import pygame
from pathlib import PurePath
from time import time
from src.maze import Maze, Cell, conv_ind


class Globals():
    START_COLOR   = (255, 255, 0)
    END_COLOR     = (100, 194, 237)
    COLOR         = (255, 100, 98) 
    SURFACE_COLOR = (167, 255, 100) 
    PATH_COLOR    = (80,  200, 120) 
    CELL_SIZE = 20
    END_GAME_TIME = [False, True]
    COUNT_DESTROYED_WALLS = [0, 0]
    DESTROYED_WALLS = []


def size_convert(value):
    return conv_ind(value) * Globals.CELL_SIZE


class MazeElementWithGraphics(Cell, pygame.sprite.Sprite):
    def __init__(self, x, y, value, sol):
        Cell.__init__(self, x, y)
        pygame.sprite.Sprite.__init__(self)
        self.value = value
        self.image = pygame.Surface([Globals.CELL_SIZE, 
                                     Globals.CELL_SIZE])
        
        color = [Globals.SURFACE_COLOR, 
                 Globals.COLOR, 
                 Globals.PATH_COLOR if sol else Globals.SURFACE_COLOR, 
                 Globals.START_COLOR, 
                 Globals.END_COLOR]
        
        self.image.fill(color[value])
        
        pygame.draw.rect(self.image, color[value], 
                         pygame.Rect(x * Globals.CELL_SIZE, 
                                     y * Globals.CELL_SIZE,
                                     Globals.CELL_SIZE,
                                     Globals.CELL_SIZE)) 
        
        self.rect = self.image.get_rect()
        self.rect.x = x * Globals.CELL_SIZE
        self.rect.y = y * Globals.CELL_SIZE


class MazeBonuses(pygame.sprite.Sprite):
    def __init__(self, x, y, type):
        super().__init__()
        self.type = type
        path_bonus = PurePath('images', 'bonus.png')
        self.image = pygame.image.load(path_bonus)
        self.rect = self.image.get_rect()
        self.rect.x = x * Globals.CELL_SIZE
        self.rect.y = y * Globals.CELL_SIZE


    def update(self, player, maze):
        if self.rect.colliderect(player.rect) and self.type == "speed_up":
            player.speed *= 1.3
            print(f"{player.speed=}")
            self.kill()
        if self.rect.colliderect(player.rect) and self.type == "speed_down":
            player.speed *= 0.7
            print(f"{player.speed=}")
            self.kill()
        if self.rect.colliderect(player.rect) and self.type == "teleport":
            x, y = maze.get_random_cell()
            player.rect.x = x * Globals.CELL_SIZE
            player.rect.y = y * Globals.CELL_SIZE
            print(f"{x=} {y=}")
            self.kill()


class MazeWithGraphics(Maze):
    def __init__(self, algorithm, size, run_alg=True):
        super().__init__(algorithm, size, run_alg)
        self.elems_to_draw = None


    def set_elems_to_draw(self, show_path):
        self.solve()
        self.elems_to_draw = [[MazeElementWithGraphics(i, j, 
                                                       self.maze[j][i], 
                                                       show_path)
                                 for i in range(conv_ind(self.width))] 
                                     for j in range(conv_ind(self.height))]
        

    @classmethod        
    def upload(cls, path, algorithm):
        new = super(MazeWithGraphics, cls).upload(path, algorithm)
        return new
    

    def add_start_end_to_group(self):
        start_end_cells = pygame.sprite.Group()
        self.maze[1][1] = 3
        self.maze[2 * self.height - 1][2 * self.width - 1] = 4
        self.elems_to_draw[1][1] = MazeElementWithGraphics(1, 1, 
                                                           self.maze[1][1],
                                                           None)
        self.elems_to_draw[conv_ind(self.height) - 2]\
            [conv_ind(self.width) - 2] = \
                MazeElementWithGraphics(
                    conv_ind(self.width) - 2, 
                    conv_ind(self.height) - 2, 
                    self.maze[conv_ind(self.height) - 2]\
                        [conv_ind(self.width) - 2],
                    None)
        
        start_end_cells.add(self.elems_to_draw[1][1], 
            self.elems_to_draw[conv_ind(self.height) - 2]\
            [conv_ind(self.width) - 2])
        return start_end_cells
    

    def get_elem_position(self, type):
        pos = []
        [[pos.append((i, j))
            for i in range(conv_ind(self.width)) if self.maze[j][i] == type]
                for j in range(conv_ind(self.height))]
        return pos
    

    def add_walls_to_group(self):
        walls_sprites_list = pygame.sprite.Group() 
        
        [[walls_sprites_list.add(self.elems_to_draw[j][i]) 
            for i in range(conv_ind(self.width)) if self.maze[j][i] == 1]
                for j in range(conv_ind(self.height))]
        
        return walls_sprites_list
    
    def get_sol_position(self):
        sol_list = []
        [[sol_list.append((self.elems_to_draw[j][i].rect.x, self.elems_to_draw[j][i].rect.y))
            for i in range(conv_ind(self.width)) if self.maze[j][i] == 2]
                for j in range(conv_ind(self.height))]
        return sol_list

    def add_solution_to_group(self):
        solution_sprites_list = pygame.sprite.Group() 
        [[solution_sprites_list.add(self.elems_to_draw[j][i]) 
            for i in range(conv_ind(self.width)) if self.maze[j][i] == 2] 
                for j in range(conv_ind(self.height))]
        return solution_sprites_list


class Player(pygame.sprite.Sprite):
    def __init__(self, num=0, speed=2):
        super().__init__() 
        self.num = num
        self.speed = speed
        path_blue = PurePath('images', "Player_blue.png")
        path_red = PurePath('images', "Player_red.png")
        self.image = pygame.image.load(path_blue)
        if self.num:
            self.image = pygame.image.load(path_red)
        self.rect = self.image.get_rect()
        self.rect.x = 1.25 * Globals.CELL_SIZE
        self.rect.y = 1.25 * Globals.CELL_SIZE
    
    
    def update(self, walls_sprites_list, end_cell, 
               width_limit, height_limit, bonuses):
        global end_flag
        self.speedx = 0
        self.speedy = 0
        old_x, old_y = self.rect.topleft
        
        keystate = pygame.key.get_pressed()
        keys = {'left':    (pygame.K_LEFT,  pygame.K_a),
                'right':   (pygame.K_RIGHT, pygame.K_d),
                'down':    (pygame.K_DOWN,  pygame.K_s),
                'up':      (pygame.K_UP,    pygame.K_w),
                'destroy': (pygame.K_RSHIFT, pygame.K_LSHIFT)}

        if keystate[keys['left'][self.num]]:
            self.speedx = -self.speed
        if keystate[keys['right'][self.num]]:
            self.speedx = self.speed
        if keystate[keys['down'][self.num]]:
            self.speedy = self.speed
        if keystate[keys['up'][self.num]]:
            self.speedy = -self.speed

        self.rect.x += self.speedx
        self.rect.y += self.speedy

        if self.rect.left <= 0 or self.rect.right >= width_limit:
            self.rect.x = old_x
        
        if self.rect.top <= 0 or self.rect.bottom >= height_limit:
            self.rect.y = old_y

        
        for wall in walls_sprites_list:
            if self.rect.colliderect(wall.rect):
                self.rect.x = old_x
                self.rect.y = old_y

                if (keystate[keys['destroy'][self.num]] and  
                        Globals.COUNT_DESTROYED_WALLS[self.num] < 3 and
                        bonuses):
                    
                    Globals.COUNT_DESTROYED_WALLS[self.num] += 1 
                    Globals.DESTROYED_WALLS = [wall.rect.x, wall.rect.y]
                    print(Globals.DESTROYED_WALLS)
                    wall.kill()
                
        if (self.rect.colliderect(end_cell.rect) and 
                not Globals.END_GAME_TIME[self.num]):
            
            Globals.END_GAME_TIME[self.num] = time()

        
            
        
    def draw(self, surface):
        surface.blit(self.image, self.rect)


def print_winner(start_time, players_count):
    if Globals.END_GAME_TIME[0] and Globals.END_GAME_TIME[1]: 
        
        print("BLUE TIME: ", end='')
        print(f"{Globals.END_GAME_TIME[0] - start_time:.2f} sec")
                
        if players_count == 2:
            print("RED TIME: ", end='')
            print(f"{Globals.END_GAME_TIME[1] - start_time:.2f} sec")
                    
            print("WINNER: ", end='')
            if (Globals.END_GAME_TIME[1] < Globals.END_GAME_TIME[0]):
                print('RED')
            else:
                print('BLUE')
                
        pygame.quit()  
        quit()
    


def start_game(alg, width, height, filename,
               solution, players_count, bonuses, speed):
    pygame.init()

    if filename:
        my_maze = MazeWithGraphics.upload(filename, alg)
    else:
        my_maze = MazeWithGraphics(alg, (width, height))
    
    my_maze.set_elems_to_draw(solution)

    screen = pygame.display.set_mode((size_convert(my_maze.width), 
                                      size_convert(my_maze.height)))

    pygame.display.set_caption("Try to solve!")
    path_icon = PurePath('images', "icon.png")
    pygame_icon = pygame.image.load(path_icon)
    pygame.display.set_icon(pygame_icon)
    clock = pygame.time.Clock() 
    
    walls_sprites_list = my_maze.add_walls_to_group()
    solution_sprites_list = my_maze.add_solution_to_group()
    start_end_cells = my_maze.add_start_end_to_group()

    if bonuses:
        bonuse_tp = [MazeBonuses(*my_maze.get_random_cell(), "teleport") 
                         for _ in range((my_maze.width + my_maze.height)//2)]
        
        bonuse_speed_up = [MazeBonuses(*my_maze.get_random_cell(), "speed_up")
                               for _ in range(4)]
        
        bonuse_speed_down = [MazeBonuses(*my_maze.get_random_cell(),
                                         "speed_down") for _ in range(4)]
        
        bonuses_group = pygame.sprite.Group(*bonuse_tp, 
                                            *bonuse_speed_up, 
                                            *bonuse_speed_down)
    
    player_0 = Player(0, speed=speed)
    group_players = pygame.sprite.Group()
    group_players.add(player_0)

    if players_count == 2:
        player_1 = Player(1, speed=speed)
        group_players.add(player_1)
        Globals.END_GAME_TIME[1] = False

    start_time = time()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("You couldn't solve it!")
                pygame.quit()  
                quit()
            print_winner(start_time, players_count)

        walls_sprites_list.update() 
        solution_sprites_list.update()
        group_players.update(walls_sprites_list, start_end_cells.sprites()[1],
                            size_convert(width), size_convert(height),
                            bonuses)
        start_end_cells.update()
        if bonuses:
            bonuses_group.update(player_0, my_maze)
        if players_count == 2 and bonuses:
            bonuses_group.update(player_1, my_maze)
        
        screen.fill(Globals.SURFACE_COLOR)
        walls_sprites_list.draw(screen)
        solution_sprites_list.draw(screen)
        start_end_cells.draw(screen)
        group_players.draw(screen)
        if bonuses:
            bonuses_group.draw(screen)
        
        pygame.display.flip() 
        clock.tick(60)


    
    