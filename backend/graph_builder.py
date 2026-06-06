def build_graph(findings):
    nodes = []
    edges = []
    seen_nodes = set()

    def add_node(node_id, label, node_type):
        if node_id not in seen_nodes:
            nodes.append({
                "id": node_id,
                "label": label,
                "type": node_type
            })
            seen_nodes.add(node_id)

    add_node("profile_1", "Digital Shadow", "profile")

    for i, item in enumerate(findings):
        file_id = f"file_{i}_{item['source_file']}"
        data_id = f"data_{i}_{item['kind']}_{item['value']}"

        add_node(file_id, item["source_file"], "file")
        add_node(data_id, item["value"], "data")
        add_node("profile_1", "Digital Shadow", "profile")

        edges.append({
            "source": file_id,
            "target": data_id,
            "label": "contains"
        })
        edges.append({
            "source": data_id,
            "target": "profile_1",
            "label": item["category"]
        })

    return {
        "nodes": nodes,
        "edges": edges
    }