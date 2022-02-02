import networkx as nx
import matplotlib
from networkx.drawing.layout import multipartite_layout
from patch import topological_generations
from networkx.algorithms.shortest_paths.generic import shortest_path
from networkx.exception import NetworkXNoPath
from math import prod


def report(CG, ignore_assert=False):
    print()
    n = CG.number_of_nodes()
    m = CG.number_of_edges()
    print("n,m", n, m)
    for v in CG.nodes():
        if CG.out_degree(v) == 0 and not ignore_assert:
            assert v == CG.graph["DA"]
    d = [CG.out_degree(v) for v in CG.nodes() if CG.out_degree(v) > 1] + [1]
    print(d)
    print("max out degree", max(d))
    print("number of splitting nodes", len(d) - 1)
    print("number of cf", prod(d))
    print("number of feedback edges", m - n + 1)
    print()


def correct_dist(CG, v):
    DA = CG.graph["DA"]
    try:
        path = shortest_path(CG, v, DA)
        return len(path) - 1
    except NetworkXNoPath:
        return None


def is_start(CG, v):
    if v in CG.nodes():
        return CG.nodes[v]["node_type"] == "S"
    else:
        return False


def remove_start(CG, v):
    assert is_start(CG, v)
    CG.nodes[v]["node_type"] = ""


def is_blockable(CG, u, v):
    if "blockable" in CG[u][v]:
        return CG[u][v]["blockable"]
    else:
        return False


def set_blockable(CG, u, v, val):
    CG[u][v]["blockable"] = val


def remove_dead_nodes(CG):
    keepGoing = True
    while keepGoing:
        keepGoing = False
        for v in set(CG.nodes):
            if correct_dist(CG, v) is None:
                CG.remove_node(v)
                keepGoing = True


def evaluate(CG):
    # todo: not efficient
    # but ok-ish if the number of starting nodes is small
    res = 0
    DA = CG.graph["DA"]
    for v in CG.nodes():
        if is_start(CG, v):
            try:
                path = shortest_path(CG, v, DA)
                res += f(len(path) - 1, CG)
            except NetworkXNoPath:
                pass
    return res


def f(dist, CG):
    return 0.95 ** dist / len(CG.graph["start_nodes"])


def display(DG, always_delete=None):
    matplotlib.use("TkAgg")

    CG = DG.copy()
    if always_delete is not None:
        CG.remove_nodes_from(always_delete)
        remove_dead_nodes(CG)
    layers = list(topological_generations(CG))
    for i, vs in enumerate(layers):
        for v in vs:
            DG.nodes[v]["layer"] = i
    for u in DG.nodes():
        if "layer" not in DG.nodes[u]:
            DG.nodes[u]["layer"] = len(layers) - 1 - correct_dist(DG, u)

    nx.draw(
        DG,
        pos=multipartite_layout(DG, subset_key="layer"),
        with_labels=False,
        node_size=30,
        # node_color="#333333",
    )
    matplotlib.pyplot.show()


def upper_lower_bounds(CG):
    print("Upper bound", evaluate(CG))
    CG_copy = CG.copy()
    for u, v in CG.edges():
        if is_blockable(CG, u, v):
            CG_copy.remove_edge(u, v)
    lb = evaluate(CG_copy)
    print("Lower bound", lb)
    return lb
