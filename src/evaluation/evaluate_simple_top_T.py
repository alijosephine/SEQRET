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
    precisions = []
    for mined_rule in mined_model.rules_list:
        best_similarity, best_match = compute_best_rule_similarity(mined_rule, true_model)
        precisions.append(best_similarity)
    precisions.sort(reverse=True)
    num_nonredundants = true_model.get_size() if true_model.get_size() < mined_model.get_size() else mined_model.get_size()
    aggregate_correctness = sum(precisions[:num_nonredundants])
    return aggregate_correctness / mined_model.get_size()