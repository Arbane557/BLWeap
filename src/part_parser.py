import json
import os

def load_parts(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)

def load_all_parts(filepaths):
    all_parts = []
    for path in filepaths:
        all_parts.extend(load_parts(path))
    return all_parts

def filter_parts_by_type(parts, part_type):
    return [p for p in parts if p["type"] == part_type]