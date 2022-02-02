import json
import networkx as nx
import numpy as np
def assign_costs(edge_name):
    edges = {
        "MemberOf": 5,
        "Contain": 5,
        "GpLink": 5,
        "AdminTo": 20,
        "HasSession": 40,
        "TrustedBy": 100,
        "CanRDP": 100,
        "CanPSRemote": 100,
        "ExecuteDCOM": 100,
        "AllowedToDelegate": 100,
        "AllowedToAct": 100,
        "AddAllowedToACT": 100,
        "GetChanges": 100,
        "GetChangesAll": 100
    }

    return edges.get(edge_name, 30)

# infile = open('matlab.txt','r')
# numbers = []
# for line in infile:
#     numbers.append([float(val) for val in line.split('\t')])
# infile.close()

#--------------------------------------------------------
input_path = 'C:/Users/DELL/Documents/Research_Express/routes/cfr/all.json'
f = open(input_path)
data = json.load(f)
edges = list(data["edges"])
print("1st edge: ", edges[0])
print("last edge: ", edges[2057])
result = []

n_nodes = 1554
edges_type = []

# print(topology)
count = 0
topology=[ [0] * n_nodes for _ in range(n_nodes)]
for edge in edges:
    # if edge['label'] not in edges_type:
    #     edges_type.append(edge['label'])
    i = int(edge["start"]["id"])
    j = int(edge["end"]["id"])
    if topology[i][j] != 0 and topology[i][j] > (assign_costs(edge['label']) / 100):
        topology[i][j] = assign_costs(edge['label']) / 100
    else:
        topology[i][j] = assign_costs(edge['label']) / 100
    # topology[i][j] = 1

for i in range(len(topology)):
    topology[i][i] = 0
print(topology[150][524])


#---------------------------------------------------------
edges = []
for i in range(n_nodes):
    for j in range(n_nodes):
        if topology[i][j] != 0:
            temp = (i, j, {'weight':topology[i][j]})
            edges.append(temp)
#--------------------------------------------------------
# for edge in edges:
#     if edge[0] == 150:
#         print("Here we found: ", edge)


# edges = [(1,2, {'weight':4}),
#         (1,3,{'weight':2}),
#         (2,3,{'weight':1}),
#         (2,4, {'weight':5}),
#         (3,4, {'weight':8}),
#         (3,5, {'weight':10}),
#         (4,5,{'weight':2}),
#         (4,6,{'weight':8}),
#         (5,6,{'weight':5})]
# edge_labels = {(1,2):4, (1,3):2, (2,3):1, (2,4):5, (3,4):8, (3,5):10, (4,5):2, (4,6):8, (5,6):5}


G = nx.DiGraph()
# for i in range(n_nodes):
#     G.add_node(i)
G.add_edges_from(edges)

# pos = nx.planar_layout(G)

# This will give us all the shortest paths from node 1 using the weights from the edges.
# p1 = nx.shortest_path(G, source=150, weight='weight')

# This will give us the shortest path from node 1 to node 6.
p1to6 = nx.shortest_path(G, source=237, target=524, weight='weight')

# This will give us the length of the shortest path from node 1 to node 6.
length = nx.shortest_path_length(G, source=237, target=524, weight='weight')

# print("All shortest paths from 0: ", p1)
print("Shortest path from 237 to 524: ", p1to6)
print("Length of the shortest path: ", length)

pathGraph = nx.path_graph(p1to6)  # does not pass edges attributes

# Read attributes from each edge
for ea in pathGraph.edges():
    #print from_node, to_node, edge's attributes
    print(ea, G.edges[ea[0], ea[1]])
# temp = (0, 1, {'weight':4})
# print(temp)
# print("temp:")