import random
import json
import numpy as np
from data_generator.generator_rules import *
import utils.constants as constants

class Generator():

    INSERT_RULE_TAIL = 0
    FILL_RULE = 1
    generator_option = INSERT_RULE_TAIL

    def __init__(self):
        self.alphabet_ids = []
        self.target_sequence_size = 1000
        self.target_noise = 0.40
        self.generated_sequence = []
        self.generated_noise = 0.0
        self.gen_rule_model = None
        self.gen_rule_model_param = {
            "num_rules": 5,
            "is_rule_head_random": False,
            "rule_conf": 0.75,
            "rule_head_size": 2,
            "rule_tail_size": 3,
            "rule_transitivity": 0
        }
        # TO-DO: decide gap/delay probability based on max ratio??
        self.gap_probability = 0
        self.delay_probability = 0
        # files to write to!
        self.write_sequence_file = None
        self.write_true_model_file = None

    def get_generated_sequence_size(self):
        return len(self.generated_sequence)


    def load_gen_rule_model_param(self, gen_rules_params_json_dict):
        self.gen_rule_model_param["num_rules"] = gen_rules_params_json_dict["num_rules"]
        self.gen_rule_model_param["is_rule_head_random"] = gen_rules_params_json_dict["is_rule_head_random"] or False
        self.gen_rule_model_param["rule_conf"] = gen_rules_params_json_dict["rule_conf"]
        self.gen_rule_model_param["rule_head_size"] = gen_rules_params_json_dict["rule_head_size"]
        self.gen_rule_model_param["rule_tail_size"] = gen_rules_params_json_dict["rule_tail_size"]
        self.gen_rule_model_param["rule_transitivity"] = gen_rules_params_json_dict["rule_transitivity"]

        if self.gen_rule_model_param["num_rules"] is None:
            self.target_sequence_size = random.choice(range(1, 10, 1))
        if self.gen_rule_model_param["rule_conf"] is None:
            self.target_noise = random.choice(range(99, 40, 1)) / 100
        if self.gen_rule_model_param["rule_head_size"] is None:
            self.gap_probability = random.choice(range(1, 5, 1))
        if self.gen_rule_model_param["rule_tail_size"] is None:
            self.delay_probability = random.choice(range(1, 5, 1))
        if self.gen_rule_model_param["rule_transitivity"] is None:
            self.delay_probability = random.choice(range(0, 4, 1))


    def load_gen_data_from_json_dict(self, gen_data_json_dict):
        random.seed(gen_data_json_dict["seed"])

        if not gen_data_json_dict['alphabet_IDs'] is None:
            self.alphabet_ids = gen_data_json_dict['alphabet_IDs']
        elif not gen_data_json_dict['alphabet_size'] is None:
            self.alphabet_ids = list(range(1, gen_data_json_dict['alphabet_size'] + 1))

        if not gen_data_json_dict["generator_rules"] is None:
            gen_rules_json_dict = gen_data_json_dict["generator_rules"]
            self.gen_rule_model = GeneratorRuleModel()
            self.gen_rule_model.load_rule_model_from_json_dict(gen_rules_json_dict)
        elif not gen_data_json_dict["generator_rules_param"] is None:
            self.load_gen_rule_model_param(gen_data_json_dict["generator_rules_param"])

        self.target_sequence_size = gen_data_json_dict["target_sequence_size"]
        self.target_noise = gen_data_json_dict["target_noise"]
        self.gap_probability = gen_data_json_dict["gap_probability"]
        self.delay_probability = gen_data_json_dict["delay_probability"]
        self.write_sequence_file = gen_data_json_dict["generated_sequences_file"]
        self.write_true_model_file = gen_data_json_dict["generated_true_model_file"]
        Generator.generator_option = gen_data_json_dict["generator_option"] or 0

        if self.target_sequence_size is None:
            self.target_sequence_size = random.choice(range(3000, 12000, 1))
        if self.target_noise is None:
            self.target_noise = random.choice(range(10, 60, 1)) / 100
        if self.gap_probability is None:
            self.gap_probability = random.choice(range(1, 20, 1)) / 100
        if self.delay_probability is None:
            self.delay_probability = random.choice(range(1, 20, 1)) / 100
    

    def generate_gen_rule_model_under_constraints(self):
        # randomize generation of rules subject to constraints (refer notes)!!
        used_alph = []
        self.gen_rule_model = GeneratorRuleModel()
        while self.gen_rule_model.get_size() < self.gen_rule_model_param["num_rules"]:
            # TO-DO: review if it should be sample (i.e, w/o replacement)
            avail = list(set(self.alphabet_ids) - set(used_alph))
            rule_head = random.choices(avail, k = int(self.gen_rule_model_param["rule_head_size"]))
            rule_head.sort()  # to be able to compare with competitors that do not respect order
            used_alph = used_alph + rule_head
            avail = list(set(self.alphabet_ids) - set(used_alph))
            rule_tail = random.choices(avail, k = int(self.gen_rule_model_param["rule_tail_size"]))
            rule_tail.sort()  # to be able to compare with competitors that do not respect order
            used_alph = used_alph + rule_tail
            rule = GeneratorRule(rule_head, rule_tail)
            rule.set_target_confidence(self.gen_rule_model_param["rule_conf"])
            self.gen_rule_model.add_rule(rule)
            if not self.gen_rule_model_param["is_rule_head_random"]:
                self.gen_rule_model.add_rule(GeneratorRule([-1], rule_head))
            if self.gen_rule_model_param["rule_transitivity"] > 0:
                # TO-DO: accommodate specified transitivity (within num_rules?)
                print("transitive rules currently not implemented in rule generator!")

    
    def generate_data(self):
        if self.gen_rule_model is None:  # generate generator model!
            self.generate_gen_rule_model_under_constraints()
        if Generator.generator_option == Generator.INSERT_RULE_TAIL:
            self.generate_sequence_insert_rule()
        elif Generator.generator_option == Generator.FILL_RULE:
            self.generate_sequence_fill_rule()
        else:
            raise ValueError('invalid generator option')
        # self.generate_sequences_random_x_fill_y()

        # write sequence to file (expects .txt file)         
        if not self.write_sequence_file is None:
            with open(self.write_sequence_file, 'w') as gen_file:
                for event in self.generated_sequence:
                    gen_file.write(str(event)+",")
                gen_file.write("\nlen: "+str(self.get_generated_sequence_size()))
                gen_file.write("\nnoise: "+str(self.generated_noise))
        # TO-DO: also report other generated data statistics?
        # write true model to file (expects .json file)
        # note: std model exl. when writing to file
        if not self.write_true_model_file is None:
            with open(self.write_true_model_file, 'w') as model_file:
                true_model_json = {}
                true_model_json["model"] = self.gen_rule_model.write_rule_model_to_json_dict(skip_standard=True)
                json.dump(true_model_json, model_file)


    def fill_transitive_or_overlap_rule_tail(self, transitive_or_overlap_rule, next_position):
        to_start_position = next_position
        hit = random.choices([1,0], cum_weights=[transitive_or_overlap_rule.target_confidence * 100, 100], k=1)[0]
        if hit:
            y_start = 0
            while not y_start:
                if to_start_position >= self.get_generated_sequence_size():
                    # stop midway like real data?!
                    break
                delay = random.choices([1,0], cum_weights=[self.delay_probability * 100, 100], k=1)[0] 
                if not delay:
                    y_start = 1
                    break
                to_start_position += 1
            if y_start:
                self.fill_rule_tail(transitive_or_overlap_rule, given_start_position=to_start_position)


    def fill_rule_tail(self, rule, given_start_position = None):
        if not rule.is_empty_head():
            # TO-DO: add check to ensure given_start_position exists
            next_position = given_start_position
        else:
            # block filling positions that could be contained by existing triggers so as to not mess with minimal triggers!!!
            # TO-DO: if using shortest trigger instead of minimal trigger, then this may not be needed
            if constants.trigger_xwin_option == constants.TRIGGER_XWIN_MINIMAL and not rule.is_tail_singleton():
                blocked_start_positions = self.gen_rule_model.find_blocked_start_positions(rule)
                potential_start_positions = list(set(range(0, self.get_generated_sequence_size())) - set(blocked_start_positions))
            else:
                potential_start_positions = list(range(0, self.get_generated_sequence_size()))
            next_position = random.choice(potential_start_positions)
        y_index = 0
        y_fills = []
        next_gap = 0
        while y_index < rule.get_y_pattern_size() and next_position < self.get_generated_sequence_size():  
            # restrict to within the max allowed gap ratio??
            if not next_gap:
                if self.generated_sequence[next_position] == 0:
                    self.generated_sequence[next_position] = rule.y_pattern[y_index]
                    y_index += 1
                    y_fills.append(next_position)
                    next_gap = random.choices([1,0], cum_weights=[self.gap_probability * 100, 100], k=1)[0]
                # else:
                #    TO-DO: handle noise in gap probability caused by already filled in positions!!
                #           will have to factor in delay as well if non-empty head rule?!
            else:
                next_gap = random.choices([1,0], cum_weights=[self.gap_probability * 100, 100], k=1)[0]
            next_position += 1
        if y_index >= rule.get_y_pattern_size():
            if not rule.is_standard():  # std rules do not have these fields!
                rule.increment_generated_rule_tails()
            # look for transitive rules, if found fill rule tail!
            transitive_rules = self.gen_rule_model.find_transitive_rules_to_trigger(rule)
            for transitive_rule in transitive_rules:
                transitive_rule.generated_trigger_xwins.append(Window(y_fills))
                self.fill_transitive_or_overlap_rule_tail(transitive_rule, next_position)
            # look for overlap rules, if found look for newly formed trigger, if found fill rule tail!
            overlap_rules = self.gen_rule_model.find_overlap_rules_to_trigger(rule)
            overlap_rules = list(set(overlap_rules) - set(transitive_rules))  # TO-DO: consider treating transitive rules the same as overlap rules!
            if len(overlap_rules) > 0 and not rule.is_standard():
                print("error: overlap found for non-empty or non-singleton rule: ", rule.x_pattern, " --> ", rule.y_pattern)
            for overlap_rule in overlap_rules:
                # this is needed to allow for randomly occuring rule head triggers
                # below strategy works only for minimal window triggers!!
                # look for minimal window triggers between gap ratio to the left and gap ratio to the right
                # such that trigger involves positions in y_fills, i.e, newly formed
                # such that there is no other existing trigger of same rule containing the newly formed trigger
                # OR such that no(/not whole?) part of the newly formed trigger is already part of another trigger of same rule?
                # OR add rule tail anyway if newly formed trigger found? potentially messes up association of rule tails to rule heads? 
                relevant_start = y_fills[0] - (constants.xy_win_gap_ratio_max + 1) * overlap_rule.get_x_pattern_size()
                relevant_end = y_fills[-1] + (constants.xy_win_gap_ratio_max + 1) * overlap_rule.get_x_pattern_size()
                if relevant_start < 0: 
                    relevant_start = 0
                if relevant_end >= self.get_generated_sequence_size(): 
                    relevant_end = self.get_generated_sequence_size()
                overlap_rule.find_trigger_xwins_in_seq(self.generated_sequence, relevant_start, relevant_end)
                y_fills_set = set(y_fills)
                for trigger in overlap_rule.trigger_xwins:
                    if len(y_fills_set.intersection(trigger.indices)) > 0:
                        existing_duplicate_trigger = False
                        for existing_trigger in overlap_rule.generated_trigger_xwins:
                            if constants.trigger_xwin_option == constants.TRIGGER_XWIN_MINIMAL and existing_trigger.indices[0] <= trigger.indices[0] and existing_trigger.indices[-1] >= trigger.indices[-1]:
                                existing_duplicate_trigger = True
                            elif constants.trigger_xwin_option == constants.TRIGGER_XWIN_SHORTEST and existing_trigger.indices[0] == trigger.indices[0]:
                                existing_duplicate_trigger = True
                        if not existing_duplicate_trigger:
                            overlap_rule.generated_trigger_xwins.append(trigger)
                            self.fill_transitive_or_overlap_rule_tail(overlap_rule, trigger.indices[-1]+1)
                            break  # let the new fill trigger only once per overlap rule at max
        elif next_position >= self.get_generated_sequence_size():
            # stop midway like real data?! or backtrack to previous state like below? re-try then?
            # for position in y_fills:
            #     self.generated_sequence[position] = 0
            pass
        else:
            print("error: control should never reach here in generation!")
        self.filled_sequence_size += len(y_fills)
        y_fills.clear()


    def generate_sequence_fill_rule(self):  
        # refer to notes on ipad to see reasoning behind this generation algorithm
        self.gen_rule_model.load_standard_rule_model(self.alphabet_ids)  # because the other generation algorithm doesn't expect std model currently
        self.generated_sequence = list(np.zeros((self.target_sequence_size,), dtype=int))
        self.filled_sequence_size = 0
        random_fills = 0
        while self.filled_sequence_size < self.target_sequence_size:
            sampled_index = random.choices(list(range(1,self.gen_rule_model.get_size())),k=1)[0]
            rule_to_fill = self.gen_rule_model.rules_list[sampled_index - 1]
            if not rule_to_fill.is_empty_head():  # non-empty head rules to be triggered, not planted
                continue
            if rule_to_fill.is_tail_singleton():
                if random_fills < self.target_noise * self.target_sequence_size:
                    random_fills += 1  # std model to be used only as noise
                else:
                    continue
            self.fill_rule_tail(rule_to_fill)

        # data generation complete - report generated data details:
        self.generated_noise = random_fills / self.get_generated_sequence_size()
        print("generated noise (Y's unexplained by any X inc. empty and random): ", self.generated_noise)
        print("generated sequence length: ", self.get_generated_sequence_size())
        for rule in self.gen_rule_model.rules_list:
            if not rule.is_standard():
                print("generated statistics for rule: ", rule.x_pattern, " --> ", rule.y_pattern)
                if not rule.is_empty_head():
                    trigger_count = len(rule.generated_trigger_xwins)
                    print("reported trigger_count: ", trigger_count)
                    if trigger_count > 0:
                        print("confidence: ", rule.generated_rule_tails/trigger_count)
                    else:
                        print("error: no triggers reported for rule head!")



    def generate_sequence_insert_rule(self):
        self.generated_sequence = list(np.zeros((self.target_sequence_size,), dtype=int))

        empty_head_rules = []
        for gen_rule in self.gen_rule_model.rules_list:
            if gen_rule.is_empty_head():
                empty_head_rules.append(gen_rule)
        if len(empty_head_rules) > 0:
            # generate empty head rule tails with equal probability to fill in the sequence
            count_filled = 0
            while count_filled < self.target_sequence_size * (1 - self.target_noise):  # TO-DO: half of this? to approximately accommodate rule tails...
                # TO-DO: review how to ensure uniform sampling!!
                sampled_index = random.choices(list(range(0,len(empty_head_rules))),k=1)[0]
                gen_rule = empty_head_rules[sampled_index]
                next_position = random.choice(range(0, self.get_generated_sequence_size() - gen_rule.get_y_pattern_size() * (1 + constants.xy_win_gap_ratio_max), 1))
                y_index = 0
                y_fills = []
                next_gap = 0
                while y_index < gen_rule.get_y_pattern_size() and next_position < self.get_generated_sequence_size():
                    if not next_gap:
                        if self.generated_sequence[next_position] == 0:
                            self.generated_sequence[next_position] = gen_rule.y_pattern[y_index]
                            y_index += 1
                            y_fills.append(next_position)
                            next_gap = random.choices([1,0], cum_weights=[self.gap_probability * 100, 100], k=1)[0]
                        # else:
                        #    TO-DO: handle noise in gap probability caused by already filled in positions!!
                    else:
                        next_gap = random.choices([1,0], cum_weights=[self.gap_probability * 100, 100], k=1)[0]
                    next_position += 1
                if y_index >= gen_rule.get_y_pattern_size():
                    count_filled += gen_rule.get_y_pattern_size()
                    gen_rule.increment_generated_trigger_count()
                elif next_position >= self.get_generated_sequence_size():
                    for position in y_fills:
                        self.generated_sequence[position] = 0
                else:
                    print("error: control should never reach here in generation!")
                y_fills.clear()
        for gen_rule in empty_head_rules:
            gen_rule.set_generated() 
            gen_rule.print_rule()
            print("generated_trigger_count (empty --> head rule): ", gen_rule.generated_trigger_count)   

        # fill in the rest of the sequence randomly using the full alphabet
        # TO-DO: assign slighlty higher probability to those alphabet which forms rule heads?? Nope!!
        for position in range(0, self.get_generated_sequence_size(), 1):
            if self.generated_sequence[position] == 0:
                self.generated_sequence[position] = random.choice(self.alphabet_ids)

        # for non empty head rule triggers, fill in the rule tail based on rule confidence
        pending_non_empty_head_rules = []
        for gen_rule in self.gen_rule_model.rules_list:
            if not gen_rule.is_empty_head() and not gen_rule.is_generated():
                pending_non_empty_head_rules.append(gen_rule)
        while len(pending_non_empty_head_rules) > 0:
            for gen_rule in pending_non_empty_head_rules:
                if self.gen_rule_model.is_prev_rule_generated_if_transitive(gen_rule):
                    print("filling rule: ")
                    gen_rule.print_rule()
                    gen_rule.find_trigger_xwins_in_seq(self.generated_sequence)  # find trigger_xwins everytime as previous iterations could change the windows for insertions!
                    # subsequent insertion of rule tails could break minimal windows as well as increase delays and gaps for past rules!!  
                    # keep tails disjoint (no overlap) for now, and keep track of positions filled/inserted
                    # TO-DO: 
                    # 1. transitive rules - handled by enforcing order!
                    # 2. multiple rules with same x_pattern?
                    # TO-DO: handle randomly occurring rule tails?
                    # 1. ignore -- 
                    # 2. remove -- 
                    # 3. take into account -- those forming rule heads accounted for by trigger calculation after each insertion!
                    # TO-DO: with each insertion of Y, the xwin trigger indices will change! offset added to account for this!
                    count_trigger_hits = 0
                    for trigger in gen_rule.trigger_xwins:
                        max_offset = count_trigger_hits * gen_rule.get_y_pattern_size()
                        next_position = trigger.get_end_index() + 1 + max_offset
                        hit = random.choices([1,0], cum_weights=[gen_rule.target_confidence * 100, 100], k=1)[0]
                        if hit:
                            y_index = 0
                            y_start = 0
                            while y_index < gen_rule.get_y_pattern_size():
                                if next_position >= self.get_generated_sequence_size():
                                    self.generated_sequence.insert(next_position - 1, random.choice(self.alphabet_ids))
                                if not y_start:
                                    delay = random.choices([1,0], cum_weights=[self.delay_probability * 100, 100], k=1)[0] 
                                if not delay:
                                    y_start = 1
                                    gap = random.choices([1,0], cum_weights=[self.gap_probability * 100, 100], k=1)[0]
                                    if not gap:
                                        self.generated_sequence.insert(next_position, gen_rule.y_pattern[y_index])
                                        y_index += 1
                                next_position += 1
                            count_trigger_hits += 1
                    gen_rule.set_generated()
                    pending_non_empty_head_rules.remove(gen_rule)

        self.generated_noise = self.target_noise * self.target_sequence_size / self.get_generated_sequence_size()
        # TO-DO: correct this for case where true model is empty, i.e, full random data!
        print("generated noise (Y's unexplained by any X inc. empty and random): ", self.generated_noise)
        print("generated sequence length: ", self.get_generated_sequence_size())
        # TO-DO: insert to match target_noise! --> again, noise in gap and delay probabilities!
