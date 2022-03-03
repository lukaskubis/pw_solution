# solution.py

import argparse
import csv
import json

from collections import defaultdict
from copy import deepcopy
from datetime import datetime as dt, timedelta as td

MIN_LAYOVER = td(hours=1)
MAX_LAYOVER = td(hours=6)


def parse_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='Dataset location.')
    parser.add_argument('origin', help='Origin airport.')
    parser.add_argument('destination', help='Destination airport.')
    parser.add_argument('-b', '--bags', type=int, default=0, help='Number of selected bags.')
    parser.add_argument('-r', '--return', action='store_true', dest='_return', help='Return journey?')

    return parser.parse_args()


def convert_flight(flight: dict) -> dict:
    flight['base_price'] = float(flight['base_price'])
    flight['bag_price'] = int(flight['bag_price'])
    flight['bags_allowed'] = int(flight['bags_allowed'])
    return flight


def read_csv_file(csv_file: str) -> list:
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        return [convert_flight(f) for f in reader]


def make_graph(flights: list) -> dict:
    graph = defaultdict(list)
    for flight in flights:
        graph[flight['origin']].append(flight)
    return graph


def get_flight_travel_time(flight):
    return dt.fromisoformat(flight['arrival']) - dt.fromisoformat(flight['departure'])


def make_journey(flights, args):
    base_price = sum([f['base_price'] for f in flights])
    total_price = base_price + (sum([f['bag_price'] for f in flights]) * args.bags)

    travel_dep = dt.fromisoformat(flights[0]['departure'])
    travel_arr = dt.fromisoformat(flights[-1]['arrival'])

    return {
        'flights': flights,
        'origin': flights[0]['origin'],
        'destination': flights[-1]['destination'],
        'bags_count': args.bags,
        'bags_allowed': min([f['bags_allowed'] for f in flights]),
        'total_price': total_price,
        'travel_time': str(travel_arr - travel_dep)
    }


def get_lay_time(fa, fb):
    _dt = lambda x: dt.fromisoformat(x)
    return _dt(fb['departure']) - _dt(fa['arrival'])


def dfs(graph, flights, journeys, visited, args):
    start = args.origin

    if flights:
        latest = flights[-1]
        start = latest['destination']
        if start == args.destination:
            j = make_journey(deepcopy(flights), args)
            journeys.append(j)
            return

    for f in graph[start]:
        if f['destination'] in visited or f['bags_allowed'] < args.bags:
            continue

        if flights and not (MIN_LAYOVER <= get_lay_time(latest, f) < MAX_LAYOVER):
            continue

        visited.append(f['destination'])
        flights.append(f)

        dfs(graph, flights, journeys, visited, args)
        visited.pop()
        flights.pop()


def search(graph: dict, args) -> list:
    valid_locations = (args.origin in graph and args.destination in graph)
    if not valid_locations:
        return

    current = []
    journeys = []
    visited = [args.origin]

    dfs(graph, current, journeys, visited, args)

    return journeys


if __name__ == '__main__':
    args = parse_cli()
    flights = read_csv_file(args.file)
    graph = make_graph(flights)
    journeys = sorted(search(graph, args), key=lambda x: x['total_price'])
    print(json.dumps(journeys, indent=2))
