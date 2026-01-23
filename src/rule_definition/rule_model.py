from rule_definition.rule import Rule
from sequential_data.sequential_data import SequentialData

class RuleModel():

    def __init__(self):
        self.rules_list = []

    def rule_exists(self, other_rule):
        for rule in self.rules_list:
            if rule == other_rule:
                return True
        return False

    def add_rule(self, new_rule):
        if not self.rule_exists(new_rule):
            self.rules_list.append(new_rule)

    def remove_rule(self, other_rule):
        if self.rule_exists(other_rule):
                self.rules_list.remove(other_rule)

    def get_rule(self, other_rule):  # TO-DO: revisit: imp. note - hash values based on x and y patterns, therefore, same. objects could be still different!!
        for rule in self.rules_list:
            if rule == other_rule:
                return rule
        return None

    def get_size(self) -> int:
        return len(self.rules_list)
    

    def get_count_empty_head(self) -> int:  # incl. singletons
        # TO-DO: consider saving this value somewhere instead of O(alph+pattern+rules) method call
        count = 0
        for rule in self.rules_list:
            if rule.is_empty_head():
                count += 1
        return count


    def shallow_copy_rule_model(self, other_model, skip_standard=False):
        # shallow copy!
        self.rules_list = other_model.rules_list.copy()
    

    def load_standard_rule_model(self, alphabet):
        for event in alphabet:
            new_rule = Rule(-1, [event])
            self.add_rule(new_rule)

    def remove_standard_rules(self):
        to_remove = []
        for rule in self.rules_list:
            if rule.is_standard():
                to_remove.append(rule)
        for rule in to_remove:
            self.remove_rule(rule)

    def get_standard_rules_list(self):
        std_list = []
        for rule in self.rules_list:
            if rule.is_standard():
                std_list.append(rule)
        return std_list
    
    def get_non_standard_rules_list(self):
        non_std_list = []
        for rule in self.rules_list:
            if not rule.is_standard():
                non_std_list.append(rule)
        return non_std_list


    def load_rule_model_from_json_dict(self, rule_model_json, skip_standard=False):
        for rule_json in rule_model_json:
            new_rule = Rule(rule_json["X_pattern"], rule_json["Y_pattern"])
            if not skip_standard or not new_rule.is_standard():
                self.add_rule(new_rule)

    def write_rule_model_to_json_dict(self, skip_standard=False):
        json_dict_list = []
        for rule in self.rules_list:
            if not skip_standard or not rule.is_standard():
                json_dict_list.append({"X_pattern": rule.x_pattern, "Y_pattern": rule.y_pattern, "supp": rule.get_rule_support(), "conf": rule.get_rule_confidence()})
        return json_dict_list


    def print_rule_model(self, out_file=None, skip_standard=False):
        for rule in self.rules_list:
            if not skip_standard or not rule.is_standard():  
                rule.print_rule(out_file)


    def load_trigger_xwins(self, seq_data : SequentialData, reload=True):
        # TO-DO: how to ensure that if len(trigger_xwins) > 0, then trigger_xwins found for current sequence?
        # TO-DO: also, what if len(trigger_xwins) = 0 because there are no triggers?
        for rule in self.rules_list:
            if reload or len(rule.trigger_xwins) <= 0:
                if not rule.is_empty_head():
                    copy_found = False
                    for other_rule in self.rules_list:
                        if not rule == other_rule and rule.x_pattern == other_rule.x_pattern and len(other_rule.trigger_xwins) > 0:
                            rule.copy_trigger_xwins(other_rule)
                            copy_found = True
                            break
                    if not copy_found:
                        rule.find_trigger_xwins_in_sequences(seq_data)


    def load_candidate_rwin_tuples(self, seq_data : SequentialData, reload=True):
        # TO-DO: how to ensure that if support > 0, then rwins found for current sequence?
        #        also, what if support = 0 because there are no rwins?
        for rule in self.rules_list:
            if reload or rule.get_rule_support() <= 0:
                rule.find_candidate_rwin_tuples_in_sequences(seq_data)
        pass
        