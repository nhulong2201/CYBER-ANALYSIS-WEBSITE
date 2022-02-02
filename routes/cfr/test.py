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
import copy
import time
start = time.time()

def parse_file(filename):
    edges = set()
    node_meta = dict()
    print(filename)
    with open(filename, encoding='utf-8-sig') as json_file:
        j=json.load(json_file)

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

def deepcpy(path):
    path[0][1]=200
    return 100

def main():
    # input_path = 'C:/Users/DELL/Documents/Research_Express/routes/cfr/today.json'
    # # with open('C:/Users/DELL/Documents/Research_Express/routes/all.json', encoding='utf-8-sig') as json_file:
    # #     j=json.load(json_file)
    # # output_path = './parsed_graph'
    # # print(edges[0])

    # # Opening JSON file
    # f = open(input_path)

    # # returns JSON object as
    # # a dictionary
    # data = json.load(f)
    # edges = list(data["edges"])
    # print(int(edges[0]["start"]["id"]))
    # t1 = [[2, 4], [3,5]]
    # # t2 = copy.deepcopy(t1)
    # t2 = copy.deepcopy(t1[1])
    # t2[1]= 10
    # print(t1)
    # road = [2,6,7,10]
    # number = 10
    # result = deepcpy(copy.deepcopy(road))
    # print(road)
    l1 = [2,5,3]
    l3 = [2,5,3]
    l2 = [10,50]
    list = [[10,50]]
    if l3 in list:
        print("Here")
    else:
        print("Not here")
    # del l1[-1]
    # l1.extend(l2)
    print(l1)
    # num = int(random.sample(l1, 1)[0])
    # print(num)






if __name__ == "__main__":
    main()
end = time.time()
print(f"Runtime of the program is {end - start}")
