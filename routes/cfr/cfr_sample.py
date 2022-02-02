import json
import codecs
import os
import networkx as nx
import sys
import random
import math
from array import *
from networkx.generators.trees import prefix_tree
import numpy as np
import itertools


class Edge:
    def __init__(self, src, dst, type):
        self.src = src
        self.dst = dst
        self.type = type
        self.time = None

    def set_time(self, time):
        self.time = time

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.src == other.src and self.dst == other.dst and self.type == other.type and self.time == other.time

    def __hash__(self):
        return hash((self.src, self.dst, self.type, self.time))

def extract_aces(json):
    edges = set()
    for ace in json['Aces']:
        edges.add(Edge(ace['PrincipalSID'], json['ObjectIdentifier'], ace['RightName']))
    return edges

def extract_members(json):
    edges = set()
    for member in json['Members']:
        edges.add(Edge(member['MemberId'], json['ObjectIdentifier'], 'MemberOf'))
    return edges

def extract_sessions(json):
    edges = set()
    for sess in json['Sessions']:
        edges.add(Edge(sess['ComputerId'], sess['UserId'], 'HasSession'))
    return edges

def extract_delegate(json):
    edges = set()
    for delegate in json['AllowedToDelegate']:
        edges.add(Edge(delegate, json['ObjectIdentifier'], 'AllowedToDelegate'))
    return edges

def extract_local_admins(json):
    edges = set()
    for admin in json['LocalAdmins']:
        edges.add(Edge(admin['MemberId'], json['ObjectIdentifier'], 'AdminTo'))
    return edges

def extract_rdp_users(json):
    edges = set()
    for rdp in json['RemoteDesktopUsers']:
        edges.add(Edge(rdp['MemberId'], json['ObjectIdentifier'], 'CanRDP'))
    return edges

def extract_execute_dcom(json):
    edges = set()
    for dcom in json['DcomUsers']:
        edges.add(Edge(dcom['MemberId'], json['ObjectIdentifier'], 'ExecuteDCOM'))
    return edges

def extract_ps_remote(json):
    edges = set()
    for psr in json['PSRemoteUsers']:
        edges.add(Edge(psr['MemberId'], json['ObjectIdentifier'], 'CanPSRemote'))
    return edges

def extract_allowed_to_act(json):
    edges = set()
    for act in json['AllowedToAct']:
        edges.add(Edge(act['MemberId'], json['ObjectIdentifier'], 'AllowedToAct'))
    return edges

def extract_sid_history(json):
    edges = set()
    for sid in json['HasSIDHistory']:
        edges.add(Edge(json['ObjectIdentifier'], sid['MemberId'], 'AllowedToAct'))
    return edges

def extract_spn(json):
    edges = set()
    for spn in json['SPNTargets']:
        edges.add(Edge(json['ObjectIdentifier'], spn['ComputerSid'], spn['Service']))
    return edges

def parse_users(json):
    edges = set()
    node_meta = dict()
    if 'users' not in json:
        return node_meta, edges
    for user in json['users']:
        node_meta[user['ObjectIdentifier']] = ('User', user['Properties'])
        if user['PrimaryGroupSid'] != None:
            edges.add(Edge(user['ObjectIdentifier'], user['PrimaryGroupSid'], 'MemberOf'))
        edges.update(extract_aces(user))
        edges.update(extract_delegate(user))
        edges.update(extract_sid_history(user))
        edges.update(extract_spn(user))
    return node_meta, edges

def parse_groups(json):
    edges = set()
    node_meta = dict()
    if 'groups' not in json:
        return node_meta, edges
    for group in json['groups']:
        node_meta[group['ObjectIdentifier']] = ('Group', group['Properties'])
        edges.update(extract_aces(group))
        edges.update(extract_members(group))
    return node_meta, edges


def parse_computers(json):
    edges = set()
    node_meta = dict()
    if 'computers' not in json:
        return node_meta, edges
    for computer in json['computers']:
        node_meta[computer['ObjectIdentifier']] = ('Computer', computer['Properties'])
        if computer['PrimaryGroupSid'] != None:
            edges.add(Edge(computer['ObjectIdentifier'], computer['PrimaryGroupSid'], 'MemberOf'))
        edges.update(extract_sessions(computer))
        edges.update(extract_local_admins(computer))
        edges.update(extract_rdp_users(computer))
        edges.update(extract_aces(computer))
        edges.update(extract_delegate(computer))
        edges.update(extract_allowed_to_act(computer))
        edges.update(extract_ps_remote(computer))
        edges.update(extract_execute_dcom(computer))
    return node_meta, edges

