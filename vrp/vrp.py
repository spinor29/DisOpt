#!/usr/bin/python

# Vehicle routing problem
# Given a list of locations N = 0...n-1, location 0 is the warehouse location where all of the vehicles start and end their routes. The remaining locations are customers. Each location is characterized by a demand d_i, and coordinates (x_i, y_i). The fleet of vehicles V = 0...v-1 is fixed and each vehicle has a limited capacity c. Find a route for each vehicle so that all of the customers are served by exactly one vehicle and the travel distance of the vehicles is minimized.

# Formulation:
# Minimize:
# \sum_{j = 0...v-1} ( \sum_{e in E_j} dist_e * z_e )   # E_j is a set of edges  formed by warehouse and those customers served by vehicle j
# Subject to:
# (\sum_(i = 1...n-1) d_j h_i,j) <= c_j for j in 0...v-1  # Capacity constraint
# (\sum_(j = 0...v-1) h_i,j) = 1 for i in 1...n-1  # each customer is served by exactly one vehicle
# h_i,j = {0, 1}  # i: customer index, j: vehicle index
# z_\delta(i = 0) <= 2 * v # number of edges that have end point warehouse 0
# z_\delta(i) = 2 for i != 0 # number of edges that have end point customer i
# z_\delta(S) >= 2 for S in V  # number of edges that have exactly one end point in S and one end point in V-S. This is the subtour elimination constraint.
# z_e = {0, 1}, for e in E_j

# The vehicle routing problem is essentially a combination of multi-knapsacks problem and traveling salesman problem.

# Here I use the simulated annealing algorithm to find the optimal routes.

import math
from collections import namedtuple

Customer = namedtuple("Customer", ['index', 'demand', 'x', 'y'])
Point = namedtuple("Point", ['x', 'y'])

def length(customer1, customer2):
    return math.sqrt((customer1.x - customer2.x)**2 + (customer1.y - customer2.y)**2)

import random
def ori_init(alist, points):
    # Start from origin and connect to nearest neighbor if possible
    blist = list(alist)
    clist = []
    p = random.randrange(0, len(blist)) # starting point
    #p = 0
    clist.append(p)
    blist.remove(p)
    while (len(blist) > 0):
        dmin = 1e20
        qmin = blist[0]
        # Find the nearest neighbor to p
        for q in blist:  
            dis = length(points[p],points[q])
            if dmin > dis:
                dmin = dis
                qmin = q
        p = qmin
        clist.append(p)
        blist.remove(p)
    return clist

def kopt2(vehicle_t, points, obj_kopt):
    for i_tour in range(0,len(vehicle_t)):
        swaplist = list(vehicle_t[i_tour])
        swaplist = [0] + swaplist + [0]
        swapped = 1
        while (swapped > 0):
            swapped = 0
            for i in range(1, len(vehicle_t[i_tour])):
                j_diff = []
                diff_min = 1e20
                j_min = 0
                for j in range(i+1, len(vehicle_t[i_tour])+1):
                    cost1 = length(points[swaplist[i-1]], points[swaplist[i]]) + length(points[swaplist[j]], points[swaplist[j+1]])
                    cost2 = length(points[swaplist[i-1]], points[swaplist[j]]) + length(points[swaplist[i]], points[swaplist[j+1]])
                    diff_cost = cost2 - cost1
                    if diff_cost < 0: # find the best swap for all j
                        j_diff.append([j, diff_cost])
                        if diff_min > diff_cost:
                            diff_min = diff_cost
                            j_min = j
                if len(j_diff) > 0: # swap i and j_min
                    swaplist[i], swaplist[j_min] = swaplist[j_min], swaplist[i]
                    swaplist[i+1:j_min] = swaplist[j_min-1:i:-1]
                    obj_kopt += diff_min
                    swapped += 1
        vehicle_t[i_tour] = swaplist[1:-1]

    
    obj_test = 0
    for v in range(0, len(vehicle_t)):
        vehicle_tour = vehicle_t[v]

        if len(vehicle_tour) > 0:
            obj_test += length(points[0],points[vehicle_tour[0]])
            for i in range(0, len(vehicle_tour)-1):
                obj_test += length(points[vehicle_tour[i]],points[vehicle_tour[i+1]])
            obj_test += length(points[vehicle_tour[-1]],points[0])
    
    if abs(obj_kopt - obj_test) > 1.e-6:
        print "obj_kopt not equal to obj_test!!!"
        print
    return obj_kopt

