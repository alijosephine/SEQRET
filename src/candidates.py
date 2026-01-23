from rule_definition.rule import *
from rule_definition.rule_model import *
from sequential_data.sequential_data import *
from parse_input import parse_sequence
from encoding.encoding_over_events import *
from encoding.encoding_over_patterns import *
from cover.greedy_cover import *
import json, argparse, time


#def secret_encode(candidate_model : RuleModel, seq_data : SequentialData, reload_triggers_and_candidates=True):
def secret_encode_redo(candidate_model, seq_data, reload_triggers_and_candidates=True):
    # TO-DO: currently, standard model has to be included into the model before calling secret_encode from wherever as needed!
    #        consider ensuring standard model inside this method (even if redundnat)!
    candidate_model.load_trigger_xwins(seq_data, reload=reload_triggers_and_candidates)
    candidate_model.load_candidate_rwin_tuples(seq_data, reload=reload_triggers_and_candidates)
    candidate_greedy_cover = GreedyCover(seq_data, candidate_model)
    candidate_greedy_cover.cover()
    if constants.encode_over_patterns:
        candidate_encoding = EncodingCausal(candidate_greedy_cover)
    else:
        candidate_encoding = Encoding(candidate_greedy_cover)
    candidate_encoding.compute_encoding()
    return candidate_encoding


def load_patterns_as_empty_head_rules(patterns_as_empty_head_rules_file):
    init_model = RuleModel()
    with open(patterns_as_empty_head_rules_file, 'r') as json_file:
        mined_model_json = json.load(json_file)
        if "model" in mined_model_json.keys() and not mined_model_json["model"] is None:
            init_model.load_rule_model_from_json_dict(mined_model_json["model"])
        else:
            print("some error in loading patterns as empty head rules model!")
    return init_model


def filter_rule_model_combine_patterns(seq_data : SequentialData, init_model : RuleModel):
    # first, extend init_model which is probably patterns_as_empty_head_rules with standard_rules!
    init_model.load_standard_rule_model(seq_data.alphabet_ids)
    # then, prepare all combination rules!!
    valid_combination_rules = []
    init_rules = init_model.rules_list
    for rule in init_rules:
        if not rule.is_empty_head():
            continue
        for other_rule in init_rules:
            if not rule.is_empty_head():
                continue
            if rule.is_standard() and other_rule.is_standard():
                continue
            combination_rule = Rule(rule.y_pattern, other_rule.y_pattern)
            valid_combination_rules.append(combination_rule)
            init_model.add_rule(combination_rule)
    # re-compute cost so that confidence is calculated...
    cost = secret_encode_redo(init_model, seq_data, reload_triggers_and_candidates=True).total_enc_cost  # reload=True for the first time
    print("cost with all combination rules: ", cost)
    for rule in init_model.rules_list:
        if rule.is_standard():
            continue
        if not rule.is_empty_head() and rule.get_rule_confidence() < 0.5:
            init_model.remove_rule(rule)
        elif rule.is_empty_head() and rule.get_rule_support() < 10:
            init_model.remove_rule(rule)
    # re-compute cost to know the compression
    cost = secret_encode_redo(init_model, seq_data, reload_triggers_and_candidates=False).total_enc_cost
    print("cost with filtered combination rules: ", cost)
    return cost, init_model


def mine_rule_model_combine_patterns(seq_data : SequentialData, init_model : RuleModel):
    # first, extend init_model which is probably patterns_as_empty_head_rules with standard_rules!
    init_model.load_standard_rule_model(seq_data.alphabet_ids)
    # then, prepare all combination rules!!
    # also, setup null_model to compare combination_rule against it and order by gain:
    null_model = RuleModel()
    null_model.load_standard_rule_model(seq_data.alphabet_ids)
    null_cost = secret_encode_redo(null_model, seq_data, reload_triggers_and_candidates=True).total_enc_cost  # reload=True for the first time
    temp_model = RuleModel()
    temp_model.shallow_copy_rule_model(null_model)
    combination_rules_costs = {}
    valid_combination_rules = []

    for rule in init_model.rules_list:
        if not rule.is_empty_head():
            continue
        if rule.is_standard():
            continue
        temp_model.add_rule(rule)
        temp_cost = secret_encode_redo(temp_model, seq_data, reload_triggers_and_candidates=False).total_enc_cost
        # if temp_cost < null_cost:
        combination_rules_costs[rule] = temp_cost
        valid_combination_rules.append(rule)
        temp_model.remove_rule(rule)

    for rule in init_model.rules_list:
        if not rule.is_empty_head():
            continue
        for other_rule in init_model.rules_list:
            if not rule.is_empty_head():
                continue
            if rule.is_standard() and other_rule.is_standard():
                continue
            combination_rule = Rule(rule.y_pattern, other_rule.y_pattern)
            temp_model.add_rule(combination_rule)
            temp_cost = secret_encode_redo(temp_model, seq_data, reload_triggers_and_candidates=False).total_enc_cost
            if temp_cost < null_cost:
                combination_rules_costs[combination_rule] = temp_cost
                valid_combination_rules.append(combination_rule)
            temp_model.remove_rule(combination_rule)
    valid_combination_rules.sort(key=lambda rule: combination_rules_costs[rule])  # ascnding order nby default, i.e least temp_cost first, i.e highest gain first. 
    
    # mining candidate models restricted to valid_combination_rules - naive greedy approach
    candidate_model = RuleModel()
    candidate_model.shallow_copy_rule_model(null_model)
    candidate_cost = secret_encode_redo(candidate_model, seq_data, reload_triggers_and_candidates=True).total_enc_cost
    for rule in valid_combination_rules:
        temp_model = RuleModel()
        temp_model.shallow_copy_rule_model(candidate_model)
        temp_model.add_rule(rule)
        temp_cost = secret_encode_redo(temp_model, seq_data, reload_triggers_and_candidates=False).total_enc_cost
        if temp_cost <= candidate_cost:
            candidate_cost = temp_cost
            candidate_model.add_rule(rule)
        else:
            break
    print("cost with greedy combination incl alph rules: ", candidate_cost)
    return candidate_cost, candidate_model


