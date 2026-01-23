from rule_definition.rule_model import RuleModel
from evaluation.similarity import *


def compute_F1(true_model : RuleModel, mined_model : RuleModel):
    recall = compute_recall(true_model, mined_model)
    precision = compute_precision(true_model, mined_model)
    F1 = 2 * recall * precision / (recall + precision)
    return (F1, recall, precision)


def compute_recall(true_model : RuleModel, mined_model : RuleModel):
    aggregate_recovery = 0
    for true_rule in true_model.rules_list:
        best_similarity, best_match = compute_best_rule_similarity(true_rule, mined_model)
        aggregate_recovery += best_similarity
    return aggregate_recovery / true_model.get_size()


def compute_precision(true_model : RuleModel, mined_model : RuleModel):
    aggregate_correctness = 0
    # penalize redundancy in mined model, otherwise, they will boost precision!
    # redundancy = mined rules with overlap in tail and matched to same true rule? choose best or average? solve as a matching problem?
    # minus the number of redundant rules and pick the top remaining correctness?
    correctness_dict = {}
    matched_dict = {}
    mined_model.rules_list.sort(key = lambda x : x.get_y_pattern_size())  # TO-DO: rethink time complexity
    min_redundancy = 0
    max_redundancy = 0
    all_precisions = []
    for mined_rule in mined_model.rules_list:
        best_similarity, best_match = compute_best_rule_similarity(mined_rule, true_model)
        all_precisions.append(best_similarity)
        if not best_match in matched_dict:
            correctness_dict[mined_rule] = best_similarity
            matched_dict[best_match] = [mined_rule]
        else:
            collission = False
            colliding_rules = []
            colliding_correctness = 0
            for other_match in matched_dict[best_match]:
                # similarity betwn tails only or whole rule?
                if compute_lcs_similarity(mined_rule.y_pattern, other_match.y_pattern) > 0:
                # if compute_rule_similarity(mined_rule, other_match) >= 0.5:
                    collission = True
                    max_redundancy += 1
                    colliding_rules.append(other_match)
                    colliding_correctness += correctness_dict[other_match]
            if not collission:
                correctness_dict[mined_rule] = best_similarity
                matched_dict[best_match].append(mined_rule)
            else:
                min_redundancy += 1
                if colliding_correctness > best_similarity:
                    pass # do nothing, discard this mined rule as redundant!
                else:
                    for other_match in colliding_rules:
                        matched_dict[best_match].remove(other_match)
                        del correctness_dict[other_match]
                    matched_dict[best_match].append(mined_rule)
                    correctness_dict[mined_rule] = best_similarity

    all_precisions.sort(reverse=True)
    num_nonredundants = mined_model.get_size() - min_redundancy
    aggregate_correctness = sum(all_precisions[:num_nonredundants])
    alt_precision = aggregate_correctness / mined_model.get_size()
    print("min_redundancy p:", alt_precision)
    num_nonredundants = mined_model.get_size() - max_redundancy
    aggregate_correctness = sum(all_precisions[:num_nonredundants])
    alt_precision = aggregate_correctness / mined_model.get_size()
    print("max_redundancy p:", alt_precision)
    aggregate_correctness = 0
    for mined_rule in correctness_dict:
        aggregate_correctness += correctness_dict[mined_rule]
    alt_precision = aggregate_correctness / mined_model.get_size()
    print("exact_redundancy p:", alt_precision)
    return aggregate_correctness / mined_model.get_size()