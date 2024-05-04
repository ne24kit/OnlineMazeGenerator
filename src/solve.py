import heapq


class Node:
    def __init__(self, x, y):
        self.x = x  # x coordinate of the node on the map
        self.y = y  # y coordinate of the node on the map
        self.g = 0  # distance from start node to current node
        self.h = 0  # distance from current node to target node
        self.f = 0  # sum of g and h
        self.parent = None  # parent node, used for path recovery

    # redefine the comparison operator to compare nodes
    def __lt__(self, other):
        return self.f < other.f

    # redefine the equality operator to compare nodes
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    # redefine the hash operator
    def __hash__(self):
        return hash((self.x, self.y))

# function to find the path using algorithm A*
def astar(start, end, maze):

    start_node = Node(start[0], start[1])
    end_node = Node(end[0], end[1])

    # initialise the priority queue
    open_list = []
    heapq.heappush(open_list, start_node)

    # initialise the set of visited nodes
    closed_set = set()

    while open_list:
        # retrieve the node with the lowest score f
        current_node = heapq.heappop(open_list)
   
        if current_node == end_node:
            # reconstruct the path from the end node to the start node
            path = []
            while current_node is not None:
                path.append((current_node.x, current_node.y))
                current_node = current_node.parent
            return path[::-1]

        # add the current node to the set of visited nodes
        closed_set.add(current_node)

        # Get the neighbouring nodes
        d_x_y = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        neighbors = []
        for dx, dy in d_x_y:
            x = current_node.x + dx
            y = current_node.y + dy
            # ignore nodes outside the map
            if x < 0 or x >= len(maze) or y < 0 or y >= len(maze[0]):
                continue
            # ignore the obstacles
            if maze[x][y]:
                continue
            # create a new node and add it to the list of neighbours
            neighbor = Node(x, y)
            neighbors.append(neighbor)

        for neighbor in neighbors:
            # visited neighbouring nodes skipped
            if neighbor in closed_set:
                continue

            new_g = current_node.g + 1

            # if the neighbouring node is already in the priority queue
            if nfo := next((n for n in open_list if n == neighbor), None):
                if new_g < nfo.g:
                    # update the values of g, h and f
                    nfo.g = new_g
                    nfo.h = (end_node.x - nfo.x) ** 2 + \
                        (end_node.y - nfo.y) ** 2
                    nfo.f = nfo.g + nfo.h
                    nfo.parent = current_node
                    # update the priority of the neighbouring node
                    heapq.heapify(open_list)
            else:
                # add a neighbouring node to the priority queue
                # calculate the values of g, h and f
                neighbor.g = new_g
                neighbor.h = (end_node.x - neighbor.x) ** 2 + \
                    (end_node.y - neighbor.y) ** 2
                neighbor.f = neighbor.g + neighbor.h
                neighbor.parent = current_node
                heapq.heappush(open_list, neighbor)

    # if the destination node is unreachable, return None
    return None