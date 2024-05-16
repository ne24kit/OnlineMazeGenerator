import argparse
from .game import start_game
from .network_utils import start_client, start_server 
from .maze import start_generator, alg_DFS, alg_Prim

class RangeError(Exception):
    pass

def check_range(int_value):
    if 6 <= int_value <= 19:
        return True
    raise RangeError(f"Side of the maze must be between 6 and 19\n"
                     f"You entered: {int_value}")


def check(value):
    try:
        int_value = int(value)
        check_range(int_value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Enter an integer\n"
                                         f"You entered: {value}")
    except RangeError as e:
        raise argparse.ArgumentTypeError(e)

    return int_value


def define_alg(func):
    def wrapper(*args, **kwargs):
        algs = {"DFS": alg_DFS,
                "Prim": alg_Prim}
        args[0].algorithm = algs[args[0].algorithm]
        return func(*args, **kwargs)
    return wrapper
    

@define_alg
def play_game(args):
    print("Start game")
    start_game(args.algorithm, args.size[0], args.size[1],
                   args.filename, args.solution, 
                   args.players, args.bonuses, args.velocity)
        
@define_alg
def start_game_on_server(args):
    print("Start server")
    start_server(args.algorithm, args.size[0], args.size[1],
                     args.filename, args.solution, 
                     args.bonuses, args.velocity)
    
    
def play_online_game(args):
    print("Start online game")
    start_client(args.iphost)
    
@define_alg
def generator(args):
    print("Start generator")
    start_generator(args.algorithm, args.size[0], args.size[1], 
                    args.solution, args.filename, 
                    args.save_maze)
    


def parse_maze_settings(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-s", "--size", 
        help="Enter the size of the maze width, height", 
        nargs=2, type=check, 
        default=[10, 10], metavar=('w', 'h'))
    
    group.add_argument(
        '-f', "--filename", 
        help="Enter <filename.txt> to download the maze", 
        type=str)
    
    parser.add_argument(
        "-a", "--algorithm", 
        help="Select the generation algorithm", 
        type=str, choices=['DFS', 'Prim'], default='DFS')
    
    parser.add_argument(
        "-sol", "--solution", 
        help="Maze with a solution", 
        action='store_true', default=False)

def parse_game_settings(parser, is_online_game=False):
    if not is_online_game:
        parser.add_argument(
            "-p", "--players", 
            help="Number of players", 
            type=int, choices=[1, 2], default=1)
        
    parser.add_argument(
        "-b", "--bonuses", 
        help="Game with bonuses:\n"
        "\t1) speed up\n"
        "\t2) speed down\n"
        "\t3) telepot\n"
        "\t4) breach wall: press LSHIFT/RSHIFT",
        action='store_true', default=False)
    
    parser.add_argument(
        "-v", "--velocity",
        help="Player speed",
        type=int, choices=[2, 3, 4, 5],
        default=2)


def parser_args():
    parser = argparse.ArgumentParser(
        prog="'Maze Generator'",
        formatter_class=argparse.RawTextHelpFormatter, 
        description="Description:\n"
        "1) Generate mazes of different sizes, with or without a solution\n"
        "2) Save/load maze to/from txt format files\n"
        "3) Display maze in console using characters: '|', '---', '+'\n"
        "4) Start game after passing maze\n"
        "5) The game supports 2 players\n"
        "6) The game can be played with or without bonuses\n"
        "7) You can play online by connecting to the same network (Wi-Fi)")
    
    
    subparsers = parser.add_subparsers(
        title='mods', 
        help='game/generator/online_game programme mode', 
        required=True)
    
    parser_game = subparsers.add_parser(
        "game", 
        help="Game mode",
        formatter_class=argparse.RawTextHelpFormatter)
    
    parse_maze_settings(parser_game)

    parse_game_settings(parser_game)
      
    parser_game.set_defaults(func=play_game)


    parser_online_game = subparsers.add_parser(
        "online_game", 
        help="Online game mode (to play create server)", 
        formatter_class=argparse.RawTextHelpFormatter)
    subparsers_online_game = parser_online_game.add_subparsers(
        title='mods', 
        help='server/player', 
        required=True)

    parser_server = subparsers_online_game.add_parser(
        "server", 
        help="Server creates game sessions with certain parameters", 
        formatter_class=argparse.RawTextHelpFormatter)
    
    parse_maze_settings(parser_server)

    parse_game_settings(parser_server, is_online_game=True)
    
    parser_server.set_defaults(func=start_game_on_server)


    parser_player = subparsers_online_game.add_parser(
        "player", 
        help="Connects to server and waits for the second player", 
        formatter_class=argparse.RawTextHelpFormatter)  

    parser_player.add_argument(
        "-iph", "--iphost",
        help="Connects to server by this ip: <XXX.XXX.XXX.X>",
        type=str, required=True)
    parser_player.set_defaults(func=play_online_game)


    parser_generator = subparsers.add_parser(
        "generator", 
        help="Maze generation mode")
    parse_maze_settings(parser_generator)

    parser_generator.add_argument(
        "-sm", "--save_maze", 
        help="Save the maze in txt format", 
        action='store_true')

    parser_generator.set_defaults(func=generator)


    args = parser.parse_args()
    args.func(args)
