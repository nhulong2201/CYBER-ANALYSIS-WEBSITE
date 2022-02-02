from networkx.readwrite.gpickle import read_gpickle
import random
from utility import is_blockable, is_start

# graph_file_names = [
#     "sample.gpickle",
#     "sample-dag.gpickle",
#     "r100.gpickle",
#     "r100-dag.gpickle",
#     "r200.gpickle",
#     "r200-dag.gpickle",
#     "r500.gpickle",
#     "r500-dag.gpickle",
#     "r1000.gpickle",
#     "r1000-dag.gpickle",
#     "r2000.gpickle",
#     "r2000-dag.gpickle",
# ]
graph_file_names = [
    "r500.gpickle"
]

graphs = {}
for fn in graph_file_names:
    graphs[fn] = read_gpickle("routes/AAAI/" + fn)


def random_setup(
    fn, seed, start_node_number, blockable_p, double_edge_p, multi_block_p, budget
):
    CG = graphs[fn + ".gpickle"].copy()
    random.seed(seed)
    CG.graph["budget"] = budget

    for v in CG.nodes():
        if v == CG.graph["DA"]:
            CG.nodes[v]["node_type"] = "DA"
        else:
            CG.nodes[v]["node_type"] = ""
    start_nodes = random.choices(list(CG.nodes()), k=2 * start_node_number)
    if CG.graph["DA"] in start_nodes:
        start_nodes.remove(CG.graph["DA"])
    start_nodes = start_nodes[:start_node_number]
    assert len(start_nodes) == start_node_number
    for v in start_nodes:
        CG.nodes[v]["node_type"] = "S"

    double_edge_list = []
    for u, v in CG.edges():
        if random.random() <= blockable_p:
            if random.random() <= double_edge_p and CG.nodes[v]["node_type"] == "":
                double_edge_list.append((u, v))
            else:
                CG[u][v]["blockable"] = True
        else:
            CG[u][v]["blockable"] = False

    for u in CG.nodes():
        if CG.out_degree(u) > 1 and random.random() <= multi_block_p:
            for v in list(CG.successors(u)):
                CG[u][v]["blockable"] = True

    for u, v in double_edge_list:
        a = hash((u, v))
        CG.add_edge(u, a)
        CG.nodes[a]["node_type"] = ""
        CG.nodes[a]["layer"] = CG.nodes[v]["layer"]
        CG[u][v]["blockable"] = True
        CG[u][a]["blockable"] = True
        for x in list(CG.successors(v)):
            CG[v][x]["blockable"] = False
            CG.add_edge(a, x)
            CG[a][x]["blockable"] = False

    preprocess(CG)
    return CG


def preprocess(CG):
    for u in CG.nodes():
        if CG.out_degree(u) <= 1:
            continue
        unblockable_next = {}
        unblockable_len = {}
        for v in list(CG.successors(u)):
            path = uncached_path_to_split_node_or_DA(CG, u, v)
            path_len = len(path) - 1
            if not is_path_blockable(CG, path):
                if path[-1] not in unblockable_next:
                    unblockable_next[path[-1]] = v
                    unblockable_len[path[-1]] = path_len
                elif path_len < unblockable_len[path[-1]]:
                    unblockable_next[path[-1]] = v
                    unblockable_len[path[-1]] = path_len
        for v in list(CG.successors(u)):
            path = uncached_path_to_split_node_or_DA(CG, u, v)
            path_len = len(path) - 1
            if path[-1] not in unblockable_len:
                continue
            if (
                path_len >= unblockable_len[path[-1]]
                and v != unblockable_next[path[-1]]
            ):
                CG.remove_edge(u, v)

    has_blockable = False
    for u, v in CG.edges():
        if is_blockable(CG, u, v):
            has_blockable = True
    assert has_blockable

    remove_in_degree_0(CG)

    start_nodes = []
    split_nodes = []
    for u in CG.nodes():
        if CG.out_degree(u) > 1:
            split_nodes.append(u)
        if is_start(CG, u):
            start_nodes.append(u)
    CG.graph["start_nodes"] = tuple(sorted(start_nodes))
    CG.graph["split_nodes"] = tuple(sorted(split_nodes))


def remove_in_degree_0(CG):
    keep_deleting = True
    while keep_deleting:
        keep_deleting = False
        for u in list(CG.nodes()):
            if not is_start(CG, u) and CG.in_degree(u) == 0:
                CG.remove_node(u)
                keep_deleting = True


def uncached_path_to_split_node_or_DA(CG, u, v):
    if CG.out_degree(v) > 1 or v == CG.graph["DA"]:
        return [u, v]
    else:
        future = list(CG.successors(v))
        assert len(future) == 1
        return [u] + uncached_path_to_split_node_or_DA(CG, v, future[0])


def is_path_blockable(CG, path):
    for i in range(len(path) - 1):
        if is_blockable(CG, path[i], path[i + 1]):
            return True
    return False
