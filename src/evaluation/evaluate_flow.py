from rule_definition.rule_model import RuleModel
from evaluation.similarity import *
import networkx as nx


def compute_F1(true_model : RuleModel, mined_model : RuleModel):
    true_positives = compute_true_positives(true_model, mined_model) # compute is here, avoid computing it twice
    recall = compute_recall(true_model, mined_model, true_positives=true_positives)
    precision = compute_precision(true_model, mined_model, true_positives = true_positives)
    F1 = 2 * recall * precision / (recall + precision)
    return (F1, recall, precision)


def compute_recall(true_model : RuleModel, mined_model : RuleModel, true_positives = None):
    if true_positives == None:
        true_positives = compute_true_positives(true_model,mined_model)
    return true_positives/true_model.get_size()


def compute_precision(true_model : RuleModel, mined_model : RuleModel, true_positives = None):
    if true_positives == None:
        true_positives = compute_true_positives(true_model,mined_model)
    return true_positives/mined_model.get_size()
    

def compute_true_positives(true_model: RuleModel, mined_model: RuleModel):
    planted = true_model.rules_list
    found = mined_model.rules_list
    weightFunc = lambda x,y: max(1-compute_rule_similarity(x,y),0)

    G = nx.DiGraph()
    G.add_node('source', layer=0)
    G.add_node('sink', layer=3)
    labels = {}
    for i, pi in enumerate(planted):
        i_name = 'p{}'.format(i);
        G.add_node(i_name, layer=1)
        labels[i_name] = (str(pi))
    for j, fj in enumerate(found):
        j_name = 'f{}'.format(j)
        G.add_node(j_name, layer=2)
        labels[j_name] = (str(fj))
    for i, pi in enumerate(planted):
        G.add_edge('source', 'p{}'.format(i), capacity=1)
    for j, _ in enumerate(found):
        G.add_edge('f{}'.format(j), 'sink', capacity=1)

    # source and sync side build up

    # connecting source and sync according to weightFunc
    for i, pi in enumerate(planted):
        for j, fj in enumerate(found):
            G.add_edge('p{}'.format(i), 'f{}'.format(j), capacity=weightFunc(pi,fj))

    max_flow, _ = nx.maximum_flow(G, 'source', 'sink')
    return max_flow