from rule_definition.rule import *
from rule_definition.rule_model import *


class GeneratorRule(Rule):

    def __init__(self, x, y):
        super().__init__(x, y)
        self.target_confidence : float = 0.9  # target confidence could be different from actual confidence due to potential random occurences
        # below two used only by insert_rule generator option
        self.generated : bool = False
        self.generated_trigger_count : int = 0 # IMPORTANT - for empty --> head rules!!
        # below two only for fill_rule generator option (not for insert_rule generator option)
        self.generated_trigger_xwins = []  # to keep track of generated minimal triggers, both planted and random 
        self.generated_rule_tails = 0
        # Note: "generated.." different from actual support/confidence/trigger_xwins (actual is captured by parent rule class in encode/miner)

    def set_target_confidence(self, conf):
        if not conf is None:
            self.target_confidence = conf  # e.g: 0.6

    def increment_generated_rule_tails(self):
        self.generated_rule_tails += 1

    def increment_generated_trigger_count(self):
        self.generated_trigger_count += 1

    def set_generated(self):
        self.generated = True

    def is_generated(self):
        return self.generated



class GeneratorRuleModel(RuleModel):

    def __init__(self):
        super().__init__()

    def load_rule_model_from_json_dict(self, rule_model_dict):
        for rule_dict in rule_model_dict:
            new_rule = GeneratorRule(rule_dict["X_pattern"], rule_dict["Y_pattern"])
            new_rule.set_target_confidence(rule_dict["target_confidence"]) # e.g: 0.75
            self.add_rule(new_rule)

    def is_prev_rule_generated_if_transitive(self, rule):
        if not self.rule_exists(rule):
            print("error: in transitive generation check, given rule doesn't exist")
            return True
        for other_rule in self.rules_list:
            if other_rule.y_pattern == rule.x_pattern and not other_rule.is_generated() and not other_rule == rule:
                return False
        return True

    def find_transitive_rules_to_trigger(self, rule):
        transitive_rules = []
        if not self.rule_exists(rule):
            print("error: to find transitive rules, given rule doesn't exist")
        for other_rule in self.rules_list:
            if other_rule.x_pattern == rule.y_pattern:  # what about a --> a ??
                transitive_rules.append(other_rule)
        return transitive_rules
    
    def find_overlap_rules_to_trigger(self, rule):
        overlap_rules = []
        y_pattern_set = set(rule.y_pattern)  # order not taken into account for overlap!
        if not self.rule_exists(rule):
            print("error: to find overelap rules, given rule doesn't exist")
        for other_rule in self.rules_list:
            overlap = y_pattern_set.intersection(other_rule.x_pattern)  # what about ba --> ac ??
            if len(overlap) > 0:
                overlap_rules.append(other_rule)
        return overlap_rules
    
    def find_blocked_start_positions(self, rule):
        blocked_start_positions = []
        trans_rules = self.find_transitive_rules_to_trigger(rule)
        if len(trans_rules) > 0:
            sample_trans_rule = trans_rules[0]
            for trigger in sample_trans_rule.generated_trigger_xwins:
                s = trigger.indices[0]
                e = trigger.indices[-1]
                u = e - rule.get_y_pattern_size() + 1
                blocks = list(range(s,u))
                blocked_start_positions = blocked_start_positions + blocks
        return blocked_start_positions

