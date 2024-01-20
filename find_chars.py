import json, sys
from re import sub
from caseconverter import snakecase

"""
Filters and converts data from https://www.raidbots.com/static/analysis/top/details.json
into a format that is nearly parseable by simc.

To make piping convenient, most messaging is on stderr.

-S
  Sorts entries based on comma-separated strings. Supports multiple invocations.
-T
  Returns the first k results for -Tk.
-P
  Filters printed keys based on comma-separated strings. Supports multiple invocations.
-O
  Prints simc-formatted gear to stdout.
"""

reserved_prefixes = [
    '-S',
    '-T',
    '-P',
    '-O'
] # yapf: disable
filter_args = [
    arg.upper()
    for arg in sys.argv[1:]
    if arg[:2] not in reserved_prefixes
] # yapf: disable
sort_args = [
    subarg.upper()
    for arg in sys.argv[1:]
    if arg[:2] == '-S'
    if (tmp := [arg[2:]] if ',' not in arg else arg[2:].split(',')) or True
    for subarg in tmp
] # yapf: disable
print_args = [
    subarg.upper()
    for arg in sys.argv[1:]
    if arg[:2] == '-P'
    if (tmp := [arg[2:]] if ',' not in arg else arg[2:].split(',')) or True
    for subarg in tmp
] # yapf: disable
top_arg = [
    int(arg[2:])
    for arg in sys.argv[1:]
    if arg[:2] == '-T'
] # yapf: disable
if top_arg:
    top_arg = top_arg[0]
simc_output_arg = [
    bool(arg)
    for arg in sys.argv[1:]
    if arg[:2] == '-O'
] # yapf: disable
if simc_output_arg:
    simc_output_arg = simc_output_arg[0]

with open('details.json') as handle:
    data = json.load(handle)
print(f'Generated at: {data.get("generated")}', file=sys.stderr)
if filter_args:
    print(f'Matching for: {filter_args}', file=sys.stderr)
if sort_args:
    print(f'Sorting on: {sort_args}', file=sys.stderr)
if print_args:
    print(f'Filtering fields on: {print_args}', file=sys.stderr)
if top_arg:
    print(f'Returning top {top_arg} results.', file=sys.stderr)

profiles = [
    {
        key.upper() if hasattr(key, 'upper') else key: value
        for key, value in entry.items()
    }
    for entry in data.get('data')
    if all([v in [n.upper() for n in entry.values() if hasattr(n, 'upper')] for v in filter_args])
]
print(f'Found {len(profiles)} matching entries.', file=sys.stderr)

if sort_args:
    profiles = sorted(
        profiles,
        key=lambda e: tuple((e[k] for k in sort_args if k in e.keys())),
        reverse=True
    )

if top_arg:
    profiles = profiles[:top_arg]

print(f'Printing {len(profiles)} profile{"s" if len(profiles) > 1 else ""}:',
      file=sys.stderr)

def process_value(value):
    if isinstance(value, list):
        return '/'.join([str(v) for v in value])
    return value
def process_key(key):
    key_map = {
        'bonusLists': 'bonus_id',
        'craftedStats': 'crafted_stats'
    }
    if key in key_map.keys():
        return key_map[key]
    return key

for entry in profiles:
    print(f'ID: {entry.get("ID")}',
        file=sys.stdout if not simc_output_arg else sys.stderr)
    for key, value in entry.items():
        if key != 'ID' and key in print_args:
            print(f'  {key}: {value}',
                  file=sys.stdout if not simc_output_arg else sys.stderr)
    if simc_output_arg:
        filter_keys = ['averageItemLevel', 'averageItemLevelEquipped', 'shirt', 'tabard']
        filter_item_params = ['name', 'context', 'quality', 'icon', 'itemLevel']
        reshape_gear = [
            f'{slot_name}='+','.join(
                [snakecase(data.get('name', ''))] + [
                    f'{process_key(key)}={process_value(value)}'
                    for key, value in data.items()
                    if value and key not in filter_item_params
                ])
            for slot_name, data in entry.get('GEAR', {}).items()
            if slot_name not in filter_keys
        ]
        print('  stdout:', file=sys.stderr)
        print(f'# Start ID: {entry.get("ID")}')
        for key, value in entry.items():
            if key != 'ID' and key in print_args:
                print(f'# {key}: {value}')
        print(f'{entry.get("CLASS", "").lower()}="{entry.get("ID")}"')
        print(f'spec={entry.get("SPEC")}')
        print(f'talents={entry.get("TALENTS")}')
        for item in reshape_gear:
            print(item)
        print(f'# End ID: {entry.get("ID")}\n')
