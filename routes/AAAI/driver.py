from argparse import ArgumentParser
import json
from setupgraph import random_setup
from trivialFPT import trivialFPT, trivialFPT_helper
from greedy import greedy, greedy_v2
from utility import upper_lower_bounds, report
from treedecomposition import dp
from classification import all_classifications
import timeit
from networkx.readwrite.gpickle import write_gpickle
from gnn import run_gnn

# "sample.gpickle",
# "sample-dag.gpickle",
# "r100.gpickle",
# "r100-dag.gpickle",
# "r200.gpickle",
# "r200-dag.gpickle",
# "r500.gpickle",
# "r500-dag.gpickle",
# "r1000.gpickle",
# "r1000-dag.gpickle",
# "r2000.gpickle",
# "r2000-dag.gpickle",

def parse_args():
    parser = ArgumentParser(prog="ShotHound", prefix_chars="-/", add_help=False, description=f'Finding practical paths in BloodHound')

    parser.add_argument('budget', type = int)
    parser.add_argument('start', type = int)
    args = parser.parse_args()

    return args
args_input = parse_args()

number_of_runs = 10
args = {
    "fn": "r500",
    "budget": args_input.budget,
    "start_node_number": args_input.start,
    "blockable_p": 0,
    "double_edge_p": 0,
    "multi_block_p": 1,
}

print(args)

output = {}
result = []
greedy_details = []
gnn_details = []
trivial_details = []
class_details = []

def time_and_run(name, func, CG):

    start_time = timeit.default_timer()
    # received_list =
    # received_list = func(CG)
    # print("RECEIVED: ", received_list)
    # print("Others: ", others)
    # output[f"{name}_res"] = received_list[0]
    # greedy_details = received_list[1]

    if name == "greedy":
        global greedy_details
        output[f"{name}_res"], temp_greedy = func(CG)
        greedy_details.append(temp_greedy.copy())
        # print("CHECK OUTPUT GREEDY: ", greedy_details)
    elif name == "gnn":
        global gnn_details
        output[f"{name}_res"], temp_gnn = func(CG)
        gnn_details.append(temp_gnn.copy())
    elif name == "trivialFPT":
        global trivial_details
        output[f"{name}_res"], temp_trivial = func(CG)
        trivial_details.append(temp_trivial.copy())
    elif name == "cf":
        global class_details
        output[f"{name}_res"], temp_class = func(CG)
        class_details.append(temp_class.copy())
    else:
        output[f"{name}_res"] = func(CG)

    output[f"{name}_time"] = timeit.default_timer() - start_time


for seed in range(number_of_runs):
    args["seed"] = seed
    CG = random_setup(**args)
    print("done SETUP-------------")
    report(CG)
    print("Done REPORT ---------------")
    print(upper_lower_bounds(CG))
    print("Done UPPER BOUND")

    time_and_run("lb", upper_lower_bounds, CG)
    print("Done UPPER BOUND v2")
    time_and_run("trivialFPT", trivialFPT_helper, CG)
    print("Done TrivialFPT")
    time_and_run("greedy", greedy_v2, CG)
    print(" DETAILS: ", greedy_details)
    print("GREEDY details: ", greedy_details)
    print("Done GREEDYYYYYYYYYYY")
    if "dag" in args["fn"]:
        time_and_run("dp", dp, CG)
    print("Done DAG optional")
    time_and_run("cf", all_classifications, CG)
    print("Done Classification")
    time_and_run("gnn", run_gnn, CG)
    print("Done GNNNNNNNNNNN")

    result.append(output.copy())

print("Result length: ------------------------------------------", len(result))
print('--------------------------------------------------')
print('--------------------------------------------------')
print('--------------------------------------------------')

print("First: ", result[0])
# print(result)
store = {"items": []}
all_methods = ["trivialFPT", "greedy", "cf", "gnn"]
# "trivialFPT", "greedy", "dp", "cf", "gnn"
for method in ["lb"] + all_methods:
    if method + "_res" in result[0]:
        time_sum = sum([r[method + "_time"] for r in result])
        perf_sum = sum([r[method + "_res"] for r in result])
        print(method, time_sum / number_of_runs, perf_sum / number_of_runs)
for i, r in enumerate(result):
    best_methods = []
    for method in all_methods:
        if method + "_res" not in r:
            continue
        is_best = True
        for other_method in all_methods:
            if other_method == method or other_method + "_res" not in r:
                continue
            if r[other_method + "_res"] + 0.000001 < r[method + "_res"]:
                is_best = False
        if is_best:
            best_methods.append(method)
    temp_store = {}
    temp_store["id"] = i
    temp_store["best"] = best_methods[:]
    temp_store["greedy"] = greedy_details[i][:]
    temp_store["gnn"] = gnn_details[i][:]
    temp_store["trivial"] = trivial_details[i][:]
    temp_store["cf"] = class_details[i][:]
    store["items"].append(temp_store)
    print(f"round {i} best methods", best_methods)
    print("Greedy: ", greedy_details[i])
    print("GNN: ", gnn_details[i])
    print("Trivial: ", trivial_details[i])

# write_gpickle(
#     (args, result),
#     f"/home/m/Dropbox/{args['fn']}-{args['budget']}-{args['start_node_number']}-{args['blockable_p']}-{args['double_edge_p']}.gpickle",
# )
with open('routes/AAAI/best_methods.json', 'w') as outfile:
    json.dump(store, outfile)
write_gpickle(
    (args, result),
    f"routes/AAAI/{args['fn']}-{args['budget']}-{args['start_node_number']}-{args['blockable_p']}-{args['double_edge_p']}.gpickle",
)