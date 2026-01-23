import numpy
import scipy
import math

from rule_definition.window import Window
from sequential_data.sequential_data import SequentialData
import utils.constants as constants

class Rule():

    # # trigger_x_windows can be based on either minimal windows or shortest windows from each starting position
    # TRIGGER_XWIN_MINIMAL = 1
    # TRIGGER_XWIN_SHORTEST = 0
    # trigger_xwin_option = TRIGGER_XWIN_MINIMAL

    def __init__(self, x, y):
        if x == None or x == -1 or x[0] == -1:
            self.x_pattern = [-1]
        else:
            self.x_pattern = x
        self.y_pattern = y

        # below structures applicable only per given sequence, 
        # TO-DO: think of a structure that encapsulates all of these along with the given sequence 
        # TO-DO: __hash__ (tp use as keys) and __eq__ (to ==) rewritten to be based on x_pattern and y_pattern but below structures not included!!
        self.trigger_xwins = []
        self.candidate_rwin_tuples = []  # TO-DO: rethink use of tuples!
        self.support : int = 0  # TO-DO: handle mismatch between support value and len of rwin_tuples in cases of double counts, then remove explicit variable for support 
                                # maybe needed anyway because keeping the extra rwin does no harm, if in case it is better to cover with...
        self.confidence : float = 0
        # TO-DO: should this be an ordered dict?!?!?!
        self.neighborhood_dict = {}  # should be tied to candidate_rwin_tuples
        self.gaps_dict = {}  # is this an overkill?

    def __hash__(self):
        return hash((tuple(self.x_pattern), tuple(self.y_pattern)))

    def __eq__(self, other):
        return (self.x_pattern, self.y_pattern) == (other.x_pattern, other.y_pattern)
    
    def __ne__(self, other):
        return not self == other
    
    def __str__(self):
        return str(self.x_pattern) +  "  -->  " +  str(self.y_pattern)
    
    def is_empty_head(self) -> bool:
        return self.x_pattern[0] == -1
    
    def is_tail_singleton(self) -> bool:
        return len(self.y_pattern) == 1
    
    def is_standard(self) -> bool:
        return self.is_empty_head() and self.is_tail_singleton()
    
    def get_x_pattern_size(self) -> int:
        if self.is_empty_head():
            return 0
        else:
            return len(self.x_pattern)
        
    def get_y_pattern_size(self) -> int:
        return len(self.y_pattern)
    
    def get_trigger_count(self) -> int:
        if self.is_empty_head():
            return 0
        else:
            return len(self.trigger_xwins)
        
    def get_rule_support(self) -> int:
        return self.support
        # return len(self.candidate_rwin_tuples)  # TO-DO: fix the mismatch betwen support and count of rwins!!
    
    def get_rule_confidence(self) -> float:
        return self.confidence


    def add_trigger_xwin(self, xwin : Window):
        if not len(xwin.indices) == self.get_x_pattern_size():
            print("error: trigger xwin indices len does not match rule head size")
        self.trigger_xwins.append(xwin)


    def add_candidate_rwin_tuple(self, rwin_tuple):
        if not rwin_tuple[0] is None and not rwin_tuple[0] in self.trigger_xwins:
            print("error: xwin of rwin_tuple not found in trigger_xwins list")
        if not len(rwin_tuple[1].indices) == self.get_y_pattern_size():
            print("error: ywin indices len does not match rule tail pattern size")
        self.candidate_rwin_tuples.append(rwin_tuple)


    def increment_rule_support(self):
        self.support += 1
    
    def set_rule_support(self, s):
        self.support = s


    def update_rule_confidence(self, sequence_size = None):
        # TO-DO: requires trigger_count and support to be already set!! verify!!
        if not self.is_empty_head():
            if self.get_trigger_count() > 0:
                self.confidence = self.support / self.get_trigger_count()
            else:
                print("error: divide by zero attempt - trigger_count is ", self.get_trigger_count(), " for rule head: ", self.x_pattern, " with size ", self.get_x_pattern_size())
        else:
            if not sequence_size is None:
                # TO-DO: what is a sensible confidence for non-empty head rules?
                self.confidence = self.support / (sequence_size / self.get_y_pattern_size())
            else:
                print("error: sequence_size missing to update confidence of empty-head rules")

    
    def find_trigger_xwins_in_sequences(self, seq_data : SequentialData):
        if self.is_empty_head():
            print("error: attempt to find xwin for empty head rule - return")
            return
        self.trigger_xwins.clear()  # TO-DO: also clear candidate_rwins then??
        if constants.trigger_xwin_option == constants.TRIGGER_XWIN_MINIMAL:
            for seq_index in range(0, seq_data.get_num_sequences()):
                self.find_trigger_xwins_minimal(seq_data.get_sequence(seq_index=seq_index), seq_index=seq_index)
        elif constants.trigger_xwin_option == constants.TRIGGER_XWIN_SHORTEST:
            for seq_index in range(0, seq_data.get_num_sequences()):
                self.find_trigger_xwins_shortest(seq_data.get_sequence(seq_index=seq_index), seq_index=seq_index)
        else:
            raise ValueError("error: invalid trigger window type")
    

    # TO-DO: remove this later!!
    #        keeping it for now only because generation algorithms require it (generator generates single sequence!)
    def find_trigger_xwins_in_seq(self, seq, relevant_start = 0, relevant_end = None, seq_index = 0):
        if relevant_start < 0 or (not relevant_end is None and relevant_end > len(seq)):
            print("error: relevant start or end for sequence out of bounds in find_trigger_xwins")
        relevant_seq = seq[relevant_start:relevant_end]

        if self.is_empty_head():
            print("error: attempt to find xwin for empty head rule - return")
            return
        self.trigger_xwins.clear()  # TO-DO: also clear candidate_rwins then??
        if constants.trigger_xwin_option == constants.TRIGGER_XWIN_MINIMAL:
            self.find_trigger_xwins_minimal(relevant_seq, offset=relevant_start, seq_index=seq_index)
        elif constants.trigger_xwin_option == constants.TRIGGER_XWIN_SHORTEST:
            self.find_trigger_xwins_shortest(relevant_seq, offset=relevant_start, seq_index=seq_index)
        else:
            raise ValueError("error: invalid trigger window type")
    
    
    def find_trigger_xwins_minimal(self, seq, offset = 0, seq_index = 0): #seq_data : SequentialData
        sequence = seq #seq_data.get_sequence()
        seq_len = len(seq) #seq_data.get_sequence_size()
        max_win_len = (constants.xy_win_gap_ratio_max + 1) * self.get_x_pattern_size()
        start_index = 0
        end_index = -1
        while start_index <= (seq_len - self.get_x_pattern_size()):
            if sequence[start_index] == self.x_pattern[0]:
                # potential window start
                next_x_index = 1
                for forward_index in range(start_index + 1, start_index + max_win_len + 1): #+1 extra to handle case where range and end_index coincides
                    if forward_index >= seq_len:
                        # sequence end reached
                        break
                    if next_x_index == self.get_x_pattern_size():
                        # potential window end
                        break
                    if sequence[forward_index] == self.x_pattern[next_x_index]:
                        next_x_index += 1  
                if next_x_index < self.get_x_pattern_size():
                    start_index += 1
                    # TO-DO: keep track of next index matching self.x_pattern[0] in previous loop and jump to that index
                    #        if none found, jump to forward_index
                else:
                    end_index = forward_index - 1  # previous forward_index
                    # TO-DO: think through this properly!!!
                    if forward_index < seq_len and sequence[forward_index] == self.x_pattern[next_x_index - 1]:  # and (not sequence[forward_index - 1] == sequence[forward_index] or x_pattern[end] == x_pattern[end-1]):
                        end_index = forward_index  # case when end_index coincides with the max_win_len!!
                    indices = []
                    indices.append(end_index + offset)
                    prev_x_index = self.get_x_pattern_size() - 2
                    backward_index = end_index - 1
                    for backward_index in range(end_index - 1, start_index - 2, -1): #-1 extra to handle case where range and start_index coincides
                        if prev_x_index < 0:
                            # minimal window start found
                            break
                        if sequence[backward_index] == self.x_pattern[prev_x_index]:
                            prev_x_index += -1
                            indices.insert(0, backward_index + offset)
                    start_index = backward_index + 1 # previous backward_index
                    self.add_trigger_xwin(Window(indices, seq_index))
                    start_index += 1
                    # TO-DO: keep track of next index matching self.x_pattern[0] in previous loop and jump to that index
                    #        if none found, jump to forward_index
            else:
                start_index += 1               


    def find_trigger_xwins_shortest(self, seq, offset = 0, seq_index = 0): #seq_data : SequentialData
        sequence = seq #seq_data.get_sequence()
        seq_len = len(seq) #seq_data.get_sequence_size()
        max_win_len = (constants.xy_win_gap_ratio_max + 1) * self.get_x_pattern_size()
        start_index = 0
        while start_index <= (seq_len - self.get_x_pattern_size()):
            if sequence[start_index] == self.x_pattern[0]:
                # potential window start
                indices = []
                indices.append(start_index + offset)
                next_x_index = 1
                for forward_index in range(start_index + 1, start_index + max_win_len + 1):
                    if forward_index >= seq_len:
                        # sequence end reached
                        break
                    if next_x_index == self.get_x_pattern_size():
                        # potential window end
                        break
                    if sequence[forward_index] == self.x_pattern[next_x_index]:
                        next_x_index += 1  
                        indices.append(forward_index + offset)
                if next_x_index < self.get_x_pattern_size():
                    start_index += 1
                    # TO-DO: keep track of next index matching self.x_pattern[0] in previous loop and jump to that index
                    #        if none found, jump to forward_index
                else:
                    self.add_trigger_xwin(Window(indices, seq_index))
                    start_index += 1
                    # TO-DO: keep track of next index matching self.x_pattern[0] in previous loop and jump to that index
                    #        if none found, jump to forward_index
            else:
                start_index += 1


    def copy_trigger_xwins(self, rule):
        # needed if x_windows already found for another rule using same x_pattern
        # .copy() creates a shallow copy, therefore clearing of original trigger_xwins list will have no impact
        self.trigger_xwins = rule.trigger_xwins.copy()


    def find_candidate_rwin_tuples_in_sequences(self, seq_data : SequentialData):
        self.set_rule_support(0)  
        self.candidate_rwin_tuples.clear()
        self.neighborhood_dict.clear()
        self.gaps_dict.clear()
        if self.is_empty_head():
            if constants.trigger_xwin_option == constants.TRIGGER_XWIN_MINIMAL:
                self.find_candidate_rwins_empty_head_minimal(seq_data)
            else:
                self.find_candidate_rwins_empty_head_shortest(seq_data)
        else:
            if constants.trigger_xwin_option == constants.TRIGGER_XWIN_MINIMAL:
                self.find_candidate_rwins_non_empty_head_minimal(seq_data)
            else:
                self.find_candidate_rwins_non_empty_head_shortest(seq_data)
        self.set_candidate_rwin_tuples_priority()
        neigh_pvalues = {key:self.get_neighborhood_p_value(key, seq_data) for key, value in self.neighborhood_dict.items()}
        self.neighborhood_dict = {key:value for key, value in self.neighborhood_dict.items() if neigh_pvalues[key] <= 0.01}
        self.neighborhood_dict = dict(sorted(self.neighborhood_dict.items(), key=lambda item: neigh_pvalues[item[0]]))
    

    def set_candidate_rwin_tuples_priority(self):
        for index in range(0, len(self.candidate_rwin_tuples)):
            rwin_tuple = self.candidate_rwin_tuples[index]
            # tail = delay + ywin
            if not self.is_empty_head():
                tail_len = rwin_tuple[1].get_end_index() - rwin_tuple[0].get_end_index()
            else:
                tail_len = rwin_tuple[1].get_win_len()
            if constants.candidate_order == constants.YSIZE_SUPP_CONF_WSIZE:
                priority = (self.get_y_pattern_size(), self.support, self.confidence, -tail_len, -rwin_tuple[1].get_start_index(), -rwin_tuple[1].get_seq_index())
            elif constants.candidate_order == constants.YSIZE_CONF_SUPP_WSIZE:
                priority = (self.get_y_pattern_size(), self.confidence, self.support, -tail_len, -rwin_tuple[1].get_start_index(), -rwin_tuple[1].get_seq_index())
            elif constants.candidate_order == constants.CONF_SUPP_YSIZE_WSIZE:
                priority = (self.confidence, self.support, self.get_y_pattern_size(), -tail_len, -rwin_tuple[1].get_start_index(), -rwin_tuple[1].get_seq_index())
            else:
                raise ValueError("error: invalid candidate order!")
            # TO-DO: try a combined score like in HOPPER!! 
            self.candidate_rwin_tuples[index] = (rwin_tuple[0], rwin_tuple[1], priority)

    
    def find_candidate_rwins_empty_head_shortest(self, seq_data : SequentialData):
        # basically, shortest windows from each starting position
        # TO-DO: think if minimal windows makes more sense?
        #        factor 1 - double counting in support
        #        factor 2 - comparable support calculation between empty head and non-empty head rules
        for seq_index in range(0, seq_data.get_num_sequences()):
            sequence = seq_data.get_sequence(seq_index=seq_index)
            counted = numpy.zeros(seq_data.get_sequence_size(seq_index), dtype=int)
            max_win_len = (constants.xy_win_gap_ratio_max + 1) * self.get_y_pattern_size()
            start_index = 0
            while start_index <= (seq_data.get_sequence_size(seq_index) - self.get_y_pattern_size()):
                if sequence[start_index] == self.y_pattern[0]:
                    # potential window start
                    next_y_index = 1
                    indices = []
                    indices.append(start_index)
                    for forward_index in range(start_index + 1, start_index + max_win_len + 1):
                        if forward_index >= seq_data.get_sequence_size(seq_index):
                            # sequence end reached
                            break
                        if next_y_index == self.get_y_pattern_size():
                            # potential window end
                            break
                        if sequence[forward_index] == self.y_pattern[next_y_index]:
                            next_y_index += 1  
                            indices.append(forward_index)
                    if next_y_index < self.get_y_pattern_size():
                        start_index += 1
                        # TO-DO: keep track of next index matching self.x_pattern[0] in previous loop and jump to that index
                        #        if none found, jump to forward_index
                    else:
                        found_rwin_tuple = (None, Window(indices, seq_index))
                        self.add_candidate_rwin_tuple(found_rwin_tuple)
                        self.update_neighborhood_dict(found_rwin_tuple, seq_data)
                        double_count = True # TO-DO: handling double counting here!!!  
                        for index in indices:
                            if counted[index] == 0:
                                double_count = False
                                counted[index] = 1
                        if not double_count:
                            self.increment_rule_support()
                        start_index += 1
                        # TO-DO: keep track of next index matching self.x_pattern[0] in previous loop and jump to that index
                        #        if none found, jump to forward_index
                else:
                    start_index += 1
        self.update_rule_confidence(seq_data.get_all_sequences_size())


    def find_candidate_rwins_empty_head_minimal(self, seq_data : SequentialData):
        # basically, same as minimal triggers?
        for seq_index in range(0, seq_data.get_num_sequences()):
            sequence = seq_data.get_sequence(seq_index=seq_index)
            seq_len = seq_data.get_sequence_size(seq_index)
            counted = numpy.zeros(seq_len, dtype=int)
            max_win_len = (constants.xy_win_gap_ratio_max + 1) * self.get_y_pattern_size()
            start_index = 0
            while start_index <= (seq_len - self.get_y_pattern_size()):
                if sequence[start_index] == self.y_pattern[0]:
                    # potential window start
                    next_y_index = 1
                    for forward_index in range(start_index + 1, start_index + max_win_len + 1):
                        if forward_index >= seq_len:
                            # sequence end reached
                            break
                        if next_y_index == self.get_y_pattern_size():
                            # potential window end
                            break
                        if sequence[forward_index] == self.y_pattern[next_y_index]:
                            next_y_index += 1  
                    if next_y_index < self.get_y_pattern_size():
                        start_index += 1
                        # TO-DO: keep track of next index matching self.x_pattern[0] in previous loop and jump to that index
                        #        if none found, jump to forward_index
                    else:
                        # find minimal!!!
                        end_index = forward_index - 1  # previous forward_index
                        # TO-DO: think through this properly!!!
                        if forward_index < seq_len and sequence[forward_index] == self.y_pattern[next_y_index - 1]:  # and (not sequence[forward_index - 1] == sequence[forward_index] or y_pattern[end] == y_pattern[end-1]):
                            end_index = forward_index  # case when end_index coincides with the max_win_len!!
                        indices = []
                        indices.append(end_index)
                        prev_y_index = self.get_y_pattern_size() - 2
                        backward_index = end_index - 1
                        for backward_index in range(end_index - 1, start_index - 2, -1): #-1 extra to handle case where range and start_index coincides
                            if prev_y_index < 0:
                                # minimal window start found
                                break
                            if sequence[backward_index] == self.y_pattern[prev_y_index]:
                                prev_y_index += -1
                                indices.insert(0, backward_index)
                        start_index = backward_index + 1 # previous backward_index
                        ###################
                        found_rwin_tuple = (None, Window(indices, seq_index))
                        self.add_candidate_rwin_tuple(found_rwin_tuple)
                        self.update_neighborhood_dict(found_rwin_tuple, seq_data)
                        double_count = True # TO-DO: handling double counting - minimal from different starting positions could be the same!
                                            #        but since prev_start_index + 1 considered, probably not an issue and can be removed!!!
                        for index in indices:
                            if counted[index] == 0:
                                double_count = False
                                counted[index] = 1
                        if not double_count:
                            self.increment_rule_support()
                        start_index += 1
                        # TO-DO: keep track of next index matching self.x_pattern[0] in previous loop and jump to that index
                        #        if none found, jump to forward_index
                else:
                    start_index += 1
        self.update_rule_confidence(seq_data.get_all_sequences_size())


    def find_candidate_rwins_non_empty_head_shortest(self, seq_data : SequentialData):
        counted = numpy.zeros((seq_data.get_num_sequences(), seq_data.get_max_sequence_size()), dtype=int) # TO-DO: any issues with extra zeroes??
        for xwin in self.trigger_xwins:
            sequence = seq_data.get_sequence(seq_index=xwin.get_seq_index())
            forward_index = xwin.get_end_index() + 1
            max_tail_len = (constants.rule_tail_gap_ratio_max + 1) * self.get_y_pattern_size()
            indices = []
            next_y_index = 0
            while forward_index <= (xwin.get_end_index() + max_tail_len):
                if forward_index >= seq_data.get_sequence_size(xwin.get_seq_index()):
                    # sequence end reached
                    break
                if next_y_index == self.get_y_pattern_size():
                    # potential window end
                    break
                if sequence[forward_index] == self.y_pattern[next_y_index]:
                    next_y_index += 1  
                    indices.append(forward_index)
                forward_index += 1
            if not next_y_index < self.get_y_pattern_size():
                found_rwin_tuple = (xwin, Window(indices, xwin.get_seq_index()))
                self.add_candidate_rwin_tuple(found_rwin_tuple)
                self.update_neighborhood_dict(found_rwin_tuple, seq_data)
                double_count = True # TO-DO: handling double counting here!!!  
                for index in indices:
                    if counted[xwin.get_seq_index()][index] == 0:
                        double_count = False
                        counted[xwin.get_seq_index()][index] = 1
                if not double_count:
                    self.increment_rule_support()
        self.update_rule_confidence()


    def find_candidate_rwins_non_empty_head_minimal(self, seq_data : SequentialData):
        counted = numpy.zeros((seq_data.get_num_sequences(), seq_data.get_max_sequence_size()), dtype=int) # TO-DO: any issues with extra zeroes??
        for xwin in self.trigger_xwins:
            sequence = seq_data.get_sequence(seq_index=xwin.get_seq_index())
            seq_len = seq_data.get_sequence_size(xwin.get_seq_index())
            forward_index = xwin.get_end_index() + 1
            max_tail_len = (constants.rule_tail_gap_ratio_max + 1) * self.get_y_pattern_size()
            next_y_index = 0
            # allow more delay if gaps lesser than allowance!!!!
            while forward_index <= (xwin.get_end_index() + max_tail_len):
                if forward_index >= seq_len:
                    # sequence end reached
                    break
                if next_y_index == self.get_y_pattern_size():
                    # potential window end
                    break
                if sequence[forward_index] == self.y_pattern[next_y_index]:
                    next_y_index += 1  
                forward_index += 1
            if not next_y_index < self.get_y_pattern_size():
                # find minimal!!!
                end_index = forward_index - 1  # previous forward_index
                # TO-DO: think through this properly!!!
                if forward_index < seq_len and sequence[forward_index] == self.y_pattern[next_y_index - 1]:  # and (not sequence[forward_index - 1] == sequence[forward_index] or y_pattern[end] == y_pattern[end-1]):
                    end_index = forward_index  # case when end_index coincides with the max_win_len!!
                indices = []
                indices.append(end_index)
                prev_y_index = self.get_y_pattern_size() - 2
                backward_index = end_index - 1
                for backward_index in range(end_index - 1, xwin.get_end_index(), -1):
                    if prev_y_index < 0:
                        # minimal window start found
                        break
                    if sequence[backward_index] == self.y_pattern[prev_y_index]:
                        prev_y_index += -1
                        indices.insert(0, backward_index)
                ###################
                found_rwin_tuple = (xwin, Window(indices, xwin.get_seq_index()))
                self.add_candidate_rwin_tuple(found_rwin_tuple)
                self.update_neighborhood_dict(found_rwin_tuple, seq_data)
                double_count = True # TO-DO: handling double counting here!!!  
                                    # needed because another trigger for same rule might pick up same ywin!!
                for index in indices:
                    if counted[xwin.get_seq_index()][index] == 0:
                        double_count = False
                        counted[xwin.get_seq_index()][index] = 1
                if not double_count:
                    self.increment_rule_support()
        self.update_rule_confidence()


    def update_neighborhood_dict(self, found_rwin_tuple, seq_data : SequentialData):  
        # possible positions: -1, 0 ... |X|-1 and -1, 0 ... |Y|-1
        ywin : Window = found_rwin_tuple[1]
        sequence = seq_data.get_sequence(ywin.get_seq_index())
        # TO-DO: use rule_tail_gap_ratio_max here to capture rule heads/tails far away?? or xwin_gap_ratio itself??
        # also y_len + 1 to look for a longer range!
        remaining_max_empty_ywin_len = (constants.rule_tail_gap_ratio_max + 1) * (self.get_y_pattern_size() + 1) - ywin.get_win_len()

        def collect_gap_events(start_index, end_index, insert_position, x_or_y):
            # should this function be outside the update function???? can nested functions access the outer function parameters?
            gap_size = end_index - start_index if end_index > start_index else 0
            # if gap_size > 0:
            size_dict = self.gaps_dict.get((x_or_y, insert_position), {}) or {}
            size_dict[gap_size] = size_dict.get(gap_size, 0) + 1
            self.gaps_dict[(x_or_y, insert_position)] = size_dict  # TO-DO: review the reassignment!!!
            # self.gaps_dict[(x_or_y, insert_position)] = self.gaps_dict.get((x_or_y, insert_position), 0) + 1
            # collected_gap_events = set([])
            # for running_index in range(start_index, end_index):
            #     collected_gap_events.add(sequence[running_index])
            #     # self.neighborhood_dict[('y', insert_position, sequence[running_index])] = self.neighborhood_dict.get(('y', insert_position, sequence[running_index]), 0) + 1
            #     # self.gaps_dict[('y', insert_position)] = self.gaps_dict.get(('y', insert_position), 0) + 1
            # collected_gap_events = numpy.unique(sequence[start_index:end_index])
            collected_gap_events = set(sequence[start_index:end_index])
            for gap_event in collected_gap_events:
                self.neighborhood_dict[(x_or_y, insert_position, gap_event)] = self.neighborhood_dict.get((x_or_y, insert_position, gap_event), 0) + 1
        
        try:
            if not self.is_empty_head():
                xwin : Window = found_rwin_tuple[0]
                remaining_max_xwin_len = (constants.xy_win_gap_ratio_max + 1) * (self.get_x_pattern_size() + 1) - xwin.get_win_len()
                remaining_max_tail_len = (constants.rule_tail_gap_ratio_max + 1) * (self.get_y_pattern_size() + 1) - (ywin.get_end_index() - xwin.get_end_index())

                for position in range(0, self.get_x_pattern_size() + 1):
                    insert_position = position - 1
                    # TO-DO: review boundaries!
                    start_index = xwin.indices[position - 1] + 1 if position > 0 else max(xwin.get_start_index() - remaining_max_xwin_len, 0) 
                    end_index = xwin.indices[position] if position < self.get_x_pattern_size() else min(xwin.get_end_index() + remaining_max_xwin_len, ywin.get_start_index())
                    collect_gap_events(start_index, end_index, insert_position, 'x')

                for position in range(0, self.get_y_pattern_size() + 1):
                    insert_position = position - 1
                    # TO-DO: review boundaries!
                    start_index = ywin.indices[position - 1] + 1 if position > 0 else xwin.get_end_index() + 1
                    end_index = ywin.indices[position] if position < self.get_y_pattern_size() else min(ywin.get_end_index() + remaining_max_tail_len, seq_data.get_sequence_size(ywin.get_seq_index()))
                    collect_gap_events(start_index, end_index, insert_position, 'y')

            else:
                for position in range(0, self.get_y_pattern_size() + 1):
                    insert_position = position - 1
                    # TO-DO: review boundaries!
                    start_index = ywin.indices[position - 1] + 1 if position > 0 else max(ywin.get_start_index() - remaining_max_empty_ywin_len, 0)
                    end_index = ywin.indices[position] if position < self.get_y_pattern_size() else min(ywin.get_end_index() + remaining_max_empty_ywin_len, seq_data.get_sequence_size(ywin.get_seq_index()))
                    collect_gap_events(start_index, end_index, insert_position, 'y')
        except Exception as e:
            print(f'error: invalid or missing position <{position}> in xwin indices <{xwin.indices}> or ywin indices <{ywin.indices}> for rule <{self.x_pattern}> --> <{self.y_pattern}>')


    def get_expected_neighborhood_and_variance(self, key, seq_data : SequentialData):  
        # return self.gaps_dict[(key[0], key[1])] * seq_data.frequency_dict[key[2]]["freq"] / seq_data.get_sequence_size()
        # if appraoach 2 (exact):
        p_e = seq_data.frequency_dict[key[2]]["freq"] / seq_data.get_all_sequences_size()
        p_not_e = 1 - p_e
        size_dict = self.gaps_dict[(key[0], key[1])]
        expected_succeses = 0
        variance = 0
        for size in size_dict:
            expected_succeses += size_dict[size] * (1 - p_not_e**size)
            variance += size_dict[size] * ((1 - p_not_e**size) * (p_not_e**size))
        return expected_succeses, variance
    

    def get_neighborhood_p_value(self, key, seq_data : SequentialData): # key is the neighborhood tuple!
                                                                        # seriously, consider pointing to seq_data inside the rule object!!
        expected_successes, variance = self.get_expected_neighborhood_and_variance(key, seq_data)
        # expected_successes = math.ceil(expected_successes)
        observed_successes = self.neighborhood_dict[key]
        num_trials = len(self.candidate_rwin_tuples)
        if observed_successes > expected_successes:
            ##binomial approx with one-tailed test (because we care about extreme values in only one direction!)
            expected_probability = expected_successes / num_trials
            binom_p = scipy.stats.binomtest(observed_successes, num_trials, p=expected_probability, alternative='greater').pvalue
            return binom_p

            ##normal approx with one-tailed test (because we care about extreme values in only one direction!)
            if num_trials < 10: # try 6, 10, 20, 30
                if observed_successes > expected_successes + 1:
                    norm_p = 0.01
                else:
                    norm_p = 0.1
            else:
                if not observed_successes > expected_successes + 1:
                    norm_p = 0.1
                else:
                    std = math.sqrt(variance)
                    z_score = (observed_successes - 0.5 - expected_successes) / std
                    #if z_score >= 1.96:  # account for multiple hypothesis testing and try 0.025!!
                    if z_score >= 2.326:  # try 2.326 (p-value 0.01)!!
                        norm_p = scipy.stats.norm.sf(z_score)   
                    else:
                        norm_p = 0.1
            return norm_p
        else:
            return 0.5


    def print_rule(self, out_file=None):
        if out_file is None:
            print("rule:  ", self.x_pattern, "  -->  ", self.y_pattern)
        else:
            xp = "["
            yp = "["
            if self.is_empty_head():
                xp = xp + "-1"
            else:
                for event in self.x_pattern:
                    xp = xp + str(event) + ","
            xp = xp + "]"
            for event in self.y_pattern:
                yp = yp + str(event) + ","
            yp = yp + "]"
            out_file.write("\nrule:  " + xp + "  -->  " + yp)