def rand_interswap(vehicle_t, points, vc, obj, t):
    # Swap two customers allocated to different vehicles
    v1 = vc[0][0]
    v2 = vc[1][0]
    swaplist1 = list(vehicle_t[v1])
    swaplist1 = [0] + swaplist1 + [0]
    swaplist2 = list(vehicle_t[v2])
    swaplist2 = [0] + swaplist2 + [0]
    c1 = vc[0][1]  # c1 = 1 is the first customer on the vehicle 
    c2 = vc[1][1]

    cost1 = length(points[swaplist1[c1-1]], points[swaplist1[c1]]) + length(points[swaplist1[c1]], points[swaplist1[c1+1]]) \
            + length(points[swaplist2[c2-1]], points[swaplist2[c2]]) + length(points[swaplist2[c2]], points[swaplist2[c2+1]])
    cost2 = length(points[swaplist1[c1-1]], points[swaplist2[c2]]) + length(points[swaplist2[c2]], points[swaplist1[c1+1]]) \
            + length(points[swaplist2[c2-1]], points[swaplist1[c1]]) + length(points[swaplist1[c1]], points[swaplist2[c2+1]])
    diff_cost = cost2 - cost1
    
    n = len(points)
    k = obj/n/5
    bkt = -diff_cost/(k*t)
    bkt_max = 708. # set a maximum for exponent
    if (bkt > bkt_max): # to avoid overflow error
        p = 1.
    else:
        pf = math.exp(bkt)
        p = pf/(pf+1.)
    x = random.random()
    #if (diff_len > 0):
    if (x <= p): # swap, vehicle_t[v][0] is the first customer on vehicle v

        vehicle_t[v1][c1-1], vehicle_t[v2][c2-1] = vehicle_t[v2][c2-1], vehicle_t[v1][c1-1]
        #print "obj improved by random swap, with change of ", diff_cost
        obj += diff_cost
    return obj                


def rand_swap(vehicle_t, points, vc, obj, t):
    # Swap orders of customers allocated to a vehicle
    swaplist = list(vehicle_t[vc[0][0]])
    swaplist = [0] + swaplist + [0]
    c1 = vc[0][1]  # c1 = 1 is the first customer on the vehicle 
    c2 = vc[1][1]

    cost1 = length(points[swaplist[c1-1]], points[swaplist[c1]]) + length(points[swaplist[c2]], points[swaplist[c2+1]])
    cost2 = length(points[swaplist[c1-1]], points[swaplist[c2]]) + length(points[swaplist[c1]], points[swaplist[c2+1]])
    diff_cost = cost2 - cost1
    
    n = len(points)
    k = obj/n/5
    bkt = -diff_cost/(k*t)
    bkt_max = 708. # set a maximum for exponent
    if (bkt > bkt_max): # to avoid overflow error
        p = 1.
    else:
        pf = math.exp(bkt)
        p = pf/(pf+1.)
    x = random.random()

    if (x <= p): # swap, vehicle_t[v][0] is the first customer on vehicle v

        vehicle_t[vc[0][0]][c1-1], vehicle_t[vc[0][0]][c2-1] = vehicle_t[vc[0][0]][c2-1], vehicle_t[vc[0][0]][c1-1]
 
        vehicle_t[vc[0][0]][c1:c2-1] = vehicle_t[vc[0][0]][c2-2:c1-1:-1]

        #print "obj improved by random swap, with change of ", diff_cost
        obj += diff_cost
    return obj

import copy


