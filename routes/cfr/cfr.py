import json
import codecs
import os
import networkx as nx
import sys
import random
import math
from array import *
import numpy as np


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

def find_allowed_cut(G: nx.DiGraph, srcs, dsts, banned_set):
    cutjs = {}
    large_value = int(1e9)
    G.add_node('super_source')
    G.add_node('super_sink')
    for src in srcs:
        G.add_edge('super_source', src, capacity=int(large_value))
    for dst in dsts:
        G.add_edge(dst, 'super_sink', capacity=int(large_value))
    banned = []
    if banned_set != '-1':
        # banned = list(map(str, banned_set.split(')('))
        for tup in banned_set.split(')('):
            tup = tup.replace(')','').replace('(','')
            banned.append(tuple(tup.split(',')))

        for i in range(len(banned)):
            G[banned[i][0]][banned[i][1]]['capacity'] = large_value
    # print(banned[0])
    while True:
        cv, part = nx.minimum_cut(G, 'super_source', 'super_sink')
        print(cv)
        if cv >= large_value:
            print('The banned edges make it impossible to cut the graph!')
            with open('C:/Users/DELL/Documents/Research_Express/routes/iterative_cut/cutset.json', 'w') as outfile:
                json.dump({'impossible': 'yes'}, outfile)
            return None
        reach, not_reach = part
        cutset = make_cutset(G, reach, not_reach)
        if cv == 0:
            print('The graph is already cut.')
            with open('C:/Users/DELL/Documents/Research_Express/routes/iterative_cut/cutset.json', 'w') as outfile:
                json.dump({'alreadyCut': 'yes'}, outfile)
            return None
        cutset = list(cutset)
        print('Here is the cut I found:')
        for i in range(len(cutset)):
            cutjs[i] = cutset[i]
        with open('C:/Users/DELL/Documents/Research_Express/routes/iterative_cut/cutset.json', 'w') as outfile:
            json.dump(cutjs, outfile)
        return cutset
        # print('Please enter a single line containing either a space separated list of options indicating edges that cannot be deleted, or just -1 to indicate that these edges are OK to delete.')
        # nums = list(map(int, input().split()))
        # if nums[0] == -1:
        #     return cutset
        # for i in nums:
        #     banned.append(cutset[i])
        #     G[cutset[i][0]][cutset[i][1]]['capacity'] = large_value

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
    r = random.uniform(0, 1)
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
    return strategy

def getreward_v4(action,topology,strategy,default_strategy,currentNode,targetNode):
    reward = 0
    chosenPath = [currentNode, action]
    reward = reward + topology[chosenPath[len(chosenPath) - 2]][action]
    currentNode = action

    if currentNode == targetNode:
        reward = 1/reward
    else:
        while currentNode != targetNode:
            currentStrategy = strategy[currentNode]
            for i in range(len(currentStrategy)):
                if currentStrategy[i] != 0 and i in chosenPath:
                    currentStrategy[i] = 0
            if sum(currentStrategy) > 0:
                currentStrategy = [item / sum(currentStrategy) for item in currentStrategy]
            else:
                currentStrategy = default_strategy[currentNode]

            action = getaction(len(currentStrategy), currentStrategy)
            chosenPath.append(action)
            reward = reward + topology[currentNode][action]
            currentNode = action
            if currentNode == targetNode:
                reward = 1 / reward
                break
    return reward




