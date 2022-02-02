import networkx as nx
from itertools import combinations
from patch import topological_generations
from utility import f, is_start, is_blockable
from functools import lru_cache


def build_tree_decomposition(CG):
    tree_nodes = []
    G = CG.to_undirected()
    for layer in topological_generations(CG):
        for v in layer:
            G.add_edges_from(combinations(G.neighbors(v), 2))
            tree_nodes.append((v, tuple(sorted(G.neighbors(v))), 0))
            G.remove_node(v)

    # print(tree_nodes)
    print("tree width:", max([len(x[1]) for x in tree_nodes]))

    TD = nx.DiGraph()
    n = len(tree_nodes)
    for i in range(n - 1):
        for j in range(i + 1, n):
            if tree_nodes[j][0] in tree_nodes[i][1]:
                TD.add_edge(tree_nodes[i], tree_nodes[j])
                break

    return TD


def add_aux_nodes(TD):
    for u in list(TD.nodes()):
        assert u[2] == 0
        u_prime = (u[0], u[1], 1)
        for pre in list(TD.predecessors(u)):
            TD.remove_edge(pre, u)
            TD.add_edge(pre, u_prime)
        TD.add_edge(u_prime, u)

    # make tree binary
    not_binary = True
    while not_binary:
        not_binary = False
        for u in list(TD.nodes()):
            pres = list(TD.predecessors(u))
            if len(pres) > 2:
                u_prime = (u[0], u[1], u[2] + 1)
                TD.add_edge(u_prime, u)
                for pre in pres[1:]:
                    TD.remove_edge(pre, u)
                    TD.add_edge(pre, u_prime)
                not_binary = True
                break

    return TD


def moveon(new_node, knowledge_dict, aux_knowledge, budget):
    new_myself, new_knowledge_nodes, new_aux_flag = new_node
    new_knowledge_vals = tuple(knowledge_dict[i] for i in new_knowledge_nodes)
    new_aux_knowledge = aux_knowledge
    if new_aux_flag == 0:
        new_aux_knowledge = -1
    return go(new_node, new_knowledge_vals, new_aux_knowledge, budget)


# need to clear cache
# haskell style terminology: go is the dp function
@lru_cache(maxsize=None)
def go(node, knowledge_values, aux_knowledge, budget):
    myself, knowledge_nodes, aux_flag = node
    assert len(knowledge_nodes) == len(knowledge_values)
    knowledge_dict = dict(zip(knowledge_nodes, knowledge_values))
    if aux_flag == 0:
        assert aux_knowledge == -1
        shortest_distances = []
        for dest in DG.successors(myself):
            distance = knowledge_dict[dest] + 1
            blockable = is_blockable(DG, myself, dest)
            shortest_distances.append((distance, dest, blockable))
        shortest_distances.append((1000000, -1, False))
        shortest_distances = sorted(shortest_distances)
        max_spend = 0
        for _, _, blockable in shortest_distances:
            if blockable:
                max_spend += 1
            else:
                break
        assert len(list(TD.predecessors(node))) == 1
        res_list = []
        for spend in range(min(budget, max_spend) + 1):
            realised_distance = shortest_distances[spend][0]
            pre = list(TD.predecessors(node))[0]
            res = go(pre, knowledge_values, realised_distance, budget - spend)
            if is_start(DG, myself):
                res += f(realised_distance, DG)
            res_list.append(res)
        return min(res_list)
    else:
        assert aux_knowledge != -1
        knowledge_dict[myself] = aux_knowledge
        pres = list(TD.predecessors(node))
        if len(pres) == 0:
            # leaf aux node doesn't contribute
            return 0
        elif len(pres) == 1:
            return moveon(pres[0], knowledge_dict, aux_knowledge, budget)
        elif len(pres) == 2:
            res_list = []
            for budget0 in range(budget + 1):
                budget1 = budget - budget0
                res0 = moveon(pres[0], knowledge_dict, aux_knowledge, budget0)
                res1 = moveon(pres[1], knowledge_dict, aux_knowledge, budget1)
                res_list.append(res0 + res1)
            return min(res_list)
        else:
            assert False


def dp(CG):
    global DG, TD
    DG = CG
    TD = add_aux_nodes(build_tree_decomposition(DG))
    go.cache_clear()
    # wlog to start from the aux node for DA
    return go((DG.graph["DA"], (), 1), (), 0, DG.graph["budget"])