def rand_insert(vehicle_t, points, vehicle_capacity, vc, obj, t):
    # Move a customer to a different running vehicle
    v1 = vc[0][0]
    c1 = vc[0][1] # c1 is the customer to be removed from v1
    tmplist = list(vehicle_t[v1])
    tmplist = [0] + tmplist + [0]
    cost1 = length(points[tmplist[c1-1]], points[tmplist[c1]]) + length(points[tmplist[c1]], points[tmplist[c1+1]])
    cost2 = length(points[tmplist[c1-1]], points[tmplist[c1+1]])
    diff_cost = cost2 - cost1
    
    v2 = vc[1][0]
    c2 = vc[1][1]
    tmplist = []
    tmplist = list(vehicle_t[v2])
    tmplist = [0] + tmplist + [0]
    m = random.randrange(0, 2)
    
    if m == 0: # add customer c1 to v2 before c2

        tmplist.insert(c2, vehicle_t[v1][c1-1])
        cost1 = length(points[tmplist[c2-1]], points[tmplist[c2+1]])
        cost2 = length(points[tmplist[c2-1]], points[tmplist[c2]]) + length(points[tmplist[c2]], points[tmplist[c2+1]])
    else: # add customer c1 to v2 after c2

        tmplist.insert(c2+1, vehicle_t[v1][c1-1])
        cost1 = length(points[tmplist[c2]], points[tmplist[c2+2]])
        cost2 = length(points[tmplist[c2]], points[tmplist[c2+1]]) + length(points[tmplist[c2+1]], points[tmplist[c2+2]])

    diff_cost += cost2 - cost1
    
    # Use 2-opt method or not
    
    y = random.random()
    if (t < 0.01) & (y < 0.1):
        flag_kopt2 = True
    else:
        flag_kopt2 = False
    
    if flag_kopt2 == True:
        vehicle_tmp = copy.deepcopy(vehicle_t)
        customer_moving = vehicle_tmp[v1][c1-1]
        vehicle_tmp[v1].remove(customer_moving)
        if m == 0: 
            vehicle_tmp[v2].insert(c2-1, customer_moving)
        else:
            vehicle_tmp[v2].insert(c2, customer_moving)
        obj_tmp = obj
        obj_tmp += diff_cost
        if len(vehicle_tmp[v1]) == 0:
            vehicle_tmp.remove(vehicle_tmp[v1])

        obj_tmp = kopt2(vehicle_tmp,points,obj_tmp) # use 2-opt method
    
        diff_cost = obj_tmp - obj
    
    #return obj
    
    n = len(points)
    k = obj/n/5
    bkt = -diff_cost/(k*t)
    bkt_max = 708. # set a maximum for exponent
    if (bkt > bkt_max): # to avoid overflow error
       p = 1.
    else:
        pf = math.exp(bkt)
        p = pf/(pf+1.)
    x = random.random()
    
    if flag_kopt2 == True:
        if (x <= p):
            vehicle_t[:] = vehicle_tmp[:]
            obj = obj_tmp
        return obj  
    
    #if (diff_len > 0):
    if (x <= p): # move, vehicle_t[v][0] is the first customer on vehicle v
        
        customer_moving = vehicle_t[v1][c1-1]
        vehicle_t[v1].remove(customer_moving)
 
        if m == 0: 
            vehicle_t[v2].insert(c2-1, customer_moving)
        else:
            vehicle_t[v2].insert(c2, customer_moving)
        
        obj += diff_cost
        
        if len(vehicle_t[v1]) == 0:
            vehicle_t.remove(vehicle_t[v1])
    return obj

def rand_addvehicle(vehicle_t, points, v, c, obj, t):
    # Move customer to an empty vehicle
    tmplist = list(vehicle_t[v])
    tmplist = [0] + tmplist + [0]
    cost1 = length(points[tmplist[c-1]], points[tmplist[c]]) + length(points[tmplist[c]], points[tmplist[c+1]])
    cost2 = length(points[tmplist[c-1]], points[tmplist[c+1]])
    diff_cost = cost2 - cost1
    
    diff_cost += 2.0 * length(points[0], points[tmplist[c]])
    
    # make a copy of vehicle tours to find the best route for the assignment
    vehicle_tmp = copy.deepcopy(vehicle_t)
    customer_moving = vehicle_tmp[v][c-1]
    vehicle_tmp[v].remove(customer_moving)
    vehicle_tmp.append([customer_moving])
    
    if len(vehicle_tmp[v]) == 0:
        vehicle_tmp.remove(vehicle_tmp[v])
        
    obj_tmp = obj
    obj_tmp += diff_cost
    if len(vehicle_tmp[v]) == 0:
        vehicle_tmp.remove(vehicle_tmp[v])

    obj_tmp = kopt2(vehicle_tmp,points,obj_tmp) # use 2-opt method
    
    diff_cost = obj_tmp - obj
    
    
    n = len(points)
    k = obj/n/5
    bkt = -diff_cost/(k*t)
    bkt_max = 708. # set a maximum for exponent
    if (bkt > bkt_max): # to avoid overflow error
        p = 1.
    else:
        pf = math.exp(bkt)
        p = pf/(pf+1.)
    x = random.random()
    
    if (x <= p):
        vehicle_t[:] = vehicle_tmp[:]
        obj = obj_tmp
    return obj
 
    
    if (x <= p): # move, vehicle_t[v][0] is the first customer on vehicle v
        customer_moving = vehicle_t[v][c-1]
        vehicle_t[v].remove(customer_moving)
        
        vehicle_t.append([customer_moving])
        if len(vehicle_t[v]) == 0:
            vehicle_t.remove(vehicle_t[v])
        
        obj += diff_cost
        #print "obj improved by adding a vehicle, with change of ", diff_cost
    
    return obj
    
def rand_move(vehicle_t, points, customers, vehicle_count, vehicle_capacity, obj, t):
    n = len(points)
    c1 = random.randrange(0,n)
    c2 = c1
    while (c2 == c1):
        c2 = random.randrange(0, n)

    v1 = 0 # vehicle number in which a first customer is to be moved
    v2 = 0
    vc = []
    
    if (c1 != 0) & (c2 != 0):
        while c2 > len(vehicle_t[v2]):
            c2 -= len(vehicle_t[v2])
            v2 += 1
        while c1 > len(vehicle_t[v1]):
            c1 -= len(vehicle_t[v1])
            v1 += 1

        if (v1 == v2):
            # Swap orders of customers allocated to a running vehicle
            [ c1, c2 ] = sorted([c1,c2])
            vc = [[v1, c1], [v2, c2]]
            obj = rand_swap(vehicle_t, points, vc, obj, t)
        else:
            # Swap customers allocated to different vehicles if capacity allowed
            vc = [[v1, c1], [v2, c2]]
            #print "vc = ", vc
            capacity_used = 0
            for j in range(0, len(vehicle_t[v2])):
                capacity_used += customers[vehicle_t[v2][j]].demand

            if customers[vehicle_t[v1][c1-1]].demand <= (vehicle_capacity - capacity_used):
                obj = rand_insert(vehicle_t, points, vehicle_capacity, vc, obj, t)
            else:
                if (customers[vehicle_t[v1][c1-1]].demand - customers[vehicle_t[v2][c2-1]].demand) <= (vehicle_capacity - capacity_used):
                    capacity_used = 0
                    for j in range(0, len(vehicle_t[v1])):
                        capacity_used += customers[vehicle_t[v1][j]].demand
                    if (customers[vehicle_t[v2][c2-1]].demand - customers[vehicle_t[v1][c1-1]].demand) <= (vehicle_capacity - capacity_used):
                        obj = rand_interswap(vehicle_t, points, vc, obj, t)
    else:
        # Move customer from v1 to v2 if v1 has more than one customer and there is an empty vehicle v2
        [ c1, c2 ] = sorted([c1,c2])
        while c2 > len(vehicle_t[v2]):
            c2 -= len(vehicle_t[v2])
            v2 += 1
            
        if (len(vehicle_t) < vehicle_count) & (len(vehicle_t[v1]) > 1): # if there is an empty vehicle
            obj = rand_addvehicle(vehicle_t, points, v2, c2, obj, t)
    
    return obj

