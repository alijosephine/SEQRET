import math
import numpy

from cover.greedy_cover import GreedyCover
from rule_definition.rule import Rule
from utils.compute import *
import utils.constants as constants

class Encoding():

    #####################
    ##  best trigger options: 2 and 7, 
    ##  2 better for shorter squences as recall high, 
    ##  7 better for longer sequences as precision high
    #####################

    # TRIGGER_EMPTY_ALWAYS = 0
    # TRIGGER_EMPTY_LAST = 1
    # TRIGGER_EMPTY_PATTERN_SECOND_SINGLETON_LAST = 2
    # TRIGGER_EMPTY_PATTERN_ALWAYS_SINGLETON_LAST = 3
    # SINGLETON_RESIDUAL_UNIFORM_EMPTY_ALWAYS = 4 
    # SINGLETON_RESIDUAL_UNIFORM_EMPTY_LAST = 5
    # SINGLETON_RESIDUAL_OPTIMAL_EMPTY_ALWAYS = 6  # optimal based on usage
    # SINGLETON_RESIDUAL_OPTIMAL_EMPTY_LAST = 7  # optimal based on usage
    # PATTERN_RESIDUAL_OPTIMAL = 8  # optimal based on usage
    # # below option - singletons and patterns grouped together, alphabet size might have an influence...
    # #                therefore, do not consider. doesn't make sense to use uniform code here anyway!!
    # PATTERN_RESIDUAL_UNIFORM = 9

    # trigger_order = TRIGGER_EMPTY_ALWAYS

    def __init__(self, cover):
        self.cover : GreedyCover = cover
        self.rule_sym_dict = {}
        self.init_rule_sym_dict()
        
        self.model_enc_cost : float = 0
        self.data_enc_cost : float = 0
        self.total_enc_cost : float = 0
        self.rule_enc_cost_dict = {}
        self.init_rule_enc_cost_dict()

        # applicable only in case of residuals and set as part of update_rule_sym_dict!
        self.total_residual_usage = 0  
        self.count_residual_rules = 0  


    def init_rule_sym_dict(self):
        for rule in self.cover.rule_model.rules_list:
            self.rule_sym_dict[rule] = {"fills": 0,
                                        "gaps": 0,
                                        "starts": 0,
                                        "delays": 0,
                                        "trigger_hits": 0,
                                        "trigger_misses": 0,
                                        "residuals": 0}

    def init_rule_enc_cost_dict(self):
        for rule in self.cover.rule_model.rules_list:
            self.rule_enc_cost_dict[rule] = {"gap_stream_cost": 0,
                                                  "delay_stream_cost": 0,
                                                  "trigger_stream_cost": 0,
                                                  "residual_cost": 0,
                                                  "data_enc_cost": 0,
                                                  "model_enc_cost": 0} # note that model_enc_cost doesn't make sense in causal model!!!

    def update_rule_sym_dict(self):
        total_empty_head_trigger_hits = 0
        total_empty_head_singleton_trigger_hits = 0
        for rwin in self.cover.selected_rwins:
            rule = rwin.rule
            if rule.is_empty_head():               #empty-head
                if rule.get_y_pattern_size() == 1: #singleton
                    self.rule_sym_dict[rule]["trigger_hits"] += 1
                    total_empty_head_singleton_trigger_hits += 1
                else:
                    self.rule_sym_dict[rule]["fills"] += rule.get_y_pattern_size() - 1  # -1 because first fill automatically written down after start symbol
                    self.rule_sym_dict[rule]["gaps"] += rwin.y_window.get_win_len() - rule.get_y_pattern_size()
                    self.rule_sym_dict[rule]["trigger_hits"] += 1
                total_empty_head_trigger_hits += 1
            else:                                  #non-empty head
                if rule.get_y_pattern_size() == 1: #singleton
                    self.rule_sym_dict[rule]["starts"] += 1
                    self.rule_sym_dict[rule]["delays"] += rwin.get_delay()
                    self.rule_sym_dict[rule]["trigger_hits"] += 1
                else:
                    self.rule_sym_dict[rule]["fills"] += rule.get_y_pattern_size() - 1  # -1 because first fill automatically written down after start symbol
                    self.rule_sym_dict[rule]["gaps"] += rwin.y_window.get_win_len() - rule.get_y_pattern_size()
                    self.rule_sym_dict[rule]["starts"] += 1
                    self.rule_sym_dict[rule]["delays"] += rwin.get_delay()
                    self.rule_sym_dict[rule]["trigger_hits"] += 1
        
        # update trigger_misses, trigger_hits and residuals as required:
        for rule in self.cover.rule_model.rules_list:
            if not rule.is_empty_head():
                self.rule_sym_dict[rule]["trigger_misses"] = rule.get_trigger_count() - self.rule_sym_dict[rule]["trigger_hits"]
            else: #empty-head
                if constants.trigger_order == constants.TRIGGER_EMPTY_ALWAYS:
                    self.rule_sym_dict[rule]["trigger_misses"] = self.cover.seq_data.get_all_sequences_size() - self.rule_sym_dict[rule]["trigger_hits"]
                elif constants.trigger_order == constants.TRIGGER_EMPTY_LAST:
                    self.rule_sym_dict[rule]["trigger_misses"] = total_empty_head_trigger_hits - self.rule_sym_dict[rule]["trigger_hits"]
                elif constants.trigger_order in [constants.TRIGGER_EMPTY_PATTERN_SECOND_SINGLETON_LAST, constants.TRIGGER_EMPTY_PATTERN_ALWAYS_SINGLETON_LAST]:
                    if rule.is_tail_singleton() == 1: #singleton
                        self.rule_sym_dict[rule]["trigger_misses"] = total_empty_head_singleton_trigger_hits - self.rule_sym_dict[rule]["trigger_hits"]
                    elif constants.trigger_order == constants.TRIGGER_EMPTY_PATTERN_SECOND_SINGLETON_LAST:
                        self.rule_sym_dict[rule]["trigger_misses"] = total_empty_head_trigger_hits - self.rule_sym_dict[rule]["trigger_hits"]
                    elif constants.trigger_order == constants.TRIGGER_EMPTY_PATTERN_ALWAYS_SINGLETON_LAST:
                        self.rule_sym_dict[rule]["trigger_misses"] = self.cover.seq_data.get_all_sequences_size() - self.rule_sym_dict[rule]["trigger_hits"]
                # residuals....
                elif constants.trigger_order in [constants.SINGLETON_RESIDUAL_UNIFORM_EMPTY_LAST, constants.SINGLETON_RESIDUAL_UNIFORM_EMPTY_ALWAYS, constants.SINGLETON_RESIDUAL_OPTIMAL_EMPTY_ALWAYS, constants.SINGLETON_RESIDUAL_OPTIMAL_EMPTY_LAST]:
                    if rule.is_tail_singleton() == 1: #singleton
                        self.rule_sym_dict[rule]["residuals"] = self.rule_sym_dict[rule]["trigger_hits"]
                        self.rule_sym_dict[rule]["trigger_hits"] = 0
                    elif constants.trigger_order in [constants.SINGLETON_RESIDUAL_UNIFORM_EMPTY_ALWAYS, constants.SINGLETON_RESIDUAL_OPTIMAL_EMPTY_ALWAYS]:
                        self.rule_sym_dict[rule]["trigger_misses"] = self.cover.seq_data.get_all_sequences_size() - self.rule_sym_dict[rule]["trigger_hits"]
                    else:
                        self.rule_sym_dict[rule]["trigger_misses"] = total_empty_head_trigger_hits - self.rule_sym_dict[rule]["trigger_hits"]
                elif constants.trigger_order in [constants.PATTERN_RESIDUAL_OPTIMAL, constants.PATTERN_RESIDUAL_UNIFORM]:
                    self.rule_sym_dict[rule]["residuals"] = self.rule_sym_dict[rule]["trigger_hits"]
                    self.rule_sym_dict[rule]["trigger_hits"] = 0
                else:
                    raise ValueError('invalid trigger order')
                
        # update total_residual_usage and count_residual_rules
        if constants.trigger_order in [constants.PATTERN_RESIDUAL_OPTIMAL, constants.PATTERN_RESIDUAL_UNIFORM]:
            self.total_residual_usage = total_empty_head_trigger_hits
            self.count_residual_rules = self.cover.rule_model.get_count_empty_head()
        elif constants.trigger_order in [constants.SINGLETON_RESIDUAL_UNIFORM_EMPTY_LAST, constants.SINGLETON_RESIDUAL_UNIFORM_EMPTY_ALWAYS, constants.SINGLETON_RESIDUAL_OPTIMAL_EMPTY_ALWAYS, constants.SINGLETON_RESIDUAL_OPTIMAL_EMPTY_LAST]:
            self.total_residual_usage = total_empty_head_singleton_trigger_hits
            self.count_residual_rules = self.cover.seq_data.get_alphabet_size()

    
    def compute_encoding(self):
        self.update_rule_sym_dict()  # should always be called prior to calculating costs!
        self.compute_cost_total()
        self.update_rule_data_enc_cost_dict()

    def compute_cost_total(self) -> float:
        self.total_enc_cost = self.compute_cost_model_enc() + self.compute_cost_data_enc()
        return self.total_enc_cost

    def compute_cost_model_enc(self) -> float:
        cost = compute_cost_lN(self.cover.rule_model.get_size() - self.cover.seq_data.get_alphabet_size() + 1) + compute_cost_lN(self.cover.seq_data.get_alphabet_size())
        # note - number of patterns aka empty head non-singletons not needed even if case pattern_residual because it can be inferred from rule descriptions!
        #        (applicable only when rules defined over events)
        event_cost = math.log(self.cover.seq_data.get_alphabet_size(), 2)  # assuming uniform cost over the alphabet!
        for rule in self.cover.rule_model.rules_list:
            if not rule.is_standard():  # standard rules implicit?
                rule_cost = 0
                rule_cost += compute_cost_lN(rule.get_x_pattern_size() + 1) + compute_cost_lN(rule.get_y_pattern_size())
                rule_cost += (rule.get_x_pattern_size() + rule.get_y_pattern_size()) * event_cost
                self.rule_enc_cost_dict[rule]["model_enc_cost"] = rule_cost
                cost += rule_cost
        self.model_enc_cost = cost
        return cost

    def compute_cost_data_enc(self) -> float:
        self.data_enc_cost = self.compute_cost_gap_stream() + self.compute_cost_delay_stream() + self.compute_cost_trigger_stream() # + lN(|D|) + |D| * lN(|S|) if not single sequence!! # currently ignored
        if constants.trigger_order in [constants.SINGLETON_RESIDUAL_UNIFORM_EMPTY_LAST, constants.SINGLETON_RESIDUAL_UNIFORM_EMPTY_ALWAYS, constants.SINGLETON_RESIDUAL_OPTIMAL_EMPTY_ALWAYS, constants.SINGLETON_RESIDUAL_OPTIMAL_EMPTY_LAST, constants.PATTERN_RESIDUAL_OPTIMAL, constants.PATTERN_RESIDUAL_UNIFORM]:
            self.data_enc_cost += self.compute_cost_residuals()
        if constants.trigger_order in [constants.SINGLETON_RESIDUAL_OPTIMAL_EMPTY_LAST, constants.SINGLETON_RESIDUAL_OPTIMAL_EMPTY_ALWAYS, constants.PATTERN_RESIDUAL_OPTIMAL]:
            self.data_enc_cost += compute_cost_lU(self.total_residual_usage - 1 + self.count_residual_rules, self.count_residual_rules - 1) + compute_cost_lN(self.total_residual_usage + 1)
        return self.data_enc_cost

    def compute_cost_gap_stream(self) -> float:
        cost = 0
        for rule in self.cover.rule_model.rules_list:
            if rule.get_y_pattern_size() > 1 and self.rule_sym_dict[rule]["fills"] + self.rule_sym_dict[rule]["gaps"] > 0: # non-singletons only
                gap_stream_cost = compute_cost_preq(self.rule_sym_dict[rule]["fills"], self.rule_sym_dict[rule]["gaps"])
                self.rule_enc_cost_dict[rule]["gap_stream_cost"] = gap_stream_cost
                cost += gap_stream_cost
        return cost

    def compute_cost_delay_stream(self) -> float:
        cost = 0
        for rule in self.cover.rule_model.rules_list:
            if not rule.is_empty_head() and self.rule_sym_dict[rule]["starts"] + self.rule_sym_dict[rule]["delays"] > 0: # non-empty-heads only
                delay_stream_cost = compute_cost_preq(self.rule_sym_dict[rule]["starts"], self.rule_sym_dict[rule]["delays"])
                self.rule_enc_cost_dict[rule]["delay_stream_cost"] = delay_stream_cost
                cost += delay_stream_cost
        return cost

    def compute_cost_trigger_stream(self) -> float:
        cost = 0
        for rule in self.cover.rule_model.rules_list:
            if self.rule_sym_dict[rule]["trigger_hits"] + self.rule_sym_dict[rule]["trigger_misses"] > 0:
                trigger_stream_cost = compute_cost_preq(self.rule_sym_dict[rule]["trigger_hits"], self.rule_sym_dict[rule]["trigger_misses"])
                self.rule_enc_cost_dict[rule]["trigger_stream_cost"] = trigger_stream_cost
                cost += trigger_stream_cost
        return cost
    
    def compute_cost_residuals(self) -> float:
        # called in case of any of the residual trigger orders (singleton/pattern/uniform/optimal)
        cost = 0
        for rule in self.cover.rule_model.rules_list:
            if rule.is_empty_head():
                if constants.trigger_order in [constants.PATTERN_RESIDUAL_OPTIMAL, constants.PATTERN_RESIDUAL_UNIFORM]: 
                    residual_cost = self.rule_sym_dict[rule]["residuals"] * self.compute_cost_residual_code(rule, uniform=(constants.trigger_order == constants.PATTERN_RESIDUAL_UNIFORM))
                    self.rule_enc_cost_dict[rule]["residual_cost"] = residual_cost
                    cost += residual_cost
                elif rule.is_tail_singleton():  # empty-head singletons only
                    residual_cost = self.rule_sym_dict[rule]["residuals"] * self.compute_cost_residual_code(rule, uniform=(constants.trigger_order in [constants.SINGLETON_RESIDUAL_UNIFORM_EMPTY_LAST, constants.SINGLETON_RESIDUAL_UNIFORM_EMPTY_ALWAYS]))
                    self.rule_enc_cost_dict[rule]["residual_cost"] = residual_cost
                    cost += residual_cost
        return cost


    def compute_cost_residual_code(self, rule : Rule, uniform=True) -> float:
        if uniform:
            return math.log(self.count_residual_rules, 2)
        elif constants.trigger_order in [constants.SINGLETON_RESIDUAL_OPTIMAL_EMPTY_LAST, constants.SINGLETON_RESIDUAL_OPTIMAL_EMPTY_ALWAYS, constants.PATTERN_RESIDUAL_OPTIMAL]:
            if self.rule_sym_dict[rule]["residuals"] == 0:
                return 0
            relative_frequency_reciprocal = self.total_residual_usage / self.rule_sym_dict[rule]["residuals"]
            return math.log(relative_frequency_reciprocal, 2)
        else:
            print("error: compute pattern_incl_event code called with uniform=False but trigger_order not residual_optimal, then why?")


    # def compute_cost_preq(self, count1 : int, count2 : int) -> float:
    #     cost = 0
    #     # TO-DO: speedup: use numpy.log() as an array!!
    #     pre_log_vals = []
    #     for i in range(1, count1+1):
    #         pre_log = (2 * Encoding.preq_epsilon + i) / (Encoding.preq_epsilon + i)
    #         pre_log_vals.append(pre_log)
    #         # cost += math.log(pre_log, 2)
    #     cost += numpy.log2(pre_log_vals).sum()

    #     pre_log_vals = []
    #     for i in range(1, count2+1):
    #         pre_log = (2 * Encoding.preq_epsilon + count1 + i) / (Encoding.preq_epsilon + i)
    #         pre_log_vals.append(pre_log)
    #         # cost += math.log(pre_log, 2)
    #     cost += numpy.log2(pre_log_vals).sum()
    #     return cost


    # def compute_cost_lU(self, n : int, k : int) -> float:  # cost of n choose k
    #     nCk = math.comb(n, k)   
    #     return math.log(nCk, 2)
    

    # def compute_cost_lN(self, count : int) -> float:
    #     cost = 0
    #     while count >= 1:
    #         count = math.log(count, 2)        
    #         cost += count
    #     return cost + math.log(2.865064, 2)


    def update_rule_data_enc_cost_dict(self):
        for rule in self.cover.rule_model.rules_list:
            self.rule_enc_cost_dict[rule]["data_enc_cost"] = self.rule_enc_cost_dict[rule]["gap_stream_cost"] + self.rule_enc_cost_dict[rule]["delay_stream_cost"] + self.rule_enc_cost_dict[rule]["trigger_stream_cost"] + self.rule_enc_cost_dict[rule]["residual_cost"]
    


