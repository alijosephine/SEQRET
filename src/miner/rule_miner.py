import time

from rule_definition.rule import *
from rule_definition.rule_model import *
from sequential_data.sequential_data import *
from utils.util_methods import insert_event_in_pattern
from secret import secret_encode

# TO-DO: consider having some scoring system for rules and respective extensions (instead of threshold cut-off)?
# alternatively, some potential estimate instead of exact cover? or do both?


def check_candidate_rule_potential():
    pass


def extend_candidate_rule_by_neighbor(rule: Rule, neighbor):
    new_rules = []
    if rule.is_empty_head() and neighbor[1] == -1:
        new_rules.append(Rule([neighbor[2]], rule.y_pattern))
    if rule.is_empty_head() and neighbor[1] == rule.get_y_pattern_size() - 1: 
        new_rules.append(Rule(rule.y_pattern, [neighbor[2]]))                  
    if neighbor[0] == 'y':
        new_x = rule.x_pattern
        new_y = insert_event_in_pattern(rule.y_pattern, neighbor[2], neighbor[1])
    else:
        new_x = insert_event_in_pattern(rule.x_pattern, neighbor[2], neighbor[1])
        new_y = rule.y_pattern
    new_rules.append(Rule(new_x, new_y))
    return new_rules


def mine_rule_model(seq_data : SequentialData, init_model : RuleModel, strategy : int):
# try two approaches:
# 1. new rules by extending existing rules with alphabet in the neighborhood
# 2. new rules by combining exsiting rules (cross-product)
    if strategy == "neigh":
        return mine_rule_model_extend_rules_neighborhood(seq_data, init_model)
    elif strategy == "combi":
        return mine_rule_model_combine_rules(seq_data, init_model)
    else:
        return mine_rule_model_extend_rules_neighborhood(seq_data, init_model) # neigh as default
        #print("error: invalid miner strategy")
# Is there any significant difference between extending by neighbors vs extending by frequent events?
# In what kind of data could there be a difference? when less frequent evetns are caused by less frequent rules!!


