#from numba import jit
import math
import numpy

#@jit(nopython=True)
def compute_cost_preq(count1 : int, count2 : int) -> float:
    preq_epsilon = 0.5  # TO-DO: check what this value should be and why?!
    cost = 0

    i_arr = numpy.arange(count1) + 1
    pre_log_vals = (2 * preq_epsilon + i_arr) / (preq_epsilon + i_arr)
    cost += numpy.log2(pre_log_vals).sum()

    i_arr = numpy.arange(count2) + 1
    pre_log_vals = (2 * preq_epsilon + count1 + i_arr) / (preq_epsilon + i_arr)
    cost += numpy.log2(pre_log_vals).sum()
    return cost

#@jit(nopython=True)
def compute_cost_lU(n : int, k : int) -> float:  # cost of n choose k
    nCk = math.comb(n, k)   
    return math.log(nCk, 2)

#@jit(nopython=True)
def compute_cost_lN(count : int) -> float:
    cost = 0
    while count >= 1:
        count = math.log(count, 2) 
        #count = numpy.log2(count)
        cost += count
    return cost + math.log(2.865064, 2)
    #return cost + numpy.log2(2.865064)