#####################  print methods for debug/test etc. #####################################
    

    def print_rule_data_enc_cost(self, rule, out_file=None):
        rule.print_rule(out_file)
        if out_file is None:
            print("gap stream cost: ", self.rule_enc_cost_dict[rule]["gap_stream_cost"])
            print("delay stream cost: ", self.rule_enc_cost_dict[rule]["delay_stream_cost"])
            print("trigger stream cost: ", self.rule_enc_cost_dict[rule]["trigger_stream_cost"])
            print("residual stream cost: ", self.rule_enc_cost_dict[rule]["residual_cost"])
            print("data encoding cost: ", self.rule_enc_cost_dict[rule]["data_enc_cost"])
        else:
            out_file.write("\ngap stream cost: " + str(self.rule_enc_cost_dict[rule]["gap_stream_cost"]))
            out_file.write("\ndelay stream cost: " + str(self.rule_enc_cost_dict[rule]["delay_stream_cost"]))
            out_file.write("\ntrigger stream cost: " + str(self.rule_enc_cost_dict[rule]["trigger_stream_cost"]))
            out_file.write("\nresidual stream cost: " + str(self.rule_enc_cost_dict[rule]["residual_cost"]))
            out_file.write("\ndata encoding cost: " + str(self.rule_enc_cost_dict[rule]["data_enc_cost"]))


    def print_each_stream_data_enc_cost(self, out_file=None):
        gap_stream_cost = 0
        delay_stream_cost = 0
        trigger_stream_cost = 0
        residual_stream_cost = 0
        for rule in self.cover.rule_model.rules_list:
            gap_stream_cost += self.rule_enc_cost_dict[rule]["gap_stream_cost"]
            delay_stream_cost += self.rule_enc_cost_dict[rule]["delay_stream_cost"]
            trigger_stream_cost += self.rule_enc_cost_dict[rule]["trigger_stream_cost"]
            residual_stream_cost += self.rule_enc_cost_dict[rule]["residual_cost"]
        if out_file is None:
            print("total gap stream cost: ", gap_stream_cost)
            print("total delay stream cost: ", delay_stream_cost)
            print("total trigger stream cost: ", trigger_stream_cost)
            print("total residual stream cost: ", residual_stream_cost)
        else:
            out_file.write("\ntotal gap stream cost: " + str(gap_stream_cost))
            out_file.write("\ntotal delay stream cost: " + str(delay_stream_cost))
            out_file.write("\ntotal trigger stream cost: " + str(trigger_stream_cost))
            out_file.write("\ntotal residual stream cost: " + str(residual_stream_cost))


    def print_rule_sym_count(self, rule, out_file=None):
        rule.print_rule(out_file)
        if out_file is None:
            print("triggers: ", self.rule_sym_dict[rule]["trigger_hits"] + self.rule_sym_dict[rule]["trigger_misses"])
            print("hits: ", self.rule_sym_dict[rule]["trigger_hits"])
            print("misses: ", self.rule_sym_dict[rule]["trigger_misses"])
            print("gaps: ", self.rule_sym_dict[rule]["gaps"])
            print("fills: ", self.rule_sym_dict[rule]["fills"])
            print("delays: ", self.rule_sym_dict[rule]["delays"])
            print("starts: ", self.rule_sym_dict[rule]["starts"])
            print("residuals: ", self.rule_sym_dict[rule]["residuals"])
        else:
            out_file.write("\ntriggers: " + str(self.rule_sym_dict[rule]["trigger_hits"] + self.rule_sym_dict[rule]["trigger_misses"]))
            out_file.write("\nhits: " + str(self.rule_sym_dict[rule]["trigger_hits"]))
            out_file.write("\nmisses: " + str(self.rule_sym_dict[rule]["trigger_misses"]))
            out_file.write("\ngaps: " + str(self.rule_sym_dict[rule]["gaps"]))
            out_file.write("\nfills: " + str(self.rule_sym_dict[rule]["fills"]))
            out_file.write("\ndelays: " + str(self.rule_sym_dict[rule]["delays"]))
            out_file.write("\nstarts: " + str(self.rule_sym_dict[rule]["starts"]))
            out_file.write("\nresiduals: " + str(self.rule_sym_dict[rule]["residuals"]))

    
    def print_encoding_cost(self, out_file=None, detailed=False, skip_standard=True):
        if out_file is None:
            print("model encoding cost: ", self.model_enc_cost)
            print("data encoding cost: ", self.data_enc_cost)
            print("total encoding cost: ", self.total_enc_cost)
        else:
            out_file.write("\nRESULT: ... ")
            out_file.write("\nmodel encoding len: " + str(self.model_enc_cost) + 
                           "\ndata encoding len: " + str(self.data_enc_cost) + 
                           "\ntotal encoding len: " + str(self.total_enc_cost))
            if detailed:
                out_file.write("\n\n---------Deatiled Counts and Costs per Rule: ... ")
                for rule in self.cover.rule_model.rules_list:
                    if not skip_standard or not rule.is_standard():
                        self.print_rule_sym_count(rule, out_file)
                        self.print_rule_data_enc_cost(rule, out_file)
                        out_file.write("\n--------------------------------------------------")
                out_file.write("\n\n---------Deatiled Costs per Stream: ... ")
                self.print_each_stream_data_enc_cost(out_file)
            out_file.write("\n*******************************************************************************\n")