def mine_rule_model_combine_patterns_excl_alph(seq_data : SequentialData, init_model : RuleModel):
    # first, extend init_model which is probably patterns_as_empty_head_rules with standard_rules!
    init_model.load_standard_rule_model(seq_data.alphabet_ids)
    # then, prepare all combination rules!!
    # also, setup null_model to compare combination_rule against it and order by gain:
    null_model = RuleModel()
    null_model.load_standard_rule_model(seq_data.alphabet_ids)
    null_cost = secret_encode_redo(null_model, seq_data, reload_triggers_and_candidates=True).total_enc_cost  # reload=True for the first time
    temp_model = RuleModel()
    temp_model.shallow_copy_rule_model(null_model)
    combination_rules_costs = {}
    valid_combination_rules = []

    for rule in init_model.rules_list:
        if not rule.is_empty_head():
            continue
        if rule.is_standard():
            continue
        temp_model.add_rule(rule)
        temp_cost = secret_encode_redo(temp_model, seq_data, reload_triggers_and_candidates=False).total_enc_cost
        # if temp_cost < null_cost:
        combination_rules_costs[rule] = temp_cost
        valid_combination_rules.append(rule)
        temp_model.remove_rule(rule)

    for rule in init_model.rules_list:
        if not rule.is_empty_head():
            continue
        for other_rule in init_model.rules_list:
            if not rule.is_empty_head():
                continue
            #if rule.is_standard() and other_rule.is_standard():
            if rule.is_standard() or other_rule.is_standard():
                continue
            combination_rule = Rule(rule.y_pattern, other_rule.y_pattern)
            temp_model.add_rule(combination_rule)
            temp_cost = secret_encode_redo(temp_model, seq_data, reload_triggers_and_candidates=False).total_enc_cost
            if temp_cost < null_cost:
                combination_rules_costs[combination_rule] = temp_cost
                valid_combination_rules.append(combination_rule)
            temp_model.remove_rule(combination_rule)
    valid_combination_rules.sort(key=lambda rule: combination_rules_costs[rule])  # ascnding order nby default, i.e least temp_cost first, i.e highest gain first. 
    
    # mining candidate models restricted to valid_combination_rules - naive greedy approach
    candidate_model = RuleModel()
    candidate_model.shallow_copy_rule_model(null_model)
    candidate_cost = secret_encode_redo(candidate_model, seq_data, reload_triggers_and_candidates=True).total_enc_cost
    for rule in valid_combination_rules:
        temp_model = RuleModel()
        temp_model.shallow_copy_rule_model(candidate_model)
        temp_model.add_rule(rule)
        temp_cost = secret_encode_redo(temp_model, seq_data, reload_triggers_and_candidates=False).total_enc_cost
        if temp_cost <= candidate_cost:
            candidate_cost = temp_cost
            candidate_model.add_rule(rule)
        else:
            break
    print("cost with greedy combination excl alph rules: ", candidate_cost)
    return candidate_cost, candidate_model