def get_used_fields(json_node, fields, field=''):
    if type(json_node) is dict:
        for field in json_node.keys():
            get_used_fields(json_node[field], fields, field)
    elif type(json_node) is list:
        if len(json_node) > 0:
            fields.add(field)
            for elem in json_node:
                get_used_fields(elem, fields)

def parse_file(filename):
    edges = set()
    node_meta = dict()
    print(filename)
    # text = codecs.decode(open(filename).read().encode(), 'utf-8-sig')
    # with open("C:/Users/DELL/Downloads/bloodHound/BloodHound-Tools/DBCreator/20210921092626_computers.json", encoding='utf-8-sig', errors='ignore') as json_data:
    #     j = json.load(json_data)
    with open(filename, encoding='utf-8-sig') as json_file:
        j=json.load(json_file)

    # j = json.loads(text)
    fields = set()
    get_used_fields(j, fields)
    print("Parsing " + filename)
    for field in fields:
        print("\tContains field: ", field)
    for meta, e in [parse_users(j), parse_groups(j), parse_computers(j)]:
        node_meta.update(meta)
        edges.update(e)
    mod_time = os.path.getmtime(filename)
    for e in edges:
        e.set_time(mod_time)
    return (node_meta, edges)

def build_networkx_DiGraph(edges):
    G = nx.DiGraph()
    for e in edges:
        if e.src == None or e.dst == None:
            print(e.type, e.src, e.dst)
        G.add_edge(e.src, e.dst, capacity=1, type=e.type)
    return G

def make_cutset(G: nx.DiGraph, reach, not_reach):
    cutset = set()
    not_reach = set(not_reach)
    for src in reach:
        for dst in G.neighbors(src):
            if dst in not_reach:
                cutset.add((src, dst))
    return cutset

def transitive_users(G: nx.DiGraph, dom_admin, node_meta):
    stk = [dom_admin]
    vis = set()
    R = G.reverse()
    while len(stk) > 0:
        at = stk.pop()
        for n in R.neighbors(at):
            if node_meta[n][0] not in ['User', 'Group'] or n in vis:
                continue
            stk.append(n)
            vis.add(n)
    return vis

def getaction(num_action, strategy):
    a = 0
    cum_prob = 0
    # r = random.uniform(0, 1)
    r = 0.43
    while True:
        if a > num_action - 2:
            break
        cum_prob = cum_prob + strategy[a]
        if r < cum_prob:
            break
        a = a + 1
    return a

def getstrategy(num_actions,regret_sum,strategy):
    norm_sum = 0
    old_strategy = strategy
    for a in range(num_actions):
        if regret_sum[a] > 0:
            strategy[a] = regret_sum[a]
        else:
            strategy[a] = 0
        norm_sum = norm_sum + strategy[a]
    for a in range(num_actions):
        if norm_sum>0:
            strategy[a]=strategy[a]/norm_sum
        else:
            strategy[a]=old_strategy[a]
    print(12)
    return strategy

def getreward_v4(action,topology,strategy,default_strategy,currentNode,targetNode):
    reward = 0
    chosenPath = [currentNode, action]
    reward = reward + topology[chosenPath[len(chosenPath) - 2]][action]
    currentNode = action
    parentNode = 0
    print("check reward")
    time = 0
    if currentNode == targetNode:
        reward = 1/reward
    else:
        while currentNode != targetNode:
            if time == 0:
                if currentNode == len(topology) - 1:
                    time += 1
                    print("Node now 0: ", currentNode)
            elif time == 1:
                if currentNode == len(topology) - 1:
                    time += 1
                    print("Node now 1: ", currentNode)
                else:
                    time = 0
            elif time == 2:
                if currentNode == len(topology) - 1:
                    print("Time breakkkkkkkkkk", time)
                    break
                else:
                    time = 0
            print("Pre CurrentNode", currentNode)
            currentStrategy = strategy[currentNode]
            # print("PRE current: ", currentStrategy)
            print("Go in with current ", currentNode, " and target ", targetNode)
            for i in range(len(currentStrategy)):
                if currentStrategy[i] != 0 and i in chosenPath:
                    currentStrategy[i] = 0
            total = sum(currentStrategy)
            if total > 0:
                currentStrategy = [item / total for item in currentStrategy]
            else:
                currentStrategy = default_strategy[currentNode]
            # print("Current Strategy: ", currentStrategy)
            action = getaction(len(currentStrategy), currentStrategy)
            print("Action: ", action)
            chosenPath.append(action)
            reward = reward + topology[currentNode][action]
            parentNode = currentNode
            currentNode = action
            print("CurrentNode ", currentNode)
            if currentNode == targetNode:
                reward = 1 / reward
                break
    return reward




