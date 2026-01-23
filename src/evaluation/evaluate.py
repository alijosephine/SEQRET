import evaluation.evaluate_simple_top_T as simple
import evaluation.evaluate_simple_non_redundant as non_redundant
import evaluation.evaluate_augment_top_T as augment
import evaluation.evaluate_flow as flow
from rule_definition.rule_model import RuleModel


def evaluate(true_model : RuleModel, mined_model : RuleModel, eval_metric="simple", skip_standard=True):
    if eval_metric == "nonredundant":
        metric = non_redundant
    elif eval_metric == "augment":
        metric = augment
    elif eval_metric == "simple":
        metric = simple
    elif eval_metric == "flow":
        metric = flow
    else:
        metric = non_redundant
        # nonredundant as default because --metric is optional

    if mined_model is None:
        return (-0.01,-0.01,-0.01)  # case some failure
    true_copy = RuleModel()
    mined_copy = RuleModel()
    true_copy.shallow_copy_rule_model(true_model)
    mined_copy.shallow_copy_rule_model(mined_model)
    if skip_standard:
        true_copy.remove_standard_rules()
        mined_copy.remove_standard_rules()
    if mined_copy.get_size() == 0:
        if true_copy.get_size() == 0:
            return (0.99, 0.99, 0.99)
        else:
            # miner didn't find any non-standard rule
            return (0.001,0.001,0.001)  # TO-DO: review!
    if true_copy.get_size() == 0 and mined_copy.get_size() > 0:
        # either case true model unknown or case sanity check fail!
        return (0.001,0.001,0.001)  # TO-DO: review!
    return metric.compute_F1(true_copy, mined_copy)