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

def getaction_v2(num_action, currentStrategy, currentNode, parentNode, chosenPath, deadend):
    cum_prob = 0
    choices = []

    #check to see if the node is deadend, if it is, return to the parentNode
    if currentNode in deadend:
        return parentNode

    for i in range(num_action):
        if currentStrategy[i] > 0 and i not in chosenPath and i not in deadend:
            choices.append(i)
            cum_prob += currentStrategy[i]

    #if there is no path to move forward, return to parentNode, otherwise, pick randomly one to move
    if cum_prob == 0:
        # strategy[parentNode][currentNode] = 0
        if currentNode not in deadend:
            deadend.append(currentNode) #if there is no more path, then the node is deadend, store that in deadend list
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

def getreward_v4(action,topology,strategy,default_strategy,currentNode,targetNode, path, deadend):
    reward = 0
    chosenPath = path[:] #visited nodes

    chosenPath.append(action)
    options = [currentNode, action] #keep track of the current path
    reward = reward + topology[chosenPath[len(chosenPath) - 2]][action]
    parentNode = options[0]
    currentNode = options[1]

    if currentNode == targetNode:
        reward = 1/reward
    else:
        while currentNode != targetNode:
            # print("Options: ", options)
            currentStrategy = strategy[currentNode][:]
            for i in range(len(currentStrategy)):
                if currentStrategy[i] != 0 and i in chosenPath:
                    currentStrategy[i] = 0
            total = math.fsum(currentStrategy)
            if total > 0:
                currentStrategy = [item / total for item in currentStrategy]
                action = getaction_v2(len(currentStrategy), currentStrategy[:], currentNode, parentNode, chosenPath[:], deadend)
                chosenPath.append(action)

                #if the currentNode returning back to parentNode
                if action == parentNode:

                    #if there are more than 2 remaining nodes
                    if len(options) != 2:
                        del options[-1] #delete the node from the path option
                        reward -= topology[parentNode][currentNode] #take back the reward giving out before
                        currentNode = action
                        parentNode = options[len(options) - 2]
                    else:
                        #there is no path, so reward is 0
                        # print("Chosen Path: ", chosenPath)
                        reward = 0
                        return 0
                #Otherwise, moving forward
                else:
                    options.append(action)
                    reward = reward + topology[currentNode][action]
                    parentNode = currentNode
                    currentNode = action

                if currentNode == targetNode:
                    reward = 1 / reward
                    break
            else: #if currentNode is deadend
                if len(options) == 2:
                    if currentNode not in deadend:
                        deadend.append(currentNode)
                    return 0
                # if there is no way to continue, we backtrack
                del options[-1] #delete the node from the path option
                reward -= topology[parentNode][currentNode] #take back the reward giving out before
                if currentNode not in deadend:
                    deadend.append(currentNode)
                currentNode = parentNode
                parentNode = options[len(options) - 2]

    # print("Chosen Path: ", chosenPath)
    return reward

def parse_args():
    parser = ArgumentParser(prog="ShotHound", prefix_chars="-/", add_help=False, description=f'Finding practical paths in BloodHound')

    parser.add_argument('entry', type = int)
    parser.add_argument('target', type = int)
    args = parser.parse_args()

    return args

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



