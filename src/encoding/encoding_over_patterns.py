import math

from encoding.encoding_over_events import Encoding
from cover.greedy_cover import GreedyCover
from rule_definition.rule import Rule
from utils.compute import *
import utils.constants as constants

class EncodingCausal(Encoding):

    # causal_eqn_flag = False
    # encode_over_patterns = False

    def __init__(self, cover):
        super().__init__(cover)
        self.all_patterns = []  # all_patterns includes empty, singletons, rule head patterns and rule tail patterns
        self.all_y_patterns_excl_std = []  # all_y_patterns excl. std. 
        #self.all_y_patterns_incl_std = []  # all_y_patterns incl. std.

    def find_all_patterns(self):
        for rule in self.cover.rule_model.rules_list:
            if not rule.x_pattern in self.all_patterns:
                self.all_patterns.append(rule.x_pattern)
            if not rule.y_pattern in self.all_patterns:
                self.all_patterns.append(rule.y_pattern)

    def find_all_y_patterns(self):
        for rule in self.cover.rule_model.rules_list:
            if not rule.is_standard() and not rule.y_pattern in self.all_y_patterns_excl_std:
            #if not rule.y_pattern in self.all_y_patterns_incl_std:
                self.all_y_patterns_excl_std.append(rule.y_pattern)
                #self.all_y_patterns_incl_std.append(rule.y_pattern)

    def get_count_all_patterns(self):
        return len(self.all_patterns)
    
    def get_count_all_y_patterns(self):
        return len(self.all_y_patterns_excl_std)
        # return len(self.all_y_patterns_incl_std)
    
    def compute_encoding(self):
        self.find_all_patterns()  # should be called before any cost computation
        super().compute_encoding()

    def compute_cost_model_enc(self) -> float:
        all_patterns_count = self.get_count_all_patterns()
        non_empty_patterns_count = all_patterns_count - 1
        non_singleton_non_empty_patterns_count = non_empty_patterns_count - self.cover.seq_data.get_alphabet_size()
        per_all_patterns_cost = math.log(all_patterns_count, 2)
        per_non_empty_patterns_cost = math.log(non_empty_patterns_count, 2)
        # note - number of non_empty_non_singleton all_patterns needed (like alphabet size) to describe patterns
        #        (so that rules can be defined over patterns)
        event_cost = math.log(self.cover.seq_data.get_alphabet_size(), 2)  # assuming uniform cost over the alphabet!
        cost = compute_cost_lN(self.cover.seq_data.get_alphabet_size()) + compute_cost_lN(non_singleton_non_empty_patterns_count + 1)
        # describe the constituent patterns
        for pattern in self.all_patterns:
            if len(pattern) > 1: # singletons and empty need not be described!!
                cost += compute_cost_lN(len(pattern))
                cost += len(pattern) * event_cost

        # describe the edges or structural equations
        if not constants.causal_eqn_flag:  # describe edges!!
            cost += compute_cost_lN(self.cover.rule_model.get_size() - self.cover.seq_data.get_alphabet_size() + 1)
            for rule in self.cover.rule_model.rules_list:
                if not rule.is_standard():  # standard rules implicit?  # even if not, fixed overhead?
                    rule_cost = 0
                    rule_cost += per_non_empty_patterns_cost  # tail cannot be empty
                    # if rule.is_tail_singleton():
                    #     rule_cost += per_non_empty_patterns_cost  # empty head singletons already excluded from description
                    # else:  # empty head rules still need to be separately encoded for indepenedent patterns
                    rule_cost += per_all_patterns_cost  # so as to not make it easier to describe empty-head or singleton rules?
                    self.rule_enc_cost_dict[rule]["model_enc_cost"] = rule_cost
                    cost += rule_cost

        else:  # describe equations
            # TO-DO: not possible to isolate out self.rule_enc_cost_dict[rule]["model_enc_cost"] = rule_cost???
            self.find_all_y_patterns() # whether including std rules, so that full causal model is described!
                                       # or excluding std rules, because they could be implicit?
            cost += compute_cost_lN(self.get_count_all_y_patterns() + 1) # number of equations
            for y_pat in self.all_y_patterns_excl_std:
                se_cost = 0
                se_cost += per_non_empty_patterns_cost  # empty cannot be a rule tail ever
                if len(y_pat) == 1: # singletons
                    head_count_excl_empty = 0
                    for rule in self.cover.rule_model.rules_list:
                        if rule.y_pattern == y_pat:
                            if not rule.is_standard(): # standard rules implicit? but then is it two different equations for same y!!
                                head_count_excl_empty += 1
                                se_cost += per_all_patterns_cost  # use all_pattern_count if empty to be explicitly allowed alongside non-empty head rules for same rule tail!
                                # se_cost += per_non_empty_patterns_cost  # use all_pattern_count if empty to be explicitly allowed alongside non-empty head rules for same rule tail!
                    se_cost += compute_cost_lN(head_count_excl_empty)
                else: # non-singletons
                    head_count_incl_empty = 0
                    for rule in self.cover.rule_model.rules_list:
                        if rule.y_pattern == y_pat:
                                head_count_incl_empty += 1
                                se_cost += per_all_patterns_cost  # use all_pattern_count if empty to be explicitly allowed alongside non-empty head rules for same rule tail!
                    se_cost += compute_cost_lN(head_count_incl_empty)
            
                cost += se_cost

        self.model_enc_cost = cost
        return cost
    
