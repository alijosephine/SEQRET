from rule_definition.window import Window
from rule_definition.rule import Rule

import utils.constants as constants

class RuleWindow():

    # YSIZE_SUPP_CONF_WSIZE = 0  # slighlty better for precision? nope!
    # YSIZE_CONF_SUPP_WSIZE = 1  # seems like best option for recall!
    # CONF_SUPP_YSIZE_WSIZE = 2  # found to be worst option
    # YSIZE_WSIZE_CONF_SUPP = 3  # yet to try!
    # candidate_order = YSIZE_SUPP_CONF_WSIZE


    def __init__(self, rule : Rule, xwin : Window, ywin : Window, priority=None):
        self.rule = rule
        self.x_window = xwin
        self.y_window = ywin
        # priority has to be optional as new rwins could be found by the cover!
        if priority is not None:
            self.priority = priority
        else:
            self.set_priority()
        if not xwin is None and not xwin.get_seq_index() == ywin.get_seq_index():
            print("error: seq_index of xwin and ywin different for rule_win!!")


    def set_priority(self):
        if constants.candidate_order == constants.YSIZE_SUPP_CONF_WSIZE:
            self.priority = (self.rule.get_y_pattern_size(), self.rule.support, self.rule.confidence, -self.get_tail_len(), -self.y_window.get_start_index(), -self.y_window.get_seq_index())
        elif constants.candidate_order == constants.YSIZE_CONF_SUPP_WSIZE:
            self.priority = (self.rule.get_y_pattern_size(), self.rule.confidence, self.rule.support, -self.get_tail_len(), -self.y_window.get_start_index(), -self.y_window.get_seq_index())
        elif constants.candidate_order == constants.CONF_SUPP_YSIZE_WSIZE:
            self.priority = (self.rule.confidence, self.rule.support, self.rule.get_y_pattern_size(), -self.get_tail_len(), -self.y_window.get_start_index(), -self.y_window.get_seq_index())
        else:
            raise ValueError("error: invalid candidate order!")
        # TO-DO: try a combined score like in HOPPER!! 

    
    def __lt__ (self, other):      
        # lesser and greater reversed to be used in priority queue as max-heap
        return self.priority > other.priority

    def __eq__(self, other):
        # TO-DO: should both give same results?? do check!!!
        # return self is other
        return not self<other and not other<self
    
    def __ne__(self, other):
        return not self == other
    
    def __gt__(self, other):
        return other<self
    
    def __ge__(self, other):
        return not self<other
    
    def __le__(self, other):
        return not other<self


    def get_delay(self) -> int:
        if not self.rule.is_empty_head():
            return self.y_window.get_start_index() - self.x_window.get_end_index() - 1
        else:
            return 0


    def get_tail_len(self) -> int:
        # tail = delay + ywin
        if not self.rule.is_empty_head():
            return self.y_window.get_end_index() - self.x_window.get_end_index()
        else:
            return self.y_window.get_win_len()

