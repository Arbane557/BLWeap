import networkx as nx

def build_part_graph(parts):
    G = nx.Graph()
    for part in parts:
        G.add_node(part["id"], **part)

    for i, a in enumerate(parts):
        for b in parts[i+1:]:
            if a["class"] != b["class"]:
                continue
            if a["type"] != b["type"]:
                G.add_edge(a["id"], b["id"])
    return G