def main():
    input_path = 'C:/Users/DELL/Downloads/bloodHound/BloodHound-Tools/DBCreator/'
    output_path = './parsed_graph'
    edges = set()
    node_meta = dict()
    for file in os.listdir(input_path):
        if file.endswith('.json'):
            meta, e = parse_file(input_path + file)
            edges.update(e)
            node_meta.update(meta)

    # Remove edges between nodes that do not exist
    edges = set(filter(lambda e: e.src in node_meta and e.dst in node_meta, edges))
    edges = list(edges)
    print(edges[0])
    print('Json files parsed...')
    print("Total Edges: ", len(edges))
    print("Total Nodes: ", len(node_meta))
    # print(node_meta['S-1-5-21-3575477103-1058849377-3253337160-1000'])
    dom_admin = 'S-1-5-21-3575477103-1058849377-3253337160-512'
    # dom_admin = 'S-1-5-21-1390582872-192029990-4074164785-512'
    # S-1-5-21-1390582872-192029990-4074164785-512
    # from edges and nodes, build a graph (like Sigma)
    G = build_networkx_DiGraph(edges)

    # Render a virtual graph (takes too long), can be ignored
    # nx.draw(G, with_labels=1)

    print('Networkx graph built')

    #id's of 2 nodes
    entry = 0
    target = 3


    # entryNode = int(input())
    # targetNode = int(input())
    entryNode = 0
    targetNode = 3
    # entryNode
    topology = (nx.to_numpy_matrix(G)).tolist()
    topology = [[0,0,1,0], [0,0,0,0], [0,0,0,1], [0,0,0,0]]
    print("convert to matrix")
    for i in range(len(topology)):
        topology[i][i] = 0
    print(1)
    #Initialization for CFR
    strategy = topology
    for i in range(len(strategy)):
        for j in range(len(strategy)):
            if strategy[i][j] != 0:
                strategy[i][j] = 1
    print(2)
    print(len(strategy))
    for i in range(len(strategy)):
        if sum(strategy[i]) != 0:
            print(i)
            #strategy(i,:) = strategy(i,:)./sum(strategy(i,:));
            strategy[i] = [item / sum(strategy[i]) for item in strategy[i]]
    print(3)
    defaultStrategy = strategy
    # regret_sum = zeros(length(topology),length(topology))
    regret_sum = [ [0] * len(topology) for _ in range(len(topology))]
    print(4)
    print("main")
    # Main algorithm
    repeat = 10

    utility = np.zeros(len(topology))
    for episodes in range(repeat):
        print(episodes)
    #Exploration
        if episodes < repeat - 1:
            #not the final one
            strategy = defaultStrategy
        else:
            for i in range(len(defaultStrategy)):
                if sum(regret_sum[i]) > 0:
                    strategy[i] = [item / sum(regret_sum[i]) for item in regret_sum[i]]
                else:
                    strategy[i] = defaultStrategy[i]

    ###
        reward = 0
        currentNode = entryNode
        chosenPath = [currentNode]

        while currentNode != targetNode:
    #Compute the expected utility using simulation
            utility = np.zeros(len(topology)).tolist()
            for a in range(len(defaultStrategy)):
                if defaultStrategy[currentNode][a] != 0:
                    utility[a] = getreward_v4(a,topology,strategy,defaultStrategy,currentNode,targetNode)
    # Compute the regret_sum
            for a in range(len(defaultStrategy)):
                if defaultStrategy[currentNode][a] != 0:
                    regret_sum[currentNode][a] = regret_sum[currentNode][a] + utility[a] - sum(np.multiply(utility, defaultStrategy[currentNode]))
            # regret_sum[currentNode] = max(regret_sum(currentNode,:),0);
            for index in range(len(regret_sum[currentNode])):
                if regret_sum[currentNode][index] < 0:
                    regret_sum[currentNode][index] = 0

    # Update strategy based on regret minimization
            if sum(regret_sum[currentNode]) > 0:
                strategy[currentNode] = getstrategy(len(defaultStrategy),regret_sum[currentNode],strategy[currentNode])
            else:
                strategy[currentNode] = defaultStrategy[currentNode]
    # Update current strategy
            currentStrategy = strategy[currentNode]
            for i in range(len(currentStrategy)):
                if currentStrategy[i] != 0 and i in chosenPath:
                    currentStrategy[i] = 0
            if sum(currentStrategy) == 0:
                currentStrategy = defaultStrategy[currentNode]
                for i in range(len(defaultStrategy)):
                    if currentStrategy[i] != 0 and i in chosenPath:
                        currentStrategy[i] = 0
                if sum(currentStrategy) > 0:
                    currentStrategy = [item /sum(currentStrategy) for item in currentStrategy]
                else:
                    currentStrategy = defaultStrategy[currentNode]
                    for i in range(len(defaultStrategy)):
                        if currentStrategy[i] != 0 and i == chosenPath[len(chosenPath) - 2]:
                            currentStrategy[i] = 0
                    if sum(currentStrategy) > 0:
                        currentStrategy = [item /sum(currentStrategy) for item in currentStrategy]
                    else:
                        currentStrategy = defaultStrategy[currentNode]
            else:
                currentStrategy = [item /sum(currentStrategy) for item in currentStrategy]
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

            currentNode = action

    #STOP
            if currentNode == targetNode:
                break
    print(chosenPath)


if __name__ == "__main__":
    main()

# res = next(iter(G.edges.data()))
#     print(str(next(iter(G.edges.data()))))
#     print("source: ", str(next(iter(G.edges.data()))[0]))
#     print("dest: ", str(next(iter(G.edges.data()))[1]))
#     print(str(next(iter(G.edges.data()))))
#     print(str(next(iter(G.edges.data()))))