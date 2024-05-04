import argparse
from src.game import start_game
from src.network_utils import start_client, start_server 
from src.maze import start_generator, alg_DFS, alg_Prim

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


def play_game(args):
    print("Start game")
    if args.server:
        start_server(args.algorithm, args.size[0], args.size[1],
                     args.filename, args.solution, 
                     args.players, args.bonuses, args.velocity)
    else:
        start_game(args.algorithm, args.size[0], args.size[1],
                   args.filename, args.solution, 
                   args.players, args.bonuses, args.velocity)
    
    
def play_online_game(args):
    start_client()
    

def generator(args):
    print("Start generator")

    start_generator(args.algorithm, args.size[0], args.size[1], 
                    args.solution, args.filename, 
                    args.save_maze)
    
def parser_args():
    parser = argparse.ArgumentParser(
        prog="'Maze Generator'",
        formatter_class=argparse.RawTextHelpFormatter, 
        description="Description:\n"
        "1) Generate mazes of different sizes, with or without a solution\n"
        "2) Save/load the maze to/from txt format files\n"
        "3) Display the maze in the console using special characters: '|', '---', '+'\n"
        "4) Start the game after passing the maze\n"
        "5) The game supports 2 players\n"
        "6) The game can be played with or without bonuses")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-s", "--size", 
                       help="Enter the size of the maze width, height", 
                       nargs=2, type=check, 
                       default=[10, 10], metavar=('w', 'h'))
    group.add_argument('-f', "--filename", 
                       help="Enter <filename.txt> to download the maze", 
                       type=str)
    
    parser.add_argument("-a", "--algorithm", 
                        help="Select the generation algorithm", 
                        type=str, choices=['DFS', 'Prim'], default='DFS')
    parser.add_argument("-sol", "--solution", 
                        help="Maze with a solution", 
                        action='store_true', default=False)
    subparsers = parser.add_subparsers(title='mods', 
                                       help='Game/generator programme mode', 
                                       required=True)

    parser_game = subparsers.add_parser(
        "game", 
        help="Game mode", 
        formatter_class=argparse.RawTextHelpFormatter)
    parser_game.add_argument("-p", "--players", 
                             help="Number of players", 
                             type=int, choices=[1, 2], default=1)
    parser_game.add_argument("-b", "--bonuses", 
                             help="Game with bonuses:\n"
                             "\t1) speed up\n"
                             "\t2) speed down\n"
                             "\t3) telepot\n"
                             "\t4) breach wall: press LSHIFT/RSHIFT",
                             action='store_true', default=False)
    parser_game.add_argument("-v", "--velocity",
                             help="Player speed",
                             type=int, choices=[2, 3, 4, 5],
                             default=2)
    parser_game.add_argument("-serv", "--server",
                             help="Create server to play online game",
                             action='store_true', default=False
                             )
    
    parser_game.set_defaults(func=play_game)


    parser_online_game = subparsers.add_parser(
        "online_game", 
        help="Online game mode (to play create server [-serv] in mode \"game\")", 
        formatter_class=argparse.RawTextHelpFormatter)
    parser_online_game.set_defaults(func=play_online_game)


    parser_generator = subparsers.add_parser("generator", 
                                             help="Maze generation mode")
    parser_generator.add_argument("-sm", "--save_maze", 
                                  help="Save the maze in txt format", 
                                  action='store_true')

    parser_generator.set_defaults(func=generator)

    args = parser.parse_args()
    algs = {"DFS": alg_DFS,
            "Prim": alg_Prim}
    args.algorithm = algs[args.algorithm]
    args.func(args)
