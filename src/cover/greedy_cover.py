import numpy
import heapq

from rule_definition.window import Window
from rule_definition.rule_window import RuleWindow
from rule_definition.rule_model import RuleModel
from rule_definition.rule import Rule
from sequential_data.sequential_data import SequentialData
from utils.util_methods import *
import utils.constants as constants

class GreedyCover():

    def __init__(self, seq_data : SequentialData, rule_model : RuleModel):
        # self.candidate_rwins_heapq = []  # Note - heapq changed to sorted list with binary search for insertions 
                                           #        because comparison seems to be taking way more time than shifts!!
        self.candidate_rwins_sortedq = []
        self.selected_rwins = []
        self.covered_rwins_per_index_y = numpy.zeros((seq_data.get_num_sequences(),seq_data.get_max_sequence_size()))
        self.count_covered_indices = 0
        self.seq_data = seq_data
        self.rule_model = rule_model
    

    def load_candidate_rwins_priorityq(self):
        for rule in self.rule_model.rules_list:
            for rwin_tuple in rule.candidate_rwin_tuples:
                # self.candidate_rwins_heapq.append(RuleWindow(rule, rwin_tuple[0], rwin_tuple[1], rwin_tuple[2]))
                self.candidate_rwins_sortedq.append(RuleWindow(rule, rwin_tuple[0], rwin_tuple[1], rwin_tuple[2]))
        # heapq.heapify(self.candidate_rwins_heapq) 
        # sort with python's inbuilt sort
        self.candidate_rwins_sortedq.sort(reverse=True)  # so that popping from last index possible!

        # sort with numpy
        # argsort = numpy.lexsort(numpy.fliplr(numpy.array(list(map(lambda x: x.priority,  self.candidate_rwins_sortedq)))).T)
        # self.candidate_rwins_sortedq = numpy.array(self.candidate_rwins_sortedq)[argsort].tolist()


    # below will not change the support or confidence, as they're only alterative rwins! 
    # therefore, not adding to the respective rule data structures, only relevant to the cover!
    def find_next_best_candidate_rwin(self, rwin : RuleWindow) -> RuleWindow:
        if rwin.rule.is_empty_head():
            if constants.trigger_xwin_option == constants.TRIGGER_XWIN_MINIMAL:
                return self.find_next_best_candidate_rwin_empty_head_minimal(rwin)
            else:
                return self.find_next_best_candidate_rwin_empty_head_shortest(rwin)
        else:
            if constants.trigger_xwin_option == constants.TRIGGER_XWIN_MINIMAL:
                return self.find_next_best_candidate_rwin_non_empty_head_minimal(rwin)
            else:
                return self.find_next_best_candidate_rwin_non_empty_head_shortest(rwin)
    

    def find_next_best_candidate_rwin_non_empty_head_shortest(self, rwin : RuleWindow) -> RuleWindow:
        sequence = self.seq_data.get_sequence(rwin.y_window.get_seq_index())
        forward_index = rwin.x_window.get_end_index() + 1
        max_tail_len = (constants.rule_tail_gap_ratio_max + 1) * rwin.rule.get_y_pattern_size()
        indices = []
        next_y_index = 0
        while forward_index <= (rwin.x_window.get_end_index() + max_tail_len):
            if forward_index >= self.seq_data.get_sequence_size(rwin.y_window.get_seq_index()):
                # sequence end reached
                break
            if next_y_index == rwin.rule.get_y_pattern_size():
                # potential window end
                break
            if self.covered_rwins_per_index_y[rwin.y_window.get_seq_index()][forward_index] == 0 and sequence[forward_index] == rwin.rule.y_pattern[next_y_index]:
                next_y_index += 1  
                indices.append(forward_index)
            forward_index += 1
        if not next_y_index < rwin.rule.get_y_pattern_size():
            return RuleWindow(rwin.rule, rwin.x_window, Window(indices, rwin.y_window.get_seq_index()))
        else:
            return None
        

    def find_next_best_candidate_rwin_non_empty_head_minimal(self, rwin : RuleWindow) -> RuleWindow:
        sequence = self.seq_data.get_sequence(rwin.y_window.get_seq_index())
        seq_len = self.seq_data.get_sequence_size(rwin.y_window.get_seq_index())
        forward_index = rwin.x_window.get_end_index() + 1
        max_tail_len = (constants.rule_tail_gap_ratio_max + 1) * rwin.rule.get_y_pattern_size()
        next_y_index = 0
        while forward_index <= (rwin.x_window.get_end_index() + max_tail_len):
            if forward_index >= seq_len:
                # sequence end reached
                break
            if next_y_index == rwin.rule.get_y_pattern_size():
                # potential window end
                break
            if self.covered_rwins_per_index_y[rwin.y_window.get_seq_index()][forward_index] == 0 and sequence[forward_index] == rwin.rule.y_pattern[next_y_index]:
                next_y_index += 1  
            forward_index += 1
        if not next_y_index < rwin.rule.get_y_pattern_size():
            # find minimal!
            end_index = forward_index - 1  # previous forward_index
            # TO-DO: think through this properly!!!
            if forward_index < seq_len and sequence[forward_index] == rwin.rule.y_pattern[next_y_index - 1] and self.covered_rwins_per_index_y[rwin.y_window.get_seq_index()][forward_index] == 0:  # and (not sequence[forward_index - 1] == sequence[forward_index] or y_pattern[end] == y_pattern[end-1]):
                end_index = forward_index  # case when end_index coincides with the max_win_len!!
            indices = []
            indices.append(end_index)
            prev_y_index = rwin.rule.get_y_pattern_size() - 2
            backward_index = end_index - 1
            for backward_index in range(end_index - 1, rwin.x_window.get_end_index(), -1):
                if prev_y_index < 0:
                    # minimal window start found
                    break
                if self.covered_rwins_per_index_y[rwin.y_window.get_seq_index()][backward_index] == 0 and sequence[backward_index] == rwin.rule.y_pattern[prev_y_index]:
                    prev_y_index += -1
                    indices.insert(0, backward_index)
            return RuleWindow(rwin.rule, rwin.x_window, Window(indices, rwin.y_window.get_seq_index()))
        else:
            return None
    

    def find_next_best_candidate_rwin_empty_head_shortest(self, rwin : RuleWindow) -> RuleWindow:
        # must not proceed if a singleton or if first occurence itself is a conflict (becasue other shortest windows are already in the heap!)
        # must not find duplicates, i.e, first event occurence should be at same position as in given rwin as long as candidate windows are found using shortest principle!
        if rwin.rule.is_tail_singleton() or self.covered_rwins_per_index_y[rwin.y_window.get_seq_index()][rwin.y_window.get_start_index()] == 1:
            return None

        sequence = self.seq_data.get_sequence(rwin.y_window.get_seq_index())
        max_win_len = (constants.xy_win_gap_ratio_max + 1) * rwin.rule.get_y_pattern_size()
        indices = []
        next_y_index = 0
        forward_index = rwin.y_window.get_start_index()
        while forward_index <= (rwin.y_window.get_start_index() + max_win_len):
            if forward_index >= self.seq_data.get_sequence_size(rwin.y_window.get_seq_index()):
                # sequence end reached
                break
            if next_y_index == rwin.rule.get_y_pattern_size():
                # potential window end
                break
            if self.covered_rwins_per_index_y[rwin.y_window.get_seq_index()][forward_index] == 0 and sequence[forward_index] == rwin.rule.y_pattern[next_y_index]:
                next_y_index += 1  
                indices.append(forward_index)
            forward_index += 1
        if not next_y_index < rwin.rule.get_y_pattern_size():
            return RuleWindow(rwin.rule, rwin.x_window, Window(indices, rwin.y_window.get_seq_index()))
        else:
            return None
        

    def find_next_best_candidate_rwin_empty_head_minimal(self, rwin : RuleWindow) -> RuleWindow:
        # must not proceed if a singleton (becasue other minimal windows are already in the heap!)
        if rwin.rule.is_tail_singleton():
            return None
            
        sequence = self.seq_data.get_sequence(rwin.y_window.get_seq_index())
        seq_len = self.seq_data.get_sequence_size(rwin.y_window.get_seq_index())
        max_win_len = (constants.xy_win_gap_ratio_max + 1) * rwin.rule.get_y_pattern_size()
        remaining_win_len = max_win_len - rwin.y_window.get_win_len()
        range_start = rwin.y_window.get_start_index() - int(remaining_win_len / 2)
        range_end = rwin.y_window.get_end_index() + int(remaining_win_len / 2)
        next_y_index = 0
        forward_index = range_start
        while forward_index <= range_end:
            if forward_index >= seq_len:
                # sequence end reached
                break
            if next_y_index == rwin.rule.get_y_pattern_size():
                # potential window end
                break
            if self.covered_rwins_per_index_y[rwin.y_window.get_seq_index()][forward_index] == 0 and sequence[forward_index] == rwin.rule.y_pattern[next_y_index]:
                next_y_index += 1  
            forward_index += 1
        if not next_y_index < rwin.rule.get_y_pattern_size():
            # find minimal!
            end_index = forward_index - 1  # previous forward_index
            # TO-DO: think through this properly!!!
            if forward_index < seq_len and sequence[forward_index] == rwin.rule.y_pattern[next_y_index - 1] and self.covered_rwins_per_index_y[rwin.y_window.get_seq_index()][forward_index] == 0:  # and (not sequence[forward_index - 1] == sequence[forward_index] or y_pattern[end] == y_pattern[end-1]):
                end_index = forward_index  # case when end_index coincides with the max_win_len!!
            indices = []
            indices.append(end_index)
            prev_y_index = rwin.rule.get_y_pattern_size() - 2
            backward_index = end_index - 1
            for backward_index in range(end_index - 1, range_start - 1, -1):
                if prev_y_index < 0:
                    # minimal window start found
                    break
                if self.covered_rwins_per_index_y[rwin.y_window.get_seq_index()][backward_index] == 0 and sequence[backward_index] == rwin.rule.y_pattern[prev_y_index]:
                    prev_y_index += -1
                    indices.insert(0, backward_index)
            return RuleWindow(rwin.rule, rwin.x_window, Window(indices, rwin.y_window.get_seq_index()))
        else:
            return None


    def is_rwin_conflicting(self, rwin : RuleWindow):
        if self.is_rwin_y_conflicting(rwin) or self.is_rwin_x_conflicting(rwin):
            return True
        return False
    
    def is_rwin_y_conflicting(self, rwin : RuleWindow):
        for index in rwin.y_window.indices:
            if not self.covered_rwins_per_index_y[rwin.y_window.get_seq_index()][index] == 0:  # -1 for not covered and 1 for rule? OR lsit of rules? in that case, None or pointer to rule..
                return True
        return False
    
    # looks like this is slower than list comprehension!!! check rough_work.ipynb
    # def is_rwin_y_conflicting(self, rwin : RuleWindow):
    #     return not numpy.all(self.covered_rwins_per_index_y[rwin.y_window.get_seq_index()][rwin.y_window.indices] == 0)
    
    def is_rwin_x_conflicting(self, rwin : RuleWindow):
        return False


    def is_all_data_covered(self):
        return self.count_covered_indices == self.seq_data.get_all_sequences_size()


    def cover(self):
        self.load_candidate_rwins_priorityq()
        # if len(self.candidate_rwins_heapq) <= 0:
        if len(self.candidate_rwins_sortedq) <= 0:
            print("error: cover_candidate_rwins_heapq or candidate_rwins_sortedq is empty!!")
        # while (not self.is_all_data_covered()) and len(self.candidate_rwins_heapq) > 0:
        while (not self.is_all_data_covered()) and len(self.candidate_rwins_sortedq) > 0:
            # rwin = heapq.heappop(self.candidate_rwins_heapq)
            rwin = self.candidate_rwins_sortedq.pop()
            if not self.is_rwin_conflicting(rwin):
                # add to cover
                self.selected_rwins.append(rwin)
                for index in rwin.y_window.indices:
                    self.covered_rwins_per_index_y[rwin.y_window.get_seq_index()][index] = 1 # 0 for not covered and 1 for rule? OR lsit of rules? in that case, None or pointer to rule..
                    self.count_covered_indices += 1
                # for index in rwin.x_window.indices:
                #     self.covered_rwins_x_per_index[index].append(rwin)
            else:
                # find next best and add to pq
                next_rwin : RuleWindow = self.find_next_best_candidate_rwin(rwin)
                if not next_rwin is None:
                    if not len(next_rwin.y_window.indices) == next_rwin.rule.get_y_pattern_size():
                        print("error: next_best rwin's ywin indices len does not match rule tail pattern size")
                    # heapq.heappush(self.candidate_rwins_heapq, next_rwin)
                    find_position_and_insert_in_list(self.candidate_rwins_sortedq, next_rwin, desc=True)


