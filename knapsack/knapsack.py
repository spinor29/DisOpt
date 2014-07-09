#!/usr/bin/python
# -*- coding: utf-8 -*-

# Knapsack problem
# Given n items to choose from, each item has a value of v_i and a weight w_i.
# How should one fill a knapsack with a limited capacity K so that the total
# value of the items in the knapsack is maximized?

# Formulation:
# Maximize: \sum (v_i * x_i)
# Subject to: \sum (w_i * x_i) <= K
#             x_i = 0 or 1

# Solution:
# 1) Use linear relaxation, i.e. assume items can be fractionalized, and
# calculate the total value in the knapsack if filling with items in descending 
# orders of value/weight till reaching capacity. Then this total value in the 
# knapsack is the upper bound.
# 2) If the last item filled in the knapsack is fractionalized, branch the item
# to 0 and 1, and continue the filling with other items and repeat the process.
# 3) Keep track of the maximum value, v_max, of the successful filling.
# Prune the node if the upper bound value of a branch is less than v_max.

from collections import namedtuple
Item = namedtuple("Item", ['index', 'value', 'weight', 'ratio'])
taken = []

# Calculate optimal value with linear relaxation.
# 'items' is a list with elements sorted by the order of value/weight.
def opt(items, capacity):
    weight = 0
    optv = 0
    taken_depth = [0]*len(items)
    for item in items:
        if weight + item.weight < capacity:
            optv += item.value
            weight += item.weight
        else:
            optv += item.value * float(capacity-weight)/item.weight
            break
    return optv


# Branch and bound
def depthfirst(items, m, maxvalue, opttaken, valuetaken, nowtaken, capacity):
    # In the case that item m is selected
    if items[m].weight <= capacity: # Here capacity means the remaining capacity
        subcapacity = capacity - items[m].weight
        newvaluetaken = valuetaken + items[m].value
        nowtaken[items[m].index] = 1
        if m < len(items)-1:
            maxvalue = depthfirst(items, m+1, maxvalue, opttaken, newvaluetaken, nowtaken, subcapacity)
        else:
            if newvaluetaken > maxvalue:
                maxvalue = newvaluetaken
                opttaken[:] = nowtaken[:]
 
    # In the case that item m is not selected
    nowtaken[items[m].index] = 0
    if m < len(items)-1:
        subitems = items[m+1:len(items)] 
        optvalue = valuetaken + opt(subitems, capacity)
        if optvalue > maxvalue:
            maxvalue = depthfirst(items, m+1, maxvalue, opttaken, valuetaken, nowtaken, capacity)
    else:
        if valuetaken > maxvalue:
            maxvalue = valuetaken
            opttaken[:] = nowtaken[:]    
    return maxvalue
 
 
def solve_it(input_data):
    # Parse the input data, which contains:
    # n K
    # v_0 w_0
    # v_1 w_1
    # ...
    # v_n-1 w_n-1
    
    lines = input_data.split('\n')

    firstLine = lines[0].split()
    item_count = int(firstLine[0])
    capacity = int(firstLine[1])

    items = []

    for i in range(1, item_count+1):
        line = lines[i]
        parts = line.split() # v_i, w_i
        items.append(Item(i-1, int(parts[0]), int(parts[1]), float(parts[0])/float(parts[1])))

    sorted(items, key = lambda x: x.ratio) # Sort items by ratio of value/weight
    

    # Use branch and bound algorithm with linear relaxation
    value = 0
    weight = 0
    taken = [0]*len(items)
    temptaken = [0]*len(items)

    optvalue = opt(items, capacity)

    m = 0
    maxvalue = 0
    valuetaken = 0
    maxvalue = depthfirst(items, m, maxvalue, taken, valuetaken, temptaken, capacity)

    chosen = []
    for item in items:
        if taken[item.index] == 1:
            value += item.value
            chosen.append(item.index)
    
    print "To maximize the value of the knapsack, choose items:"
    print chosen
    print "Maximum value: ", value
    
    return

import sys
sys.setrecursionlimit(100000)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        input_data_file = open(file_location, 'r')
        input_data = ''.join(input_data_file.readlines())
        input_data_file.close()
        solve_it(input_data)
    else:
        print 'This test requires an input file. (For example: python knapsack.py ks.txt)'

