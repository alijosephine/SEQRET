from rule_definition.rule_model import RuleModel
from evaluation.similarity import *
from utils.util_methods import find_subsequence


def compute_F1(true_model : RuleModel, mined_model : RuleModel):
    recall = compute_recall(true_model, mined_model)
    precision = compute_precision(true_model, mined_model)
    F1 = 2 * recall * precision / (recall + precision)
    return (F1, recall, precision)


def compute_recall(true_model : RuleModel, mined_model : RuleModel):
    aggregate_recovery = 0
    for true_rule in true_model.rules_list:
        aggregate_recovery += compute_rule_recovery_or_correctness(true_rule, mined_model)
    return aggregate_recovery / true_model.get_size()


def compute_precision(true_model : RuleModel, mined_model : RuleModel):
    aggregate_correctness = 0
    precisions = []
    for mined_rule in mined_model.rules_list:
        precisions.append(compute_rule_recovery_or_correctness(mined_rule, true_model))
    precisions.sort(reverse=True)
    num_nonredundants = true_model.get_size() if true_model.get_size() < mined_model.get_size() else mined_model.get_size()
    aggregate_correctness = sum(precisions[:num_nonredundants])
    return aggregate_correctness / mined_model.get_size()
    

def compute_rule_recovery_or_correctness(target_rule: Rule, against_model : RuleModel):
    best_recovery = 0
    for against_rule in against_model.rules_list:
        recovery = compute_rule_similarity(target_rule, against_rule)
        if recovery > best_recovery:
            best_recovery = recovery
        if recovery > 0 and recovery < 1:
            against_chain = [against_rule]
            get_potential_against_chain(against_rule, against_model, target_rule, against_chain)
            if len(against_chain) > 1:
                aug_sim, aug_rule = get_best_augmented_rule_similarity(target_rule, against_chain)
                if aug_sim > best_recovery:
                    best_recovery = aug_sim
    return best_recovery


def get_potential_against_chain(against_rule : Rule, against_model : RuleModel, target_rule : Rule, against_chain):
    # TO-DO: there could be multiple potential rule chains starting from same rule?!
    #        ideally, the chain that maximizes precision to be found
    #        but here depth-first sub-optimal approach used!!!
    test_start_len = len(against_chain)
    for next_against_rule in against_model.rules_list:
        if not next_against_rule.is_empty_head() and not next_against_rule in against_chain and not next_against_rule == against_rule:
            # TO-DO: make this lcs_similarity > 0.5 instead??
            if not find_subsequence(next_against_rule.x_pattern, against_rule.x_pattern + against_rule.y_pattern) is None: # TO-DO: find trigger in tail only or head and tail combined?
                if compute_lcs_similarity(next_against_rule.y_pattern, target_rule.y_pattern) > 0:
                    against_chain.append(next_against_rule)  # list maintains order of insertion
                    if len(against_chain) < target_rule.get_y_pattern_size():  # TO-DO: review depth limit (logic: min one event per rule)
                        get_potential_against_chain(next_against_rule, against_model, target_rule, against_chain)
                    return against_chain  # return at this point so that multiple chains not considered!
    test_end_len = len(against_chain)
    if not test_start_len == test_end_len:
        print("error: some rule was added to against_chain but reached return statement after loop!!")
    return against_chain  
            

def get_best_augmented_rule_similarity(target_rule : Rule, against_chain):
    best_aug_similarity = 0
    best_aug_match = None
    weight = 1
    augmented_y = against_chain[0].y_pattern
    for rule in against_chain[1:]:
        augmented_y = augmented_y + rule.y_pattern
        augmented_rule = Rule(against_chain[0].x_pattern, augmented_y)
        weight *= 0.9  # TO-DO: 0.9 is an arbitrary choice!
        augmented_similarity = weight * compute_rule_similarity(target_rule, augmented_rule)
        if augmented_similarity > best_aug_similarity:
            best_aug_similarity = augmented_similarity
            best_aug_match = augmented_rule
    return best_aug_similarity, best_aug_match

