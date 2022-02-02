from networkx.algorithms.dag import ancestors
import networkx as nx
from utility import is_blockable, is_start, correct_dist
from classification import (
    path_to_split_node_or_DA,
    classification,
    get_cf_max,
    cf_setup,
)
from torch_geometric.utils import from_networkx, dropout_adj
import torch
from torch.nn import Linear
from torch_geometric.nn import CGConv
from random import random, shuffle, choices, seed
from math import exp
from greedy import greedy


def run_gnn(CG):
    global device, DG, split_nodes, split_nodes_and_DA, category_number, cf_max

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    DG = CG
    cf_setup(CG)
    cf_max = get_cf_max()

    split_nodes = DG.graph["split_nodes"]
    split_nodes_and_DA = list(split_nodes) + [DG.graph["DA"]]
    out_degrees = [DG.out_degree(v) for v in split_nodes]
    if len(out_degrees) == 0:
        return greedy(DG)
    category_number = max(out_degrees) + 1
    init_compressed_graph()

    res = []
    for seed_used in range(5):
        seed(seed_used)
        torch.manual_seed(seed_used)
        res.append(train(seed_used))
    print("gnn trained res", res)
    return min(res)[0], min(res)[1]


def init_compressed_graph():
    global x, edge_index, edge_attr
    SNG = nx.DiGraph()
    DG_without_edges = DG.copy()
    for u, v in DG.edges():
        if is_blockable(DG, u, v):
            DG_without_edges.remove_edge(u, v)
    for v in split_nodes_and_DA:
        layer = DG.nodes[v]["layer"]
        in_degree = DG.in_degree(v)
        out_degree = DG.out_degree(v)
        start_coverage = len(set(ancestors(DG, v)).intersection(set(split_nodes)))
        correct_distance = correct_dist(DG, v)
        if correct_distance is None:
            correct_distance = 1000
        worst_distance = correct_dist(DG_without_edges, v)
        if worst_distance is None:
            worst_distance = 1000
        is_start_node = 1 if is_start(DG, v) else 0
        SNG.add_node(
            v,
            layer=layer,
            in_degree=in_degree,
            out_degree=out_degree,
            start_coverage=start_coverage,
            correct_distance=correct_distance,
            worst_distance=worst_distance,
            is_start_node=is_start_node,
        )

    print("node feature completed")

    for u in split_nodes_and_DA:
        future = sorted(DG.successors(u))
        for v in future:
            path = path_to_split_node_or_DA(u, v)
            classification_index = future.index(v)
            blockable_count = 0
            start_count = 0
            last_layer = DG.nodes[u]["layer"]
            for i in range(1, len(path) - 1):
                if is_start(DG, path[i]):
                    start_count += 1
            for i in range(len(path) - 1):
                if is_blockable(DG, path[i], path[i + 1]):
                    blockable_count += 1
                    last_layer = DG.nodes[path[i]]["layer"]
            SNG.add_edge(
                u,
                path[-1],
                length=len(path),
                classification_index=classification_index,
                blockable_count=blockable_count,
                last_layer=last_layer,
                start_count=start_count,
                direction=0,
            )
            SNG.add_edge(
                path[-1],
                u,
                length=len(path),
                classification_index=classification_index,
                blockable_count=blockable_count,
                last_layer=last_layer,
                start_count=start_count,
                direction=1,
            )

    print("edge feature completed")

    data = from_networkx(SNG)

    print("data generated")

    x = torch.stack(
        (
            data.layer,
            data.in_degree,
            data.out_degree,
            data.start_coverage,
            data.correct_distance,
            data.worst_distance,
            data.is_start_node,
        ),
        dim=1,
    ).float()
    edge_attr = torch.stack(
        (
            data.classification_index,
            data.length,
            data.blockable_count,
            data.last_layer,
            data.start_count,
            data.direction,
        ),
        dim=1,
    ).float()
    edge_index = data.edge_index
    x.to(device)
    print("x to device")
    edge_index.to(device)
    print("edge index to device")
    edge_attr.to(device)
    print("edge attr to device")


