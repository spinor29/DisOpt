#!/usr/bin/python

# Traveling salesman problem
# Given n nodes, find the shortest contour that travels each node exactly once.

# My solution is using simulated annealing to find the minimum

import math
from collections import namedtuple

Point = namedtuple("Point", ['x', 'y'])

def length(point1, point2):
    return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

import random

def rand_init(alist, points):
    # Randomly start from a point and connect to nearest neighbor if possible
    blist = list(alist)
    clist = []
    p = random.randrange(0, len(blist)) # starting point
    clist.append(p)
    blist.remove(p)
    while (len(blist) > 0):
        dmin = 1e20
        qmin = blist[0]
        # Find nearest neighbor to p
        for q in blist:  
            dis = length(points[p],points[q])
            if dmin > dis:
                dmin = dis
                qmin = q
        p = qmin
        clist.append(p)
        blist.remove(p)
        #print "length of blist = ", len(blist)
    return clist      

def rand_swap(alist, points, obj, t):
    n = len(alist) # number of elements in the list
    u = random.randrange(0, n)
    v = u
    while (v == u):
        v = random.randrange(0, n)
    [ u, v ] = sorted([u,v])

    # Calculate lengths of node(u-1)-node(u)-node(u+1) + node(u-1)-node(u)-node(u+1), before and after swap
    uv_len = [0., 0.] # uv_len[0] is the value before swap, uv_len[1] after swap

    if v != (n-1) :
        a = [ alist[u-1], alist[v+1] ]
    else:    
        a = [ alist[u-1], alist[0] ]
    
    if (u == 0) & (v == (n - 1)):
        uv_len[0] += length(points[alist[u]], points[alist[u+1]]) + length(points[alist[v]], points[alist[v-1]])
        uv_len[1] += length(points[alist[v]], points[alist[u+1]]) + length(points[alist[u]], points[alist[v-1]])
    else:
        uv_len[0] += length(points[a[0]], points[alist[u]]) + length(points[alist[v]], points[a[1]])
        uv_len[1] += length(points[a[0]], points[alist[v]]) + length(points[alist[u]], points[a[1]])
    diff_len = uv_len[1] - uv_len[0]

    k = obj/n/5. # scaled average distance between adjacent nodes

    bkt = -diff_len/(k*t) # exponent for partition function, aka (\beta k_B T)
    bkt_max = 708. # set a maximum for exponent
    if (bkt > bkt_max): # to avoid overflow error
        p = 1.
    else:
        pf = math.exp(bkt)
        p = pf/(pf+1.)
    x = random.random()

    if (x <= p): # swap
        if (u == 0) & (v == (n - 1)):
            alist[u], alist[v] = alist[v], alist[u]
        else:
            alist[u], alist[v] = alist[v], alist[u]
            alist[u+1:v] = alist[v-1:u:-1] 
    
        #print "    obj impoved with change of ", diff_len
        obj += diff_len

    return obj     

def solve_it(input_data):
    # Parse the input data:
    # n
    # x_0, y_0
    # x_1, y_1
    # ...
    # x_n-1, y_n-1
    
    lines = input_data.split('\n')

    nodeCount = int(lines[0])

    print "Solving traveling salesman problem..."
    print "Number of nodes: ", nodeCount, "\n"
    
    points = []
    for i in range(1, nodeCount+1):
        line = lines[i]
        parts = line.split()
        points.append(Point(float(parts[0]), float(parts[1])))


    obj_min = 1.e20
    solution_min = range(0,nodeCount)
    
    # Start Annealing cycle
    for j in range(2):
        print "Annealing", j+1, ":"
        solution = range(0, nodeCount)
        
        # Starting from a random point and connect to its nearest neighbor
        solution = rand_init(solution, points)

        # Calculate the length of the tour
        obj = length(points[solution[-1]], points[solution[0]])
        for index in range(0, nodeCount-1):
            obj += length(points[solution[index]], points[solution[index+1]])

        # Use random swap algorithm    
        nswap = 2000000 # increase nswap for larger node count
        t = 1. # temperature-like scale, the smaller, the lower temperature
        for t in [2., 1.5, 1.2, 1., 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05, 0.03, 0.02, 0.01, 0.005]:
            converge = True
            temp = obj
            print "T scale:", t, " minimum so far: ", obj_min
            for i in range(nswap):
                obj = rand_swap(solution, points, obj, t)

                if (i % 200000 == 0):
                    print "Iteration", i, ", obj value:", obj
                    
                if (i % 200000 == 0):
                    if (abs(obj - temp) > 1e-6): converge = False
                    temp = obj
                
                if obj_min > obj:
                    obj_min = obj
                    solution_min = list(solution)
                    
            print
            
            if converge: break

    print "Shortest route: ", ' '.join(map(str, solution_min))
    print "Total distance: ", obj_min
    
    return

import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        input_data_file = open(file_location, 'r')
        input_data = ''.join(input_data_file.readlines())
        input_data_file.close()
        solve_it(input_data)
    else:
        print 'This test requires an input file (For example: python solver.py tsp_50.txt).'