def mine_rule_model_split_patterns_all(seq_data : SequentialData, init_model : RuleModel):
    # first, extend init_model which is probably patterns_as_empty_head_rules with standard_rules!
    #init_model.load_standard_rule_model(seq_data.alphabet_ids)
    # then, prepare all combination rules!!
    # also, setup null_model to compare combination_rule against it and order by gain:
    null_model = RuleModel()
    null_model.load_standard_rule_model(seq_data.alphabet_ids)
    null_cost = secret_encode_redo(null_model, seq_data, reload_triggers_and_candidates=True).total_enc_cost  # reload=True for the first time
    temp_model = RuleModel()
    temp_model.shallow_copy_rule_model(null_model)
    split_rules_costs = {}
    best_split_rules = []
    for rule in init_model.rules_list:
        if not rule.is_empty_head():
            continue
        if rule.is_standard():
            continue
        temp_model.add_rule(rule)
        temp_cost = secret_encode_redo(temp_model, seq_data, reload_triggers_and_candidates=False).total_enc_cost
        temp_model.remove_rule(rule)
        best_split_rule = rule
        best_split_cost = temp_cost
        for i in range(1,rule.get_y_pattern_size()):
            split_rule = Rule(rule.y_pattern[:i], rule.y_pattern[i:])
            temp_model.add_rule(split_rule)
            temp_cost = secret_encode_redo(temp_model, seq_data, reload_triggers_and_candidates=False).total_enc_cost
            temp_model.remove_rule(split_rule)
            if temp_cost < best_split_cost:
                best_split_cost = temp_cost
                best_split_rule = split_rule
        split_rules_costs[best_split_rule] = best_split_cost
        best_split_rules.append(best_split_rule)
    best_split_rules.sort(key=lambda rule: split_rules_costs[rule])  # ascnding order nby default, i.e least temp_cost first, i.e highest gain first. 
    
    # mining candidate models restricted to valid_split_rules - naive greedy approach
    candidate_model = RuleModel()
    candidate_model.shallow_copy_rule_model(null_model)
    candidate_cost = secret_encode_redo(candidate_model, seq_data, reload_triggers_and_candidates=False).total_enc_cost
    for rule in best_split_rules:
        # temp_model = RuleModel()
        # temp_model.shallow_copy_rule_model(candidate_model)
        # temp_model.add_rule(rule)
        # temp_cost = secret_encode_redo(temp_model, seq_data, reload_triggers_and_candidates=False).total_enc_cost
        # if temp_cost <= candidate_cost:
            #candidate_cost = temp_cost
            candidate_model.add_rule(rule)
        # else:
        #     break
    print("cost with split-all rules: ", candidate_cost)
    return candidate_cost, candidate_model


def mine_rule_model_split_patterns_greedy(seq_data : SequentialData, init_model : RuleModel):
    # first, extend init_model which is probably patterns_as_empty_head_rules with standard_rules!
    #init_model.load_standard_rule_model(seq_data.alphabet_ids)
    # then, prepare all combination rules!!
    # also, setup null_model to compare combination_rule against it and order by gain:
    null_model = RuleModel()
    null_model.load_standard_rule_model(seq_data.alphabet_ids)
    null_cost = secret_encode_redo(null_model, seq_data, reload_triggers_and_candidates=True).total_enc_cost  # reload=True for the first time
    candidate_model = RuleModel()
    candidate_model.shallow_copy_rule_model(null_model)
    candidate_cost = null_cost

    for rule in init_model.rules_list:
        if not rule.is_empty_head():
            continue
        if rule.is_standard():
            continue
        temp_model = RuleModel()
        temp_model.shallow_copy_rule_model(candidate_model)
        temp_model.add_rule(rule)
        temp_cost = secret_encode_redo(temp_model, seq_data, reload_triggers_and_candidates=False).total_enc_cost
        temp_model.remove_rule(rule)
        best_split_rule = rule
        best_split_cost = temp_cost
        for i in range(1,rule.get_y_pattern_size()):
            split_rule = Rule(rule.y_pattern[:i], rule.y_pattern[i:])
            temp_model.add_rule(split_rule)
            temp_cost = secret_encode_redo(temp_model, seq_data, reload_triggers_and_candidates=False).total_enc_cost
            temp_model.remove_rule(split_rule)
            if temp_cost < best_split_cost:
                best_split_cost = temp_cost
                best_split_rule = split_rule
        if best_split_cost < candidate_cost:
            candidate_model.add_rule(best_split_rule)
            candidate_cost = best_split_cost

    print("cost with split-greedy rules: ", candidate_cost)
    return candidate_cost, candidate_model

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('seq_file', type=str, help='required: path to input seq file')
    parser.add_argument('pattern_file', type=str, help='required: path to patterns as empty head rules json file')
    parser.add_argument('--choose', type=str, help='optional: options to run (splitall / splitgreedy / filter / combinewoalph / combinegreedy) as comma separated names')
    args = parser.parse_args()
   
    seq_data = parse_sequence(args.seq_file)
    init_model = load_patterns_as_empty_head_rules(args.pattern_file)

    filename_prefix = (args.pattern_file).split("_sqs.json")[0]
    # assuming it is real data, print to output json files, both raw and labeled!
    # later whichver works, can be finalized and adapted to synthetic experiments!