def main():
    # G=nx.DiGraph()
    # G.add_edges_from([(1,2),(4,1),(2,3)])
    # print(G.edges.data())
    # print(nx.to_numpy_matrix(G))
    # input_path = 'C:/Users/DELL/Documents/Research_Express/routescfr/test2.json'
    # f = open(input_path)
    # data = json.load(f)
    # edges = list(data["edges"])


    dom_admin = 'S-1-5-21-3575477103-1058849377-3253337160-512'


    n_nodes = 1553
    # topology = np.zeros((n_nodes,n_nodes), dtype=int)

    chosenPath = []

    # print(topology)
    # topology=list([list(item) for item in topology])
    # for edge in edges:
    #     i = int(edge["start"]["id"]) - 2909
    #     j = int(edge["end"]["id"]) - 2909
    #     topology[i][j] = 1
    # print("TESTINGGGG---- ")
    # print("Source to DC: ", topology[])

    # topology = (nx.to_numpy_matrix(G)).tolist()



    # topology = [[0,1,1,0], [0,0,1,0], [0,0,0,1], [0,0,0,0]]
    # topology = [[0,1,1,0], [0,0,1,0], [0,1,0,1], [0,0,1,0]]
    # topology = [[0,1,1,0], [0,0,1,0], [1,0,0,1], [0,0,1,0]]
    # topology = [[0,0,1,0], [0,0,0,0], [0,0,0,1], [0,0,0,0]]
    topology = [[0,1,1,0], [0,0,0,0], [0,0,0,1], [1,0,0,0]]
    # print("Topology: ", topology)


    # topology = (nx.to_numpy_matrix(G)).tolist()
    # print("convert to matrix")
    for i in range(len(topology)):
        topology[i][i] = 0
    print(1)

    # entryNode = int(nodes[source])
    # targetNode = int(nodes[dest])

    entryNode = 0
    targetNode = 3

    #Initialization for CFR
    strategy = topology
    for i in range(len(strategy)):
        for j in range(len(strategy)):
            if strategy[i][j] != 0:
                strategy[i][j] = 1
    print(2)
    print(len(strategy))
    for i in range(len(strategy)):
        total = sum(strategy[i])
        if total != 0:
            #strategy(i,:) = strategy(i,:)./sum(strategy(i,:));
            strategy[i] = [item / total for item in strategy[i]]
    print(3)
    defaultStrategy = strategy
    # print("Default: ", defaultStrategy)
    # regret_sum = zeros(length(topology),length(topology))
    regret_sum = [ [0] * len(topology) for _ in range(len(topology))]
    print(4)
    print("main")
    # Main algorithm
    repeat = 5

    # utility = np.zeros(len(topology))
    utility = [0] * len(topology)
    # print("Utility: ", utility)

    for episodes in range(repeat):
        print("--------------------Episodesssss", episodes)
    #Exploration
        if episodes < repeat - 1:
            #not the final one
            strategy = defaultStrategy
        else:
            for i in range(len(defaultStrategy)):
                total = sum(regret_sum[i])
                if total > 0:
                    strategy[i] = [item / total for item in regret_sum[i]]
                else:
                    strategy[i] = defaultStrategy[i]

    ###
        reward = 0
        currentNode = entryNode
        chosenPath = [currentNode]

        count = 0
        time = 0

        while currentNode != targetNode:
    #Compute the expected utility using simulation
            if time == 0:
                if currentNode == len(topology) - 1:
                    time += 1

            elif time == 1:
                if currentNode == len(topology) - 1:
                    time += 1
                else:
                    time = 0

            elif time == 2:
                if currentNode == len(topology) - 1:
                    print("Time breakkkkkkkkkk", time)
                    break
                else:
                    time = 0
            print("Count: ", count)
            print("CURRENT NODESSSS: ", currentNode)
            print("Path: ", chosenPath)
            utility = np.zeros(len(topology)).tolist()
            for a in range(len(defaultStrategy)):
                if defaultStrategy[currentNode][a] != 0:
                    utility[a] = getreward_v4(a,topology,strategy,defaultStrategy,currentNode,targetNode)
            print("Reward")
    # Compute the regret_sum
            for a in range(len(defaultStrategy)):
                if defaultStrategy[currentNode][a] != 0:
                    regret_sum[currentNode][a] = regret_sum[currentNode][a] + utility[a] - sum(np.multiply(utility, defaultStrategy[currentNode]))
            # regret_sum[currentNode] = max(regret_sum(currentNode,:),0);
            for index in range(len(regret_sum[currentNode])):
                if regret_sum[currentNode][index] < 0:
                    regret_sum[currentNode][index] = 0
            print("Regret sum")
    # Update strategy based on regret minimization
            if sum(regret_sum[currentNode]) > 0:
                strategy[currentNode] = getstrategy(len(defaultStrategy),regret_sum[currentNode],strategy[currentNode])
            else:
                strategy[currentNode] = defaultStrategy[currentNode]
            print("Minimization")
    # Update current strategy
            currentStrategy = strategy[currentNode]
            for i in range(len(currentStrategy)):
                if currentStrategy[i] != 0 and i in chosenPath:
                    currentStrategy[i] = 0

            total = sum(currentStrategy)
            if total == 0:
                currentStrategy = defaultStrategy[currentNode]
                for i in range(len(defaultStrategy)):
                    if currentStrategy[i] != 0 and i in chosenPath:
                        currentStrategy[i] = 0
                total1 = sum(currentStrategy)
                if total1 > 0:
                    currentStrategy = [item / total1 for item in currentStrategy]
                else:
                    currentStrategy = defaultStrategy[currentNode]
                    for i in range(len(defaultStrategy)):
                        if currentStrategy[i] != 0 and i == chosenPath[len(chosenPath) - 2]:
                            currentStrategy[i] = 0

                    total2 = sum(currentStrategy)
                    if total2 > 0:
                        currentStrategy = [item / total2 for item in currentStrategy]
                    else:
                        currentStrategy = defaultStrategy[currentNode]
            else:
                currentStrategy = [item /total for item in currentStrategy]
            print("Update current")
    # Sample an action from the updated strategy
            action = getaction(len(currentStrategy),currentStrategy)
            # if episodes == repeat - 1:
            #     # finalStrategy = regret_sum(currentNode,:)./sum(regret_sum(currentNode,:));
            #     finalStrategy = [item / sum(regret_sum[currentNode]) for item in regret_sum[currentNode]]
            #     for i in range(len(defaultStrategy)):
            #         if finalStrategy[i] == max(finalStrategy):
            #             finalStrategy[i] = 1
            #         else:
            #             finalStrategy[i] = 0
            #         action = getaction(len(defaultStrategy),finalStrategy)

    # Update chosen path and plot
            chosenPath.append(action)
            print("Check Path: ", chosenPath)
            currentNode = action
            count += 1

    #STOP
            if currentNode == targetNode:
                break
        print("Chosen Path: ", chosenPath)
    print(chosenPath)
    print("Detailsssss")
    # key_list = list(nodes.keys())
    # val_list = list(nodes.values())
    # for i in chosenPath:
    #     position = val_list.index(i)
    #     print(key_list[position])


