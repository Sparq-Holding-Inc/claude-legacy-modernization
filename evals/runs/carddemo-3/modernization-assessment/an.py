import json
g=json.load(open('modernization-assessment/graph.json'));a=g['analysis']
for k,v in a.items():
    if k in('dead_code_candidates','wave_seed','reachable_nodes','dead_code_reasons','unresolved_dynamic','fan_in','fan_out','entry_points','reachable_programs'):
        print('##',k,len(v)); continue
    print('##',k,json.dumps(v)[:2500])
print(json.dumps(g['meta'])[:3000])
