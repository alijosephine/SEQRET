from rule_definition.rule import Rule
from rule_definition.rule_model import RuleModel


def compute_lcs_similarity(target_pattern, against_pattern):
    # distance metric should be symmetric, both LCS distance and Leveshtein distance are symmetric 
    # LCS as similarity!!
    m = len(target_pattern) 
    n = len(against_pattern)
    L = [[0 for x in range(n + 1)] 
            for y in range(m + 1)] 
    for i in range(m + 1):
        for j in range(n + 1):
            if (i == 0 or j == 0):
                L[i][j] = 0
            elif (target_pattern[i - 1] == against_pattern[j - 1]):
                L[i][j] = L[i - 1][j - 1] + 1
            else:
                L[i][j] = max(L[i - 1][j],
                              L[i][j - 1]) 
    lcs = L[m][n]
    # return (m - lcs) + (n - lcs)  # this is the lcs edit distance!
    similarity = 2 * lcs / (m + n)  # normalize over m + n
    return similarity
# TO-DO: rethink normalizing over (m + n) 


def compute_rule_similarity(target_rule : Rule, against_rule : Rule):
    target_x_pattern = target_rule.x_pattern
    target_y_pattern = target_rule.y_pattern
    against_x_pattern = against_rule.x_pattern
    against_y_pattern = against_rule.y_pattern
    # handle empty-heads:
    if target_rule.is_empty_head():
        target_x_pattern = []
    if against_rule.is_empty_head():
        against_x_pattern = []
    # compute similarity wrt heads
    # compute similarity wrt tails
    # compute similarity wrt whole
    # aggregate as weighted average!
    if target_rule.is_empty_head() and against_rule.is_empty_head():
        rule_sim = compute_lcs_similarity(target_y_pattern, against_y_pattern)
    else:
        head_sim = compute_lcs_similarity(target_x_pattern, against_x_pattern)
        tail_sim = compute_lcs_similarity(target_y_pattern, against_y_pattern)
        whole_sim = compute_lcs_similarity(target_x_pattern + target_y_pattern, against_x_pattern + against_y_pattern)
        rule_sim = 1/4 * head_sim + 1/4 * tail_sim + 1/2 * whole_sim  
    # TO-DO: any other weightage?
    return rule_sim


def compute_best_rule_similarity(target_rule: Rule, against_model : RuleModel):
    best_similarity = 0
    best_match = None
    for against_rule in against_model.rules_list:
        similarity = compute_rule_similarity(target_rule, against_rule)
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = against_rule
    return best_similarity, best_match