##########################################################3
    if args.choose and 'splitall' in args.choose:
        # all split
        init_model_copy_1 = RuleModel()
        init_model_copy_1.shallow_copy_rule_model(init_model)
        start_time = time.time()
        split_cost, split_rules_model_all = mine_rule_model_split_patterns_all(seq_data, init_model_copy_1)
        end_time = time.time()
        runtime = (end_time - start_time)/60  # this is in minutes!!
            
        filename_new = filename_prefix + "_sqsrules_splitall.json"
        filename_new_labeled = filename_prefix + "labeled_sqsrules_splitall.json"
        json_dict = {}
        json_dict["model"] = split_rules_model_all.write_rule_model_to_json_dict(skip_standard=True)
        json_dict["total_encoding_cost"] = split_cost
        with open(filename_new, "w") as json_file:
            json.dump(json_dict, json_file)
        print("completed split-all, runtime in mins: ", runtime)

##########################################################3
    if args.choose and 'splitgreedy' in args.choose:
        # greedy split
        init_model_copy_5 = RuleModel()
        init_model_copy_5.shallow_copy_rule_model(init_model)
        start_time = time.time()
        split_cost, split_rules_model_greedy = mine_rule_model_split_patterns_greedy(seq_data, init_model_copy_5)
        end_time = time.time()
        runtime = (end_time - start_time)/60  # this is in minutes!!
            
        filename_new = filename_prefix + "_sqsrules_splitgreedy.json"
        filename_new_labeled = filename_prefix + "labeled_sqsrules_splitgreedy.json"
        json_dict = {}
        json_dict["model"] = split_rules_model_greedy.write_rule_model_to_json_dict(skip_standard=True)
        json_dict["total_encoding_cost"] = split_cost
        with open(filename_new, "w") as json_file:
            json.dump(json_dict, json_file)
        print("completed split-greedy, runtime in mins: ", runtime)

#######################################################3
    if args.choose and 'combinewoalph' in args.choose:
        # greedy combination    # excl alph
        init_model_copy_2 = RuleModel()
        init_model_copy_2.shallow_copy_rule_model(init_model)
        start_time = time.time()
        greedy_cost, mined_rules_model_excl_alph = mine_rule_model_combine_patterns_excl_alph(seq_data, init_model_copy_2)
        end_time = time.time()
        runtime = (end_time - start_time)/60  # this is in minutes!!

        filename_new = filename_prefix + "_sqsrules_greedywoalph.json"
        filename_new_labeled = filename_prefix + "labeled_sqsrules_greedywoalph.json"
        json_dict = {}
        json_dict["model"] = mined_rules_model_excl_alph.write_rule_model_to_json_dict(skip_standard=True)
        json_dict["total_encoding_cost"] = greedy_cost
        with open(filename_new, "w") as json_file:
            json.dump(json_dict, json_file)
        print("compltd greedy wo alph, runtime in mins: ", runtime)

##################################################
    if args.choose and 'filter' in args.choose:
        # filtered
        init_model_copy_3 = RuleModel()
        init_model_copy_3.shallow_copy_rule_model(init_model)
        start_time = time.time()
        filtered_cost, filtered_rule_model = filter_rule_model_combine_patterns(seq_data, init_model_copy_3)
        end_time = time.time()
        runtime = (end_time - start_time)/60  # this is in minutes!!

        filename_new = filename_prefix + "_sqsrules_filter.json"
        filename_new_labeled = filename_prefix + "labeled_sqsrules_filter.json"
        json_dict = {}
        json_dict["model"] = filtered_rule_model.write_rule_model_to_json_dict(skip_standard=True)
        json_dict["total_encoding_cost"] = filtered_cost
        with open(filename_new, "w") as json_file:
            json.dump(json_dict, json_file)
        print("completed filter, runtime in mins: ", runtime)

#####################################################3
    if args.choose and 'combinegreedy' in args.choose:
        # greedy combination    # incl alph
        init_model_copy_4 = RuleModel()
        init_model_copy_4.shallow_copy_rule_model(init_model)
        start_time = time.time()
        greedy_cost, mined_rules_model = mine_rule_model_combine_patterns(seq_data, init_model_copy_4)
        end_time = time.time()
        runtime = (end_time - start_time)/60  # this is in minutes!!

        filename_new = filename_prefix + "_sqsrules_greedyalph.json"
        filename_new_labeled = filename_prefix + "labeled_sqsrules_greedyalph.json"
        json_dict = {}
        json_dict["model"] = mined_rules_model.write_rule_model_to_json_dict(skip_standard=True)
        json_dict["total_encoding_cost"] = greedy_cost
        with open(filename_new, "w") as json_file:
            json.dump(json_dict, json_file)
        print("completed greedy with alph, runtime in mins: ", runtime)
