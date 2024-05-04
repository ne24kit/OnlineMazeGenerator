import socket
import json
import pygame
from pathlib import PurePath
from dataclasses import dataclass, asdict
from time import time
from src.game import MazeWithGraphics, size_convert, MazeBonuses, Player, Globals, print_winner
from _thread import *


@dataclass
class SetUpGame:
    width:    int 
    height:   int
    speed:    int
    solution: bool
    walls:    list
    bonuses:  list

@dataclass
class СlientToServer:
    x: int
    y: int
    destroyed_wall: list

@dataclass
class ServerToClient:
    x0: int
    y0: int
    x1: int
    y1: int
    speed: int
    bonuses: list
    destroyed_wall: list


class Client:
    _id_counter = 0
    def __init__(self):
        self.id = Client._id_counter
        Client._id_counter += 1
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = 'localhost'
        self.port = 8080

    def connect(self):
        try:
            self.client.connect((self.host, self.port))
        except:
            raise Exception("Can't connect to server")
        
        
    def send(self, info):
        try:
            self.client.sendall(bytes(json.dumps(asdict(info))))
        except:
            raise Exception("Can't send data to server")
        

    def recv(self, cls):
        try:
            return cls(json.loads(self.client.recv(1024).decode('UTF-8')))
        except:
            raise Exception("Can't recive date from server")
        
    def close(self):
        self.client.close()

    def start_client_game(self):
        pygame.init()
        players_count = 2
        data = SetUpGame(*json.loads(self.client.recv(1024*10).decode('UTF-8')).values())
        bonuses = bool(data.bonuses)
        print(bonuses)
        my_maze = MazeWithGraphics(None, 
                                   (data.width, data.height), 
                                   run_alg=False)
        
        my_maze.set_zeros()
        my_maze.set_elems(data.walls, 1)
        my_maze.display()
        my_maze.set_elems_to_draw(data.solution)
        my_maze.set_elems(data.bonuses, -1)

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
            counts_bounses = (my_maze.width + my_maze.height) // 2
            bonuse_tp = []
            bonuse_speed_up = []
            bonuse_speed_down = []
            for i, bonus in enumerate(data.bonuses):
                if i < counts_bounses:
                    bonuse_tp.append(MazeBonuses(bonus[0], bonus[1], "teleport"))
                elif i <  counts_bounses + 4:
                    bonuse_speed_up.append(MazeBonuses(bonus[0], bonus[1], "speed_up"))
                else:
                    bonuse_speed_down.append(MazeBonuses(bonus[0], bonus[1], "speed_down"))                    
            
            bonuses_group = pygame.sprite.Group(*bonuse_tp, 
                                                *bonuse_speed_up, 
                                                *bonuse_speed_down)
        print(bonuses_group)
        player_0 = Player(0, speed=data.speed)
        group_players = pygame.sprite.Group()
        group_players.add(player_0)

        if players_count == 2:
            player_1 = Player(1, speed=data.speed)
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

            group_players.update(walls_sprites_list, start_end_cells.sprites()[1],
                                size_convert(my_maze.width), 
                                size_convert(my_maze.height),
                                bonuses)
            self.client.sendall(bytes(json.dumps(asdict(СlientToServer(player_0.rect.x,
                                                                       player_0.rect.y,
                                                                       Globals.DESTROYED_WALLS))), 'UTF-8'))
            
            data = ServerToClient(*json.loads(self.client.recv(1024*10).decode('UTF-8')).values())
            player_0.rect.x = data.x0
            player_0.rect.y = data.y0
            player_1.rect.x = data.x1
            player_1.rect.y = data.y1
            player_0.speed = data.speed
            bonuses_coords = data.bonuses
            Globals.DESTROYED_WALLS = data.destroyed_wall

            for bonus in bonuses_group.sprites():
                if not [bonus.rect.x, bonus.rect.y] in bonuses_coords:
                    print(f"{bonuses_coords=}")
                    print(f"{[bonus.rect.x, bonus.rect.y]=}")
                    bonuses_group.remove(bonus)

            for wall in walls_sprites_list.sprites():
                if [wall.rect.x, wall.rect.y] == Globals.DESTROYED_WALLS:
                    walls_sprites_list.remove(wall)
            
            screen.fill(Globals.SURFACE_COLOR)
            walls_sprites_list.draw(screen)
            solution_sprites_list.draw(screen)
            start_end_cells.draw(screen)
            group_players.draw(screen)
            if bonuses:
                bonuses_group.draw(screen)
            
            pygame.display.flip() 
            clock.tick(60)



