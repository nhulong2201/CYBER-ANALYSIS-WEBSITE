import networkx as nx

infile = open('matlab.txt','r')
numbers = []
for line in infile:
    numbers.append([float(val) for val in line.split('\t')])
infile.close()

edges = []
for i in range(len(numbers)):
    for j in range(len(numbers)):
        if numbers[i][j] != 0:
            temp = (i, j, {'weight':numbers[i][j]})
            edges.append(temp)


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


G = nx.Graph()
for i in range(43):
    G.add_node(i)
G.add_edges_from(edges)

pos = nx.planar_layout(G)

# This will give us all the shortest paths from node 1 using the weights from the edges.
p1 = nx.shortest_path(G, source=0, weight='weight')

# This will give us the shortest path from node 1 to node 6.
p1to6 = nx.shortest_path(G, source=0, target=38, weight='weight')

# This will give us the length of the shortest path from node 1 to node 6.
length = nx.shortest_path_length(G, source=0, target=38, weight='weight')

print("All shortest paths from 0: ", p1)
print("Shortest path from 0 to 38: ", p1to6)
print("Length of the shortest path: ", length)

# temp = (0, 1, {'weight':4})
# print(temp)
# print("temp:")