def main():
    # args = parse_args()
    # entryNode = args.entry
    # targetNode = args.target

    entryNode = 499
    targetNode = 524
    # entryNode = 0
    # targetNode = 38

    chosenPath = []
    # -------------------------------------------------------------------------
    # LOAD FILE
    # infile = open('matlab.txt','r')
    # numbers = []
    # for line in infile:
    #     numbers.append([float(val) for val in line.split('\t')])
    # infile.close()
    # topology = numbers

    # for i in range(len(topology)):
    #     topology[i][i] = 0
    #---------------------------------------------------------------------------
    input_path = 'C:/Users/DELL/Documents/Research_Express/routes/cfr/all.json'
    f = open(input_path)
    data = json.load(f)
    edges = list(data["edges"])
    result = []

    n_nodes = 1554
    # topology = np.zeros((n_nodes,n_nodes), dtype=int)

    edges_type = []

    # print(topology)
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
    for i in range(len(topology)):
        topology[i][i] = 0


    #Initialization for CFR
    strategy = [x[:] for x in topology]
    for i in range(len(strategy)):
        for j in range(len(strategy)):
            if strategy[i][j] != 0:
                strategy[i][j] = 1
    for i in range(len(strategy)):
        total = math.fsum(strategy[i])
        if total != 0:
            #strategy(i,:) = strategy(i,:)./sum(strategy(i,:));
            strategy[i] = [item / total for item in strategy[i]]
    defaultStrategy = [x[:] for x in strategy]
    regret_sum = [ [0] * len(topology) for _ in range(len(topology))]

    print("main")
    # MAIN ALGORITHM
    repeat = 5000

    utility = [0] * len(topology)
    deadend = []

    for episodes in range(repeat):
        print("--------------------Episodes----------------------", episodes)
    #Exploration
        if episodes < repeat - 1:
            #not the final one
            strategy = [x[:] for x in defaultStrategy]
        else:
            for i in range(len(defaultStrategy)):
                total = math.fsum(regret_sum[i])
                if total > 0:
                    strategy[i] = [item / total for item in regret_sum[i]]
                else:
                    strategy[i] = defaultStrategy[i][:]

    ###
        reward = 0
        currentNode = entryNode
        chosenPath = [currentNode]

        count = 0
        time = 0

        while currentNode != targetNode:

    #Compute the expected utility using simulation
            print("Path: ", chosenPath)
            # utility = np.zeros(len(topology)).tolist()
            utility = [0] * len(topology)
            # print("--------REWARD-------")
            for a in range(len(defaultStrategy)):
                if defaultStrategy[currentNode][a] != 0 and a not in deadend and a not in chosenPath:
                    # print(defaultStrategy[currentNode][a])
                    utility[a] = getreward_v4(a,topology,strategy,[x[:] for x in defaultStrategy],currentNode,targetNode,chosenPath[:], deadend)
                    # print("deadend: ", deadend)
                    # print(utility[a], "of ", a)
            # print("---------------------")
    # Compute the regret_sum
            # print("CURRENT NODE: ", currentNode)
            for a in range(len(defaultStrategy)):
                if defaultStrategy[currentNode][a] != 0:
                    regret_sum[currentNode][a] = regret_sum[currentNode][a] + utility[a] - math.fsum(np.multiply(utility, defaultStrategy[currentNode]))

            # regret_sum[currentNode] = max(regret_sum(currentNode,:),0);
            for index in range(len(regret_sum)):
                if regret_sum[currentNode][index] < 0:
                    regret_sum[currentNode][index] = 0
                # else:
                    # print("REGRET: ", regret_sum[currentNode][index])

    # Update strategy based on regret minimization
            if math.fsum(regret_sum[currentNode]) > 0:
                strategy[currentNode] = getstrategy(len(defaultStrategy),regret_sum[currentNode][:],strategy[currentNode][:])
            else:
                strategy[currentNode] = defaultStrategy[currentNode][:]

    # Update current strategy
            currentStrategy = strategy[currentNode][:]
            for i in range(len(currentStrategy)):
                if currentStrategy[i] != 0 and i in chosenPath:
                    currentStrategy[i] = 0
            total = math.fsum(currentStrategy)

            if total == 0:
                currentStrategy = defaultStrategy[currentNode][:]
                for i in range(len(defaultStrategy)):
                    if currentStrategy[i] != 0 and i in chosenPath:
                        currentStrategy[i] = 0
                total1 = math.fsum(currentStrategy)
                if total1 > 0:
                    currentStrategy = [item / total1 for item in currentStrategy]
                else:
                    currentStrategy = defaultStrategy[currentNode][:]
                    for i in range(len(defaultStrategy)):
                        if currentStrategy[i] != 0 and i == chosenPath[len(chosenPath) - 2]:
                            currentStrategy[i] = 0

                    total2 = math.fsum(currentStrategy)
                    if total2 > 0:
                        currentStrategy = [item / total2 for item in currentStrategy]
                    else:
                        currentStrategy = defaultStrategy[currentNode][:]
            else:
                currentStrategy = [item /total for item in currentStrategy]

    # Sample an action from the updated strategy
            action = getaction(len(currentStrategy),currentStrategy[:])
            if episodes == repeat - 1:
                # finalStrategy = regret_sum(currentNode,:)./sum(regret_sum(currentNode,:));
                # finalStrategy = [item / sum(regret_sum[currentNode]) for item in regret_sum[currentNode]]
                total = math.fsum(regret_sum[currentNode])
                # print("Total down: ", total)
                # print(regret_sum[currentNode])
                finalStrategy = [item / total for item in regret_sum[currentNode][:]]
                for i in range(len(defaultStrategy)):
                    if finalStrategy[i] == max(finalStrategy):
                        finalStrategy[i] = 1
                    else:
                        finalStrategy[i] = 0
                    action = getaction(len(defaultStrategy),finalStrategy)

    # Update chosen path

            chosenPath.append(action)


            currentNode = action
            count += 1

    #STOP
            if currentNode == targetNode:
                break
        print("Chosen Path: ", chosenPath)

    print("FINAL: ", chosenPath)
    store = {}

    store[0] = chosenPath
    with open('C:/Users/DELL/Documents/Research_Express/routes/cfr/cfr_check.json', 'w') as outfile:
        json.dump(store, outfile)


if __name__ == "__main__":
    main()
end = time.time()
print(f"Runtime of the program is {end - start}")