if __name__ == "__main__":
    main()

# # from edges and nodes, build a graph (like Sigma)
    # edges = [(0,1), (0,2), (1,2), (2,3)]
    # iterator = 0
    # nodes = {} #dictionary
    # graph_edges = [] #list
    # temp_list = [] #list
    # for edge in edges:
    #   temp_list.append(edge.src)
    #   temp_list.append(edge.dst)
    #   graph_edges.append(tuple(temp_list))
    #   temp_list = []

    #   #list of nodes
    #   if edge.src not in nodes.keys():
    #     nodes[edge.src] = iterator
    #     iterator += 1
    #   if edge.dst not in nodes.keys():
    #     nodes[edge.dst] = iterator
    #     iterator += 1
    # print("nodes: ", iterator)

    #######CHECK
    # for edge in edges:
    #   temp_list.append(edge[0])
    #   temp_list.append(edge[1])
    #   graph_edges.append(tuple(temp_list))
    #   temp_list = []

    #   #list of nodes
    #   if edge[0] not in nodes.keys():
    #     nodes[edge[0]] = iterator
    #     iterator += 1
    #   if edge[1] not in nodes.keys():
    #     nodes[edge[1]] = iterator
    #     iterator += 1
    # print("nodes: ", iterator)

    # # ########

    # topology=list([list(item) for item in topology])
    # for edge in graph_edges:
    #     i = int(nodes[edge[0]])
    #     j = int(nodes[edge[1]])

    #     topology[i][j] = 1