class Server:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = "localhost"
        self.port = 8080
        try:
            self.s.bind((self.host, self.port))
        except socket.error as e:
            str(e)
        self.s.listen()


    def accept_clients(self, alg, width, height, filename,
                solution, players_count, bonuses, speed):
        
        try:
            ThreadCount = 0
            while True:
                Client_0, address_0 = self.s.accept()
                print('Connected to: ' + address_0[0] + ':' + str(address_0[1]))
                Client_1, address_1 = self.s.accept()

                print('Connected to: ' + address_1[0] + ':' + str(address_1[1]))
                start_new_thread(self.start_server_game, (Client_0, Client_1, alg, width, height, filename,
                                                            solution, players_count, bonuses, speed))
                ThreadCount += 1
                print('Thread Number: ' + str(ThreadCount))
        finally:    
            self.s.close() 

    def start_server_game(self, conn_0, conn_1, alg, width, height, filename,
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
              
        print(bonuses)
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
        

        settings = SetUpGame(width,
                             height,
                             speed,
                             solution,
                             my_maze.get_elems(1),
                             my_maze.get_elems(-1))
        conn_0.sendall(bytes(json.dumps(asdict(settings)), 'UTF-8'))
        conn_1.sendall(bytes(json.dumps(asdict(settings)), 'UTF-8'))
        
        
        player_0 = Player(0, speed=speed)
        group_players = pygame.sprite.Group()
        group_players.add(player_0)

        if players_count == 2:
            player_1 = Player(1, speed=speed)
            group_players.add(player_1)
            Globals.END_GAME_TIME[1] = False

        start_time = time()
        try:
                
            while True:
                
                data_0 = СlientToServer(*json.loads(conn_0.recv(2048).decode('UTF-8')).values())
                data_1 = СlientToServer(*json.loads(conn_1.recv(2048).decode('UTF-8')).values())

                # обновляем позиции игроков 
                player_0.rect.x = data_0.x
                player_0.rect.y = data_0.y
                player_1.rect.x = data_1.x
                player_1.rect.y = data_1.y

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        print("You couldn't solve it!")
                        pygame.quit()  
                        quit()
                    print_winner(start_time, players_count)

                # Обрабатываем бонусы на сервере 
                if bonuses:
                    bonuses_group.update(player_0, my_maze)
                if players_count == 2 and bonuses:
                    bonuses_group.update(player_1, my_maze)
                bonuses_coords = [(elem.rect.x, elem.rect.y) for elem in bonuses_group.sprites()]
             
                conn_0.sendall(bytes(json.dumps(asdict(ServerToClient(player_0.rect.x,
                                                                      player_0.rect.y,
                                                                      player_1.rect.x,
                                                                      player_1.rect.y,
                                                                      player_0.speed,
                                                                      bonuses_coords,
                                                                      data_1.destroyed_wall))), 'UTF-8'))
                conn_1.sendall(bytes(json.dumps(asdict(ServerToClient(player_1.rect.x,
                                                                      player_1.rect.y,
                                                                      player_0.rect.x,
                                                                      player_0.rect.y,
                                                                      player_1.speed,
                                                                      bonuses_coords,
                                                                      data_0.destroyed_wall))), 'UTF-8'))
                
                screen.fill(Globals.SURFACE_COLOR)
                
                pygame.display.flip() 
                clock.tick(60)
        finally:
            self.s.close()

def start_client():
    c = Client()
    c.connect()
    c.start_client_game()


def start_server(alg, width, height, filename,
               solution, players_count, bonuses, speed):
    s = Server()
    s.accept_clients(alg, width, height, filename,
                solution, players_count, bonuses, speed)