######################################
#
# DBM.py 
#
# Difference bound matrices domain
#
######################################

import numbers
import abc
import copy
from graph_algorithms import WeightedGraph

class DBM(WeightedGraph):

    def __init__(self):
        self.nodes = []
        self.outgoings = {}
        self.incomings = {}

    def copy(self):
        result = DBM()
        result.nodes = self.nodes[:]
        result.outgoings = {}
        for node in self.outgoings:
            result.outgoings[node] = []
            for (weight, target) in self.outgoings[node]:
                result.outgoings[node].append((weight, target))
        result.incomings = {}
        for node in self.incomings:
            result.incomings[node] = []
            for (source, weight) in self.incomings[node]:
                result.incomings[node].append((source, weight))
        print result.to_string()
        return result

    def set_weight(self, source, weight, target):
        if source not in self.nodes:
            self.nodes.append(source)
            self.outgoings[source] = []
            self.incomings[source] = []
        if target not in self.nodes:
            self.nodes.append(target)
            self.outgoings[target] = []
            self.incomings[target] = []
        found = False
        for (existing_weight, existing_target) in self.outgoings[source]:
            if existing_target == target:
                self.outgoings[source].remove((existing_weight, existing_target))
                if weight is not None:
                    self.outgoings[source].append((weight, target))
                found = True
                break
        if not found and weight is not None:
            self.outgoings[source].append((weight, target))
        found = False
        for (existing_source, existing_weight) in self.incomings[target]:
            if existing_source == source:
                self.incomings[target].remove((existing_source, existing_weight))
                if weight is not None:
                    self.incomings[target].append((source, weight))
                found = True
                break
        if not found and weight is not None:
            self.incomings[target].append((source, weight))
    
    def all_nodes(self):
        return self.nodes

    def incomings(self, node):
        return self.incomings[node]
    
    def outgoings(self, node):
        return self.outgoings[node]

    def get_weight(self, source, target):
        ''' Get the weight of the edge between source and target,
        None for infinite weight. '''
        if source not in self.nodes or target not in self.nodes:
            return None
        for (weight, existing_target) in self.outgoings[source]:
            if existing_target == target:
                return weight
        return None

    def exists_negative_cycle(self):
        # add an artificial node None
        distance = {}
        predecessor = {}
        # Use Bellman-Ford
        for node in self.nodes[:]:
            self.set_weight(None, 0, node)
            # init dicts
            distance[node] = None
            predecessor[node] = None
        distance[None] = 0
        i = len(self.nodes)-1
        while(i > 0):
            # iterate all edges
            for source in self.nodes:
                for (weight, target) in self.outgoings[source]:
                    if weight is None:
                        continue # to be sure...
                    source_distance = distance[source]
                    target_distance = distance[target]
                    if source_distance is None:
                        continue
                    elif (target_distance is None
                          or source_distance + weight < target_distance):
                        distance[target] = distance[source] + weight
                        predecessor[target] = source
            i -= 1
        # check for cycles
        negative_cycle = False
        for source in self.nodes:
            for (weight, target) in self.outgoings[source]:
                source_distance = distance[source]
                target_distance = distance[target]
                if source_distance is None:
                    continue
                elif (target_distance is None
                      or source_distance + weight < target_distance):
                    print "Negative cycle existing."
                    negative_cycle = True
                    break
        for node in self.nodes[:]:
            if node is not None:
                self.set_weight(None, None, node)
        return negative_cycle
                
    def find_shortest_paths(self):
        # Return a dbm with shortest path as entries
        sp = self.copy()
        i = 1

        def add_weights(w1, w2):
            if w1 is None or w2 is None:
                return None
            else:
                return w1 + w2

        def min_extended(m1, m2):
            if m1 is None:
                return m2
            elif m2 is None:
                return m1
            return min(m1, m2)
        
        for node in self.nodes:
            for source in self.nodes:
                for target in self.nodes:
                    distance = min_extended(
                        sp.get_weight(source, target),
                        add_weights(sp.get_weight(source, node),
                                    sp.get_weight(node, target)))
                    sp.set_weight(source,
                                  distance,
                                  target)
        # adjust diagonals
        for node in self.nodes:
            sp.set_weight(node, 0, node)
        return sp           
        
    def to_string(self):
        ''' Get a textual representation of the DBM graph. '''
        result = ''
        for node in self.nodes:
            if node is None:
                continue # private node
            result += 'node: %s\n' % node
            for (weight, target) in self.outgoings[node]:
                result += '%s -(%s)-> %s\n' % (node, weight, target)
            for (source, weight) in self.incomings[node]:
                result += '%s <=(%s)= %s\n' % (node, weight, source)
        return result
    