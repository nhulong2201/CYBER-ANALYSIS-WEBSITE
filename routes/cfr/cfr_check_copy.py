from argparse import ArgumentParser
import json
import codecs
import os
import networkx as nx
import sys
import random
import math
from array import *
from networkx.classes.function import neighbors
from networkx.generators.trees import prefix_tree
import numpy as np
import itertools
import copy
import time
start = time.time()

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

def getaction_v2(num_action, currentStrategy, strategy, currentNode, parentNode, chosenPath, deadend):
    cum_prob = 0
    choices = []

    if currentNode in deadend:
        return parentNode

    for i in range(num_action):
        if currentStrategy[i] > 0 and i not in chosenPath:
            choices.append(i)
            cum_prob += currentStrategy[i]

    if cum_prob == 0:
        strategy[parentNode][currentNode] = 0
        deadend.append(currentNode)
        return parentNode
    return int(random.sample(choices, 1)[0])

def getstrategy(num_actions,regret_sum,strategy):
    norm_sum = 0
    old_strategy = strategy[:]
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

def getreward_long(currentNode, topology, targetNode, path, reward):
    if currentNode == targetNode:
        return True
    #count potential neighbors
    count = 0
    for i in range(len(topology[currentNode])):
        if topology[currentNode][i] != 0 and i not in path:
            count += 1
    # print("count = ", count)
    # impossible or possible
    if count == 0:
        reward = 0
        return reward
    else:
        for i in range(len(topology[currentNode])):
            if topology[currentNode][i] != 0 and i not in path:
                if getreward_long(i, topology, targetNode, path, reward):
                    reward += topology[currentNode][i]

                    return reward
    return 0

def getreward_v4(action,topology,strategy,default_strategy,currentNode,targetNode):
    reward = 0
    chosenPath = [currentNode, action]
    reward = reward + topology[chosenPath[len(chosenPath) - 2]][action]
    currentNode = action
    if currentNode == targetNode:
        reward = 1/reward
    else:
        while currentNode != targetNode:
            currentStrategy = strategy[currentNode][:]
            for i in range(len(currentStrategy)):
                if currentStrategy[i] != 0 and i in chosenPath:
                    currentStrategy[i] = 0
            total = sum(currentStrategy)
            if total > 0:
                currentStrategy = [item / total for item in currentStrategy]
            else:
                currentStrategy = default_strategy[currentNode][:]
            action = getaction(len(currentStrategy), currentStrategy[:])
            chosenPath.append(action)
            reward = reward + topology[currentNode][action]
            currentNode = action
            if currentNode == targetNode:
                reward = 1 / reward
                break
    return reward

def parse_args():
    parser = ArgumentParser(prog="ShotHound", prefix_chars="-/", add_help=False, description=f'Finding practical paths in BloodHound')

    parser.add_argument('entry', type = int)
    parser.add_argument('target', type = int)
    args = parser.parse_args()

    return args