class GCN(torch.nn.Module):
    def __init__(self, hidden_channels, num_layers, category_number):
        super(GCN, self).__init__()
        self.node_encoder = Linear(7, hidden_channels)
        self.edge_encoder = Linear(6, hidden_channels)

        self.layers = torch.nn.ModuleList()
        for i in range(1, num_layers + 1):
            self.layers.append(
                CGConv(hidden_channels, hidden_channels, aggr="max", batch_norm=True)
            )

        self.lin = Linear(hidden_channels, category_number)

    def forward(self, x, edge_index, edge_attr):
        x = self.node_encoder(x)
        edge_attr = self.edge_encoder(edge_attr)

        for layer in self.layers[1:]:
            dropped_edge_index, dropped_edge_attr = dropout_adj(
                edge_index, edge_attr, p=0.1
            )
            x = layer(x, dropped_edge_index, dropped_edge_attr)

        return self.lin(x), x


def random_cf(cf, indices, out):
    cf = list(cf)
    for i in indices:
        if random() < reuse_cf_prob:
            try:
                weights = [exp(x) for x in out[i]]
            except OverflowError:
                print("overflow warning", out[i])
                weights = [1 for x in out[i]]
        else:
            weights = [1 for x in out[i]]
        cf[i] = choices(range(category_number), weights)[0]
        if cf[i] == category_number - 1:
            cf[i] = -1
        if cf[i] > cf_max[i]:
            cf[i] = choices(range(cf_max[i]), weights[: cf_max[i]])[0]
    return tuple(cf)


def generate_batch_mask(size):
    n = len(split_nodes_and_DA)
    indices = torch.randperm(n - 1)[:size]
    mask = torch.BoolTensor([1 if i in indices else 0 for i in range(n)])
    return indices, mask


def out_to_cf(out):
    cf = []
    for v in out[:-1]:
        res = tuple(v).index(max(v))
        if res == category_number - 1:
            res = -1
        cf.append(res)
    assert len(cf) == len(cf_max)
    for i in range(len(cf)):
        if cf[i] > cf_max[i]:
            cf[i] = choices(range(cf_max[i]))[0]
    return tuple(cf)


def cf_to_out(cf):
    out = []
    for v in cf:
        res = v
        if v == -1:
            res = category_number - 1
        out.append(res)
    out.append(0)
    return torch.LongTensor(out)

global_best_edges = []
best_edges = []
def flip_cf(cf, index):
    global best_edges
    cf_list = list(cf)
    res = []
    for x in range(-1, cf_max[index]):
        cf_list[index] = x
        result = classification(tuple(cf_list))
        res.append((result, x))
    # print("CHECCCCCK: ", res)
    best_edges = min(res)[0][3].copy()
    best_x = min(res)[1]
    best_performance = min(res)[0][0]
    cf_list[index] = best_x
    # print("BEST PERFORM: ", min(res)[0][3])
    return tuple(cf_list), best_performance


# supervision
# greedy_cf = greedy_cf()
# greedy_out = cf_to_out(greedy_cf)
# print(greedy_cf)
# print(greedy_out)
# while True:
#     optimizer.zero_grad()  # Clear gradients.
#     out, h = model(x, data.edge_index, edge_attr)
#     indices, mask = generate_batch_mask(8)
#     loss = criterion(out[mask], greedy_out[mask])
#     loss.backward()
#     optimizer.step()
#     print("supervision loss", loss)
#     if loss < 0.000001:
#         break
# print(greedy_cf)


reuse_cf_prob = 0.9


def train(seed_used):
    global best_edges
    global global_best_edges
    model = GCN(hidden_channels=64, num_layers=10, category_number=category_number)
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    batch_size = 16
    learn_global_best_prob = 0.5
    epoch_limit = 50

    global_best_cf = None
    global_best_perf = 1
    epoch = 1
    while epoch <= epoch_limit:
        optimizer.zero_grad()
        out, _ = model(x, edge_index, edge_attr)
        cf = out_to_cf(out)

        indices, mask = generate_batch_mask(batch_size)
        cf = random_cf(cf, indices, out)
        shuffle(indices)
        for index in indices:
            cf, best_perf = flip_cf(cf, index)
        if global_best_cf is None or best_perf < global_best_perf:
            global_best_cf = cf
        # global_best_perf = min(best_perf, global_best_perf)
        if best_perf < global_best_perf:
            # print("-----------BEST EDGES---------", best_edges)
            global_best_perf = best_perf
            global_best_edges = best_edges.copy()
        if random() < learn_global_best_prob:
            loss = criterion(out[mask], cf_to_out(global_best_cf)[mask])
        else:
            loss = criterion(out[mask], cf_to_out(cf)[mask])
        loss.backward()
        optimizer.step()
        print(seed_used, epoch, best_perf, global_best_perf, loss)
        epoch += 1
    return global_best_perf, global_best_edges
