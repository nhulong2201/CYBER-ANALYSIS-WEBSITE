import json
import codecs
import os
import networkx as nx
import sys


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
            with open('routes/iterative_cut/cutset.json', 'w') as outfile:
                json.dump({'impossible': 'yes'}, outfile)
            return None
        reach, not_reach = part
        cutset = make_cutset(G, reach, not_reach)
        # C:/Users/DELL/Documents/Research_Express/
        if cv == 0:
            print('The graph is already cut.')
            with open('routes/iterative_cut/cutset.json', 'w') as outfile:
                json.dump({'alreadyCut': 'yes'}, outfile)
            return None
        cutset = list(cutset)
        print('Here is the cut I found:')
        for i in range(len(cutset)):
            cutjs[i] = cutset[i]
        # C:/Users/DELL/Documents/Research_Express/
        with open('routes/iterative_cut/cutset.json', 'w') as outfile:
            json.dump(cutjs, outfile)
        return cutset

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

def main():

    #Replace the input_path with your ABSOLUTE path
    # input_path = 'C:/Users/DELL/Downloads/bloodHound/BloodHound-Tools/DBCreator/'
    # input_path = 'C:/Users/DELL/Documents/Research_Express/routes/DATABASE'
    input_path = 'routes/DATABASE/'
    output_path = './parsed_graph'
    dom_admin = str(sys.argv[1])
    banned_inputs = str(sys.argv[2])

    edges = set()
    node_meta = dict()
    for file in os.listdir(input_path):
        if file.endswith('.json'):
            meta, e = parse_file(input_path + file)
            edges.update(e)
            node_meta.update(meta)

    # Remove edges between nodes that do not exist
    edges = set(filter(lambda e: e.src in node_meta and e.dst in node_meta, edges))

    #Replace dom_admin with your OWN domain admin
    # dom_admin = 'S-1-5-21-3575477103-1058849377-3253337160-512'

    # dom_admin = 'S-1-5-21-883232822-274137685-4173207997-512'
    # dom_admin = 'S-1-5-21-1390582872-192029990-4074164785-512'
    # S-1-5-21-1390582872-192029990-4074164785-512
    # from edges and nodes, build a graph (like Sigma)
    G = build_networkx_DiGraph(edges)

    # Render a virtual graph (takes too long), can be ignored
    # nx.draw(G, with_labels=1)

    print('Networkx graph built')

    # find admin users who are connected to the domain admin via only groups or users
    admin_users = transitive_users(G, dom_admin, node_meta)
    non_admin_users = set()
    for node in nx.descendants(G.reverse(), dom_admin):
        if node_meta[node][0] == 'User' and node not in admin_users:
            non_admin_users.add(node)
    print('Preprocessing done... running cut algorithm...')
    cutset = find_allowed_cut(G, non_admin_users, admin_users, banned_inputs)
    # for i in range(len(cutset)):
    #     print(i, cutset[i])


if __name__ == "__main__":
    main()