def main():
    args = parse_args()
    entryNode = args.entry
    targetNode = args.target

    infile = open('C:/Users/DELL/Documents/Research_Express/routes/cfr/matlab.txt','r')
    numbers = []
    for line in infile:
        numbers.append([float(val) for val in line.split('\t')])
    infile.close()
    topology = numbers
    for i in range(len(topology)):
        topology[i][i] = 0
    result = []
    #Initialization for CFR
    strategy = [x[:] for x in topology]
    for i in range(len(strategy)):
        for j in range(len(strategy)):
            if strategy[i][j] != 0:
                strategy[i][j] = 1
    for i in range(len(strategy)):
        total = sum(strategy[i])
        if total != 0:
            #strategy(i,:) = strategy(i,:)./sum(strategy(i,:));
            strategy[i] = [item / total for item in strategy[i]]
    defaultStrategy = [x[:] for x in strategy]
    regret_sum = [ [0] * len(topology) for _ in range(len(topology))]

    # Main algorithm
    repeat = 5000

    utility = [0] * len(topology)

    for episodes in range(repeat):
        print("--------------------Episodesssss", episodes)
    #Exploration
        if episodes < repeat - 1:
            #not the final one
            strategy = [x[:] for x in defaultStrategy]
        else:
            for i in range(len(defaultStrategy)):
                total = sum(regret_sum[i])
                if total > 0:
                    strategy[i] = [item / total for item in regret_sum[i]]
                else:
                    strategy[i] = defaultStrategy[i][:]

    ###
        reward = 0
        currentNode = entryNode
        chosenPath = [currentNode]

        count = 0

        while currentNode != targetNode:
    #Compute the expected utility using simulation
            utility = np.zeros(len(topology)).tolist()
            for a in range(len(defaultStrategy)):
                if defaultStrategy[currentNode][a] != 0:
                    # utility[a] = getreward_v4(a,topology,[x[:] for x in strategy],[x[:] for x in defaultStrategy],currentNode,targetNode,chosenPath[:])
                    utility[a] = getreward_v4(a,topology,[x[:] for x in strategy],[x[:] for x in defaultStrategy],currentNode,targetNode)
    # Compute the regret_sum
            for a in range(len(defaultStrategy)):
                if defaultStrategy[currentNode][a] != 0:
                    regret_sum[currentNode][a] = regret_sum[currentNode][a] + utility[a] - sum(np.multiply(utility, defaultStrategy[currentNode][:]))
            # regret_sum[currentNode] = max(regret_sum(currentNode,:),0);
            for index in range(len(regret_sum)):
                if regret_sum[currentNode][index] < 0:
                    regret_sum[currentNode][index] = 0
    # Update strategy based on regret minimization
            if sum(regret_sum[currentNode]) > 0:
                strategy[currentNode] = getstrategy(len(defaultStrategy),regret_sum[currentNode][:],strategy[currentNode][:])
            else:
                strategy[currentNode] = defaultStrategy[currentNode][:]
    # Update current strategy
            currentStrategy = strategy[currentNode][:]
            for i in range(len(currentStrategy)):
                if currentStrategy[i] != 0 and i in chosenPath:
                    currentStrategy[i] = 0
            total = sum(currentStrategy)
            if total == 0:
                currentStrategy = defaultStrategy[currentNode][:]
                for i in range(len(defaultStrategy)):
                    if currentStrategy[i] != 0 and i in chosenPath:
                        currentStrategy[i] = 0
                total1 = sum(currentStrategy)
                if total1 > 0:
                    currentStrategy = [item / total1 for item in currentStrategy[:]]
                else:
                    currentStrategy = defaultStrategy[currentNode][:]
                    for i in range(len(defaultStrategy)):
                        if currentStrategy[i] != 0 and i == chosenPath[len(chosenPath) - 2]:
                            currentStrategy[i] = 0

                    total2 = sum(currentStrategy)
                    if total2 > 0:
                        currentStrategy = [item / total2 for item in currentStrategy[:]]
                    else:
                        currentStrategy = defaultStrategy[currentNode][:]
            else:
                currentStrategy = [item /total for item in currentStrategy[:]]

    # Sample an action from the updated strategy
            action = getaction(len(currentStrategy),currentStrategy[:])
            if episodes == repeat - 1:
                # finalStrategy = regret_sum(currentNode,:)./sum(regret_sum(currentNode,:));
                total = sum(regret_sum[currentNode])
                print("Total down: ", total)
                print(regret_sum[currentNode])
                finalStrategy = [item / total for item in regret_sum[currentNode][:]]
                for i in range(len(defaultStrategy)):
                    if finalStrategy[i] == max(finalStrategy):
                        finalStrategy[i] = 1
                    else:
                        finalStrategy[i] = 0
                    action = getaction(len(defaultStrategy),finalStrategy[:])

    # Update chosen path and plot

            chosenPath.append(action)


            # print("Check Path: ", chosenPath)
            currentNode = action
            count += 1

    #STOP
            if currentNode == targetNode:
                break
        print("Chosen Path: ", chosenPath)
        if chosenPath not in result:
            result.append(chosenPath)

    print("FINALLLLL: ", chosenPath)
    # store = {}
    # for i in range(len(result)):
    #     store[i] = result[i]
    # with open('C:/Users/DELL/Documents/Research_Express/routes/cfr/cfr_check.json', 'w') as outfile:
    #     json.dump(store, outfile)


if __name__ == "__main__":
    main()
end = time.time()
print(f"Runtime of the program is {end - start}")

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



    #-------------------------------------------
    # while currentNode != targetNode:
    #         if time == 0:
    #             if currentNode == len(topology) - 1:
    #                 time += 1
    #                 print("Node now 0: ", currentNode)
    #         elif time == 1:
    #             if currentNode == len(topology) - 1:
    #                 time += 1
    #                 print("Node now 1: ", currentNode)
    #             else:
    #                 time = 0
    #         elif time == 2:
    #             if currentNode == len(topology) - 1:
    #                 print("Time breakkkkkkkkkk", time)
    #                 break
    #             else:
    #                 time = 0
    #         currentStrategy = copy.deepcopy(strategy[currentNode])
    #         print("PRE current: ", currentStrategy)
    #         print("Go in with current ", currentNode, " and target ", targetNode)
    #         for i in range(len(currentStrategy)):
    #             if currentStrategy[i] != 0 and i in chosenPath:
    #                 currentStrategy[i] = 0
    #         total = sum(currentStrategy)
    #         if total > 0:
    #             currentStrategy = [item / total for item in currentStrategy]
    #         else:
    #             currentStrategy = copy.deepcopy(default_strategy[currentNode])

    #         print("Current Strategy: ", currentStrategy)
    #         action = getaction(len(currentStrategy), currentStrategy)

    #         print("Action: ", action)
    #         if (currentStrategy[action] == 1):
    #             chosenPath.append(action)
    #             print("chosen: ", chosenPath)
    #             reward = reward + topology[currentNode][action]
    #             currentNode = action
    #             print("CurrentNode ", currentNode)
    #             if currentNode == targetNode:
    #                 reward = 1 / reward
    #                 break




# ------------LONG's reward------------------
# def getreward_v4(action,topology,strategy,default_strategy,currentNode,targetNode, path):
#     reward = 0
#     chosenPath = [currentNode, action]
#     reward = reward + topology[chosenPath[len(chosenPath) - 2]][action]
#     currentNode = action
#     path.append(currentNode)
#     path.append(action)
#     deadend = []
#     # print("Get Reward for node ", currentNode)
#     # print("Checkout reward")
#     time = 0
#     if currentNode == targetNode:
#         reward = 1/reward
#     else:
#         result = getreward_long(currentNode, topology, targetNode, path, 0)
#         # print("Receive: ", reward)
#         if result > 0:
#             reward += reward
#             reward = 1/reward
#         else:
#             reward = 0
#     return reward