def solve_it(input_data):
    # Parse the input data (N: number of locations including warehouse 0, V: number of vehicle, c: vehicle capacity, d_i: demand of customer i, [x,y]: coordinates):
    # N V c
    # d_0 x_0 y_0
    # d_1 x_1 y_1
    # ...
    # d_N-1, x_N-1, y_N-1
    
    lines = input_data.split('\n')

    parts = lines[0].split()
    customer_count = int(parts[0])
    vehicle_count = int(parts[1])
    vehicle_capacity = int(parts[2])
    
    customers = []
    points = []
    for i in range(1, customer_count+1):
        line = lines[i]
        parts = line.split()
        customers.append(Customer(i-1, int(parts[0]), float(parts[1]), float(parts[2])))
        points.append(Point(float(parts[1]), float(parts[2])))

    #the depot is always the first customer in the input
    depot = customers[0]
    templist = range(0, customer_count) 
    
    # Considering no capacity constraint and start from origin then connect to nearest neighbor (like traveling salesman problem)
    
    templist = ori_init(templist, points)
    templist.remove(0)
    vehicle_tours = []
    v_used = 1
    cust_on_vehi = []
    capacity_remaining = vehicle_capacity
    
    for v in range(vehicle_count):
        capacity_remaining = vehicle_capacity
        cust_on_vehi = []
        for i in templist:
            if capacity_remaining >= customers[i].demand:
                cust_on_vehi.append(i)
                capacity_remaining -= customers[i].demand
            #else:
        if len(cust_on_vehi) > 0:
            vehicle_tours.append(cust_on_vehi)
            
        for i in range(len(cust_on_vehi)):
            templist.remove(cust_on_vehi[i])
    
    if templist != []:
        print "Error! Some customers were not on a vehicle route!"
        return 0
    
    #print vehicle_tours
    
    obj_min = 1.e20
    solution_min = []
    # Start annealing cycle
    for j in range(3):
        print "Annealing cycle", j+1
        obj = 0
        temp = 0
        # calculate the length of the tour
        for tour in vehicle_tours:
            obj += length(points[0], points[tour[0]])
            for i in range(0, len(tour)-1):
                obj += length(points[tour[i]], points[tour[i+1]])
            obj += length(points[tour[-1]], points[0])
        
        nmove = 300000
        
        t = 1. # temperature-like scale, the smaller, the lower temperature
        for t in [5., 4., 3., 2., 1.8, 1.5, 1.3, 1.2, 1.1, 1., 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05, 0.03, 0.02, 0.015, 0.01, 0.0075, 0.005]:
        #for t in [1]:
            converge = True
            print "T scale:", t, " minimum so far:", obj_min
            # Random move
            for i in range(nmove):
                obj = rand_move(vehicle_tours, points, customers, vehicle_count, vehicle_capacity, obj, t)
                if (i % 20000 == 0): print "Iteration", i, " obj value:", obj
                
                if (i % 20000 == 0):
                    if abs(temp - obj) > 1.e-8:
                        converge = False
                        
                if obj_min > obj:
                    obj_min = obj
                    solution_min = copy.deepcopy(vehicle_tours)
            print
            temp = obj
            if converge: break

    print "Routes for minimize travel distance of vehicles:"
    for v in range(0, len(solution_min)):
        print "Vehicle", v, " :", ' '.join(str(cus) for cus in solution_min[v])
    print "Travel distance: ", obj_min
    
    return

import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        input_data_file = open(file_location, 'r')
        input_data = ''.join(input_data_file.readlines())
        input_data_file.close()
        print 'Solving:', file_location
        solve_it(input_data)
    else:
        print 'This test requires an input file. (For example: python solver.py vrp_20.txt)'

