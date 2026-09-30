import json
import re
import os
import yaml

def test_schema_and_graph():
    print("=== Testing schema.yaml & graph.jsonl ===")
    with open('memory/ontology/schema.yaml', 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    nodes = {}
    edges = []
    with open('memory/ontology/graph.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if item.get('op') == 'create':
                nodes[item['entity']['id']] = item['entity']
            elif item.get('op') == 'relate':
                edges.append(item)

    print(f"Entities: {len(nodes)}, Relations: {len(edges)}")
    assert len(nodes) == 199, f"Expected 199 nodes, got {len(nodes)}"
    assert len(edges) == 399, f"Expected 399 relations, got {len(edges)}"

    # Check node fields
    for nid, n in nodes.items():
        ntype = n.get('type')
        assert ntype in schema['types'], f"Invalid type {ntype} for {nid}"
        for req in schema['types'][ntype].get('required', []):
            assert req in n['properties'], f"Missing required property {req} in node {nid}"

    # Check edge constraints
    connected = set()
    for e in edges:
        s, t, rel = e['from'], e['to'], e['rel']
        assert s in nodes, f"Edge from unknown node {s}"
        assert t in nodes, f"Edge to unknown node {t}"
        assert rel in schema['relations'], f"Unknown relation {rel}"
        stype = nodes[s]['type']
        ttype = nodes[t]['type']
        assert stype in schema['relations'][rel]['from_types'], f"Type {stype} not allowed in from of {rel}"
        assert ttype in schema['relations'][rel]['to_types'], f"Type {ttype} not allowed in to of {rel}"
        connected.add(s)
        connected.add(t)

    isolated = set(nodes.keys()) - connected
    assert len(isolated) == 0, f"Found isolated nodes: {isolated}"
    print("-> Schema & Graph: 100% VALID! (0 isolated nodes)")

def test_visualizers():
    print("=== Testing 2D and 3D Visualizers ===")
    for path in ['memory/ontology/graph_visualization.html', 'memory/ontology/graph_visualization_3d.html']:
        assert os.path.exists(path), f"File {path} does not exist"
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'const rawGraph = (\[.*?\]);\n', content, re.DOTALL)
        assert match, f"Could not find rawGraph in {path}"
        data = json.loads(match.group(1))
        nodes_in_html = [d for d in data if d.get('op') == 'create']
        edges_in_html = [d for d in data if d.get('op') == 'relate']
        assert len(nodes_in_html) == 199, f"{path} has {len(nodes_in_html)} nodes, expected 199"
        assert len(edges_in_html) == 399, f"{path} has {len(edges_in_html)} edges, expected 399"
        print(f"-> {path}: 100% VALID ({len(nodes_in_html)} nodes, {len(edges_in_html)} edges)")

def test_skills():
    print("=== Testing Skills ===")
    skills_dir = '.agents/skills'
    subdirs = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))]
    print(f"Found {len(subdirs)} skill folders: {subdirs}")
    assert len(subdirs) == 8, f"Expected 8 skills, found {len(subdirs)}"
    for d in subdirs:
        skill_file = os.path.join(skills_dir, d, 'SKILL.md')
        assert os.path.exists(skill_file), f"Missing SKILL.md in {d}"
        with open(skill_file, 'r', encoding='utf-8') as f:
            text = f.read()
        assert text.startswith('---'), f"{d}/SKILL.md missing YAML frontmatter start"
        parts = text.split('---', 2)
        assert len(parts) >= 3, f"{d}/SKILL.md invalid frontmatter structure"
        meta = yaml.safe_load(parts[1])
        assert 'name' in meta, f"{d}/SKILL.md missing 'name' in frontmatter"
        assert 'description' in meta, f"{d}/SKILL.md missing 'description' in frontmatter"
        print(f"-> Skill {d}: VALID (name: {meta['name']})")

if __name__ == '__main__':
    test_schema_and_graph()
    test_visualizers()
    test_skills()
    print("\nALL TESTS PASSED SUCCESSFULLY!")
