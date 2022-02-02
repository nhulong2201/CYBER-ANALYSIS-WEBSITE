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

    #check to see if the node is deadend, if it is, return to the parentNode
    if currentNode in deadend:
        return parentNode

    for i in range(num_action):
        if currentStrategy[i] > 0 and i not in chosenPath:
            choices.append(i)
            cum_prob += currentStrategy[i]

    #if there is no path to move forward, return to parentNode, otherwise, pick randomly one to move
    if cum_prob == 0:
        strategy[parentNode][currentNode] = 0
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
            currentStrategy = strategy[currentNode][:]
            for i in range(len(currentStrategy)):
                if currentStrategy[i] != 0 and i in chosenPath:
                    currentStrategy[i] = 0
            total = math.fsum(currentStrategy)
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
    # args = parse_args()
    # entryNode = args.entry
    # targetNode = args.target

    entryNode = 0
    targetNode = 38

    chosenPath = []

    #LOAD FILE
    infile = open('C:/Users/DELL/Documents/Research_Express/routes/cfr/matlab.txt','r')
    numbers = []
    for line in infile:
        numbers.append([float(val) for val in line.split('\t')])
    infile.close()
    topology = numbers

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
    repeat = 1000

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
            utility = np.zeros(len(topology)).tolist()
            for a in range(len(defaultStrategy)):
                if defaultStrategy[currentNode][a] != 0 and a not in deadend:
                    utility[a] = getreward_v4(a,topology,strategy,[x[:] for x in defaultStrategy],currentNode,targetNode,chosenPath[:], deadend)

    # Compute the regret_sum
            for a in range(len(defaultStrategy)):
                if defaultStrategy[currentNode][a] != 0:
                    regret_sum[currentNode][a] = regret_sum[currentNode][a] + utility[a] - math.fsum(np.multiply(utility, defaultStrategy[currentNode]))

            # regret_sum[currentNode] = max(regret_sum(currentNode,:),0);
            for index in range(len(regret_sum)):
                if regret_sum[currentNode][index] < 0:
                    regret_sum[currentNode][index] = 0

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
                print("Total down: ", total)
                print(regret_sum[currentNode])
                finalStrategy = [item / total for item in regret_sum[currentNode][:]]
                for i in range(len(defaultStrategy)):
                    if finalStrategy[i] == max(finalStrategy):
                        finalStrategy[i] = 1
                    else:
                        finalStrategy[i] = 0
                    action = getaction(len(defaultStrategy),finalStrategy)

    # Update chosen path

            chosenPath.append(action)
            count += 1

    #STOP
            if currentNode == targetNode:
                break
        print("Chosen Path: ", chosenPath)

    print("FINAL: ", chosenPath)


if __name__ == "__main__":
    main()
end = time.time()
print(f"Runtime of the program is {end - start}")