def mine_rule_model_extend_rules_neighborhood(seq_data : SequentialData, init_model : RuleModel):
    # mining candidate models - naive greedy approach 
    required_stagnant_iterations = 1
    candidate_model = init_model
    current_encoding = secret_encode(candidate_model, seq_data, reload_triggers_and_candidates=True)  # reload=True for the first time
    current_cost = current_encoding.total_enc_cost
    null_model = RuleModel()
    null_model.shallow_copy_rule_model(candidate_model)
    null_cost = current_cost  # used to filter out spurious rules based on shaky "significance" criteria!
    sorted_standard_rules_list = sorted(candidate_model.get_standard_rules_list(), key=lambda rule: (rule.support, rule.confidence, rule.get_y_pattern_size(), rule.get_x_pattern_size()), reverse=True)
    consecutive_stagnant_iterations = 0
    build_num = 0
    considered_rules_model = RuleModel()  # used to capture all candidate_rules considered!!
    considered_rules_model.shallow_copy_rule_model(candidate_model)
    rejects = 0
    while True:
        prev_current_cost = current_cost
        rule_added = False
        # sorting only non-standard rules becasue sorting entire list not a good idea for large alphabet size!
        # also, order of extend matters!!!!!!!
        sorted_non_standard_rules_list = sorted(candidate_model.get_non_standard_rules_list(), key=lambda rule: (rule.support, rule.confidence, rule.get_y_pattern_size(), rule.get_x_pattern_size()), reverse=True)
        to_extend_list = sorted_non_standard_rules_list + sorted_standard_rules_list
        for rule in to_extend_list:
            for neighbor in rule.neighborhood_dict:
                # TO-DO: important decisions to review!
                # neighborhood dict filtered and sorted according to expectation determined in rule class
                # starting over after each addition!!!
                # alternatively, keep adding but break when stagnant score after a few iterations???
                candidate_rules = extend_candidate_rule_by_neighbor(rule, neighbor)
                for candidate_rule in candidate_rules:
                    if not candidate_model.rule_exists(candidate_rule): 
                        temp_candidate_model = RuleModel()
                        temp_candidate_model.shallow_copy_rule_model(candidate_model)
                        if considered_rules_model.rule_exists(candidate_rule):
                            continue  # to speed up and avoid revisiting rejected/pruned rules even if they might be profitable at a later point?
                            candidate_rule = considered_rules_model.get_rule(candidate_rule)
                        temp_candidate_model.add_rule(candidate_rule)
                        temp_encoding = secret_encode(temp_candidate_model, seq_data, reload_triggers_and_candidates=False)
                        considered_rules_model.add_rule(candidate_rule)  # to save already considered rule with triggers and rwins found!!
                        temp_cost = temp_encoding.total_enc_cost
                        if temp_cost + 5 < current_cost:
                            # if temp_encoding.rule_sym_dict[candidate_rule]["trigger_hits"] + temp_encoding.rule_sym_dict[candidate_rule]["residuals"] == 0:
                            #     print("error: how did temp_cost improve even when candidate rule is unused??")
                            # print("add candidate_rule:  ", candidate_rule.x_pattern, "  -->  ", candidate_rule.y_pattern)
                            candidate_model.add_rule(candidate_rule)
                            current_encoding = temp_encoding
                            current_cost = temp_cost
                            rule_added = True
                        elif not rule.is_standard():  # to allow replace option
                            temp_candidate_model.remove_rule(rule)
                            temp_encoding = secret_encode(temp_candidate_model, seq_data, reload_triggers_and_candidates=False)
                            temp_cost = temp_encoding.total_enc_cost
                            if temp_cost + 5 < current_cost:
                                # print("add candidate_rule:  ", candidate_rule.x_pattern, "  -->  ", candidate_rule.y_pattern)
                                # print("by removing rule:  ", rule.x_pattern, "  -->  ", rule.y_pattern)
                                candidate_model.add_rule(Rule(candidate_rule.x_pattern, candidate_rule.y_pattern))
                                candidate_model.remove_rule(rule)
                                current_encoding = temp_encoding
                                current_cost = temp_cost
                                rule_added = True
                        if not rule_added:
                            rejects += 1
                    if rule_added:
                        break
                if rule_added: 
                    break
            if rule_added:
                break
        # prune those rules which are a burden (in increasing order of size?)
        # prune based on usage in cover? i.e, refer to count of hits or residuals!
        to_prune_list = sorted(candidate_model.get_non_standard_rules_list(), key=lambda rule: (current_encoding.rule_sym_dict[rule]["trigger_hits"] + current_encoding.rule_sym_dict[rule]["residuals"], rule.get_y_pattern_size(), 0 - current_encoding.rule_enc_cost_dict[rule]["data_enc_cost"] - current_encoding.rule_enc_cost_dict[rule]["model_enc_cost"], rule.get_x_pattern_size()))
        for rule in to_prune_list:
            temp_candidate_model = RuleModel()
            temp_candidate_model.shallow_copy_rule_model(candidate_model)
            temp_candidate_model.remove_rule(rule)
            temp_encoding = secret_encode(temp_candidate_model, seq_data, reload_triggers_and_candidates=False)
            temp_cost = temp_encoding.total_enc_cost
            if temp_cost < current_cost:
                # print("pruning rule:  ", rule.x_pattern, "  -->  ", rule.y_pattern)
                candidate_model.remove_rule(rule)
                current_encoding = temp_encoding
                current_cost = temp_cost
        if prev_current_cost == current_cost:
            consecutive_stagnant_iterations += 1
        else:
            consecutive_stagnant_iterations = 0
        if consecutive_stagnant_iterations >= required_stagnant_iterations:
            break
        build_num += 1
    print(f'completed {build_num} iterations!')
    print(f'considered total {considered_rules_model.get_size()} distinct rules!')
    print(f'rejected total {rejects} rules!')

    # for rule in candidate_model.get_standard_rules_list():
    #     if not current_encoding.rule_sym_dict[rule]["trigger_hits"] + current_encoding.rule_sym_dict[rule]["residuals"] > 0:
    #         print("std rule unused:")
    #         rule.print_rule()
    hypercompressed_model = RuleModel()
    hypercompressed_model.shallow_copy_rule_model(candidate_model)
    # #pruning non-significant, spurious rules using no-hypercompressibility inequality!
    # for rule in candidate_model.get_non_standard_rules_list():
    #     temp_model = RuleModel()
    #     temp_model.shallow_copy_rule_model(null_model)
    #     temp_model.add_rule(rule)
    #     temp_encoding = secret_encode(temp_model, seq_data, reload_triggers_and_candidates=False)
    #     temp_cost = temp_encoding.total_enc_cost
    #     if not null_cost - temp_cost > 10:
    #         print("pruning rule:  ", rule.x_pattern, "  -->  ", rule.y_pattern, " with supp ", rule.get_rule_support(), " and conf ", rule.get_rule_confidence())
    #         candidate_model.remove_rule(rule)

    current_encoding = secret_encode(candidate_model, seq_data, reload_triggers_and_candidates=False)
    current_cost = current_encoding.total_enc_cost

    print("result: ")
    candidate_model.print_rule_model(skip_standard=True)

    return candidate_model, hypercompressed_model


def mine_rule_model_combine_rules(seq_data : SequentialData, init_model : RuleModel):
    print("error: miner - combine rules not implemented")
    pass
