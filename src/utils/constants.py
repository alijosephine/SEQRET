## this is potentially a bad design, but required because numba cannot work with class variables curently
## potential problem with this design - order of execution and imports might matter, i.e, updates may not reflect globally!!
## alternative approach to consider - singleton approach!


## rwin priority!!
YSIZE_SUPP_CONF_WSIZE = 0  # slighlty better for precision? nope!
YSIZE_CONF_SUPP_WSIZE = 1  # seems like best option for recall!
CONF_SUPP_YSIZE_WSIZE = 2  # found to be worst option
YSIZE_WSIZE_CONF_SUPP = 3  # yet to try!
candidate_order = YSIZE_SUPP_CONF_WSIZE

## rule minimal or shortest!!
TRIGGER_XWIN_MINIMAL = 1
TRIGGER_XWIN_SHORTEST = 0
trigger_xwin_option = TRIGGER_XWIN_MINIMAL

## windows ratios!!
xy_win_gap_ratio_max : int = 2  # x and y windows have same gap ratio?
delay_ratio_max : int = xy_win_gap_ratio_max  # as a ratio of max(x,y) or just y?
rule_tail_gap_ratio_max : int = xy_win_gap_ratio_max + delay_ratio_max  # tail refers to (delay + ywin_gaps) 

## encoding!!
#####################
##  best trigger options: 2 and 7, 
##  2 better for shorter squences as recall high, 
##  7 better for longer sequences as precision high
#####################
TRIGGER_EMPTY_ALWAYS = 0
TRIGGER_EMPTY_LAST = 1
TRIGGER_EMPTY_PATTERN_SECOND_SINGLETON_LAST = 2
TRIGGER_EMPTY_PATTERN_ALWAYS_SINGLETON_LAST = 3
SINGLETON_RESIDUAL_UNIFORM_EMPTY_ALWAYS = 4 
SINGLETON_RESIDUAL_UNIFORM_EMPTY_LAST = 5
SINGLETON_RESIDUAL_OPTIMAL_EMPTY_ALWAYS = 6  # optimal based on usage
SINGLETON_RESIDUAL_OPTIMAL_EMPTY_LAST = 7  # optimal based on usage
PATTERN_RESIDUAL_OPTIMAL = 8  # optimal based on usage
# below option - singletons and patterns grouped together, alphabet size might have an influence...
#                therefore, do not consider. doesn't make sense to use uniform code here anyway!!
PATTERN_RESIDUAL_UNIFORM = 9

trigger_order = TRIGGER_EMPTY_PATTERN_SECOND_SINGLETON_LAST
causal_eqn_flag = False
encode_over_patterns = True