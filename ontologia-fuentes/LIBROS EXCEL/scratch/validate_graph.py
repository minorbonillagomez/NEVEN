"""Validate graph.jsonl against schema.yaml for Excel ontology."""
import json
import yaml
from collections import Counter

# Load schema
with open(r'F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS EXCEL\memory\ontology\schema.yaml', 'r', encoding='utf-8') as f:
    schema = yaml.safe_load(f)

# Load graph
nodes = {}
edges = []

with open(r'F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS EXCEL\memory\ontology\graph.jsonl', 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get('op') == 'create':
                nodes[d['entity']['id']] = d['entity']
            elif d.get('op') == 'relate':
                edges.append(d)
        except json.JSONDecodeError as e:
            print(f"ERROR line {line_num}: Invalid JSON - {e}")

print(f"Loaded: {len(nodes)} entities, {len(edges)} relations")
print()

# Count by type
type_counts = Counter(n['type'] for n in nodes.values())
print("Entities by type:")
for t, c in sorted(type_counts.items()):
    print(f"  {t}: {c}")
print()

# Validate
valid = True
errors = []

# Check entity types and required fields
for nid, n in nodes.items():
    ntype = n.get('type')
    if ntype not in schema['types']:
        errors.append(f"Entity '{nid}' has invalid type '{ntype}'")
        valid = False
        continue
    
    req = schema['types'][ntype].get('required', [])
    for field in req:
        if field not in n.get('properties', {}):
            errors.append(f"Entity '{nid}' ({ntype}) missing required field '{field}'")
            valid = False

# Check relations
rel_counts = Counter(e['rel'] for e in edges)
print("Relations by type:")
for r, c in sorted(rel_counts.items()):
    print(f"  {r}: {c}")
print()

for e in edges:
    src_id = e['from']
    tgt_id = e['to']
    rel = e['rel']
    
    if src_id not in nodes:
        errors.append(f"Relation from non-existent node '{src_id}'")
        valid = False
        continue
    if tgt_id not in nodes:
        errors.append(f"Relation to non-existent node '{tgt_id}'")
        valid = False
        continue
    if rel not in schema['relations']:
        errors.append(f"Invalid relation predicate '{rel}'")
        valid = False
        continue
    
    src_type = nodes[src_id]['type']
    tgt_type = nodes[tgt_id]['type']
    allowed_from = schema['relations'][rel]['from_types']
    allowed_to = schema['relations'][rel]['to_types']
    
    if src_type not in allowed_from:
        errors.append(f"Relation '{rel}' does not allow from_type '{src_type}' (node '{src_id}')")
        valid = False
    if tgt_type not in allowed_to:
        errors.append(f"Relation '{rel}' does not allow to_type '{tgt_type}' (node '{tgt_id}')")
        valid = False

# Check connectivity (no isolated nodes)
connected = set()
for e in edges:
    connected.add(e['from'])
    connected.add(e['to'])

isolated = set(nodes.keys()) - connected
if isolated:
    errors.append(f"Found {len(isolated)} isolated nodes: {list(isolated)[:5]}...")
    valid = False

# Report
print("=" * 60)
if valid:
    print("✅ VALIDATION PASSED - Schema and graph are 100% compliant!")
else:
    print("❌ VALIDATION FAILED")
    for err in errors[:20]:  # Show first 20 errors
        print(f"  - {err}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more errors")

print()
print(f"Summary: {len(nodes)} entities, {len(edges)} relations, {len(isolated)} isolated")
