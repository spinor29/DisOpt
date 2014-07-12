#!/usr/bin/python

# Facility location problem
# Given N facilities and M customers, each facility f has a setup cost s_f and
# a capicity C_f, and each customer has a demand D_c. All customers must be
# served by exactly 1 facility. The cost to deliver goods to a particular
# customer from a facility is the distance between their locations.
# 
# Find which facilities serve which customers so that the total cost is
# minimized.

# I use SCIP MIP solver (http://scip.zib.de) to find the solution

from collections import namedtuple
import math

Point = namedtuple("Point", ['x', 'y'])
Facility = namedtuple("Facility", ['index', 'setup_cost', 'capacity', 'location'])
Customer = namedtuple("Customer", ['index', 'demand', 'location'])

def length(point1, point2):
    return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

import re

def get_sol(optdata,c_count):
    lines = optdata.split('\n')
    line = lines[1]
    parts = line.split()
    obj = parts[2]
    sol_data = []
    for i in range(2, len(lines)):
        line = lines[i]
        parts = line.split()
        #print i, parts
        if parts != []:
            if parts[0][0] == 'x':
                part = re.split('[x_]', parts[0]) # edges[0] = ''
                sol_data.append(part[2])

    return obj, sol_data

import os
from subprocess import Popen, PIPE

import numpy

def read_facility(facility_data):
    # Parse the facility data :
    # N
    # s_0 C_0 x_0 y_0
    # s_1 C_1 x_1 y_1
    # ...
    # s_N-1 C_N-1 x_N-1 y_N-1
    
    lines = facility_data.split('\n')

    facility_count = int(lines[0])
    
    facilities = []
    for i in range(1, facility_count+1):
        parts = lines[i].split()
        assert len(parts) == 4
        facilities.append(Facility(i-1, float(parts[0]), int(parts[1]), Point(float(parts[2]), float(parts[3])) ))
    return facility_count, facilities

def read_customer(customer_data):
    # Parse the customer data:
    # M
    # D_N x_N y_N
    # D_N+1 x_N+1 y_N+1
    # ...
    # D_N+M-1 x_N+M-1 y_N+M-1
    
    lines = customer_data.split('\n')

    customer_count = int(lines[0])
    
    customers = []
    for i in range(1, customer_count+1):
        parts = lines[i].split()
        assert len(parts) == 3
        customers.append(Customer(i-1, int(parts[0]), Point(float(parts[1]), float(parts[2]))))
    return customer_count, customers        

def solve_it(facility_data, customer_data):
    # Read data
    facility_count, facilities = read_facility(facility_data)
    customer_count, customers = read_customer(customer_data)

    # Limit customers to nearest facilities
    n_near = 20 
    nearest_f = []
    nearest_all = set([])
    for customer in customers:
        i = customer.index
        price = []
        for facility in facilities:
            j = facility.index
            dis = length(customer.location, facility.location)
            price.append(dis+facility.setup_cost)
        price = numpy.array(price)
        sort_index = numpy.argsort(price)
        nearest_f.append(list(sort_index[:n_near]))
        nearest_all = nearest_all | set(sort_index[:n_near])
    nearest_all = list(nearest_all)

    # Construct pip file for SCIP:
    
    # Write objective function
    pipdata = 'Minimize' + '\n' + '  obj: '
    
    for customer in customers:
        i = customer.index
        for j in nearest_f[i]:
            #j = facility.index
            dis = length(customer.location, facilities[j].location)
            pipdata += str(dis) + ' x' + str(i) + '_' + str(j) + ' + \n' 
    
    for j in nearest_all[:len(nearest_all)-1]:
        #j = facility.index
        pipdata += str(facilities[j].setup_cost) + ' f' + str(j) + ' + \n'
    
    pipdata += str(facilities[nearest_all[-1]].setup_cost) + ' f' + str(nearest_all[-1]) + '\n'  

    pipdata += 'Subject to\n'
    
    nobj = 0 # number of constraints
    
    # Write constraint
    for customer in customers:
        i = customer.index
        pipdata += '  c' + str(i) + ': ' 

        for j in nearest_f[i][:len(nearest_f[i])-1]:
            #j = facility.index
            pipdata += 'x' + str(i) + '_' + str(j) + ' + '

        pipdata += 'x' + str(i) + '_' + str(nearest_f[i][-1]) + ' == 1\n'
        nobj += 1
    
    for customer in customers:
        i = customer.index

        for j in nearest_f[i]:
            #j = facility.index
            pipdata += '  c' + str(nobj) + ': '
            pipdata += 'x' + str(i) + '_' + str(j) + ' - ' + 'f' + str(j) + ' <= 0\n'
            nobj += 1

    # Capacity constraint
    is_first = 0
    for j in nearest_all:
        #j = facility.index
        pipdata += '  c' + str(nobj) + ': '
        for customer in customers[:customer_count-1]:
            i = customer.index
            if j in nearest_f[i]:
                if is_first == 0:
                    pipdata += str(customer.demand) + ' x' + str(i) + '_' + str(j)
                    is_first = 1
                else:
                    pipdata += ' + ' + str(customer.demand) + ' x' + str(i) + '_' + str(j)
        customer = customers[customer_count-1]
        if j in nearest_f[customer.index]:
            pipdata += ' + ' + str(customer.demand) + ' x' + str(customer.index) + '_' + str(j)
        pipdata += ' <= ' + str(facilities[j].capacity) + '\n'
        nobj += 1
        
    # Write bounds
    pipdata += 'Bounds\n\n'
    
    # Write variable type
    pipdata += 'Binary\n'
    for customer in customers:
        i = customer.index
        for j in nearest_f[i]:
            #j = facility.index
            pipdata += ' x' + str(i) + '_' + str(j) + '\n'
    
    for j in nearest_all:    
        pipdata += ' f' + str(j) + '\n'
    pipdata += 'End'
    
    tmp_file_name = 'tmp.pip'
    tmp_file = open(tmp_file_name, 'w')
    tmp_file.write(pipdata)
    tmp_file.close()
    
    # Run command for SCIP MIP solver
    process = Popen(['./scip-3.1.0.darwin.x86_64.gnu.opt.spx','-b', 'run.batch'])   #, stdout=PIPE)
    (stdout, stderr) = process.communicate()

    scip_out_file = open('tmp.sol', 'r')
    tmpout = ''.join(scip_out_file.readlines())
    scip_out_file.close()

    # Get solution
    obj, solution = get_sol(tmpout,customer_count)
    
    served = []
    for i in range(facility_count):
        served.append([])
        
    for i in range(len(solution)):
        served[int(solution[i])].append(i)
    
    # Print results
    print 'Given', customer_count, 'customers to be served by', facility_count, 'facilities,'
    print 'to minimize cost, customers served by facilities are '
    for i in range(len(served)):
        if len(served[i]) > 0:
            print 'Facility', i, ':', ' '.join(map(str, served[i]))
    
    print
    print 'Cost:', obj
    
    return

import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        facility_filename = sys.argv[1].strip()
        customer_filename = sys.argv[2].strip()
        facility_data_file = open(facility_filename, 'r')
        customer_data_file = open(customer_filename, 'r')
        facility_data = ''.join(facility_data_file.readlines())
        customer_data = ''.join(customer_data_file.readlines())
        facility_data_file.close()
        customer_data_file.close()
        print 'Solving...'
        solve_it(facility_data, customer_data)
    else:
        print 'This test requires two input files. (For example: python solver.py fac_data.txt cus_data.txt)'

