#  1. Parse hyper params, input data, test data and gen data form input json.
#  2. Generate sequence if spcified.
#  3. Pass input data and test data to cover algorithm.
#  4. Call cover, encoder or miner as specified. 

import argparse
import json
import time

import parse_input as input_parser
from sequential_data.sequential_data import *
from rule_definition.rule_model import *
from cover.greedy_cover import *
from encoding.encoding_over_events import *
from encoding.encoding_over_patterns import EncodingCausal
from miner.rule_miner import *
from evaluation.evaluate import *


#def secret_encode(candidate_model : RuleModel, seq_data : SequentialData, reload_triggers_and_candidates=True):
def secret_encode(candidate_model, seq_data, reload_triggers_and_candidates=True):
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


#def secret_mine(seq_data : SequentialData, mining_strategy="neigh") -> (RuleModel, float):
def secret_mine(seq_data, mining_strategy="neigh"):
    std_model = RuleModel()
    std_model.load_standard_rule_model(seq_data.alphabet_ids)
    start_time = time.time()
    min_cost_candidate, hypercompressed_candidate = mine_rule_model(seq_data, std_model, mining_strategy)
    end_time = time.time()
    runtime = (end_time - start_time)/60  # this is in minutes!!
    return min_cost_candidate, runtime, hypercompressed_candidate  


def secret_test(input_data):
    input_parser.parse_hyper_params(input_data)
    (seq_data, true_model) = input_parser.parse_test_data(input_data)
    print("Sequence data parsed and/or generated!")
    # load miner data
    mined_rules_file = input_data["mined_rule_model_file"]
    mining_strategy = input_data["miner_strategy"]
    miner_eval_metric = input_data["miner_eval_metric"]
    if not mined_rules_file is None:
        min_cost_candidate, runtime, hypercompressed = secret_mine(seq_data, mining_strategy)
        min_cost_encoding = secret_encode(min_cost_candidate, seq_data, reload_triggers_and_candidates=False)
        true_cost_encoding = secret_encode(true_model, seq_data, reload_triggers_and_candidates=False)
        # some eval metrics!
        min_cost_loss = min_cost_encoding.total_enc_cost - true_cost_encoding.total_enc_cost
        F1_score_non_redundant = evaluate(true_model, min_cost_candidate, miner_eval_metric, skip_standard=True)
        # replace with miner_eval_metric in input.json if that makes more sense!
        F1_score_simple = evaluate(true_model, min_cost_candidate, "simple", skip_standard=True)
        if ".txt" in mined_rules_file:
            with open(mined_rules_file, "w") as out_file:
                out_file.write("\n-------------------------------\nResult for MINED model: ... ")
                out_file.write("\nF1: " + str(F1_score_non_redundant[0]))
                out_file.write("\nrecall: " + str(F1_score_non_redundant[1]))
                out_file.write("\nprecision: " + str(F1_score_non_redundant[2]))
                out_file.write("\nF1_simple: " + str(F1_score_simple[0]))
                out_file.write("\nrecall_simple: " + str(F1_score_simple[1]))
                out_file.write("\nprecision_simple: " + str(F1_score_simple[2]))
                out_file.write("\nloss: " + str(min_cost_loss))
                out_file.write("\nminer_runtime: " + str(runtime))
                out_file.write("\ntotal encoding cost: " + str(min_cost_encoding.total_enc_cost))
                min_cost_candidate.print_rule_model(out_file, skip_standard=True)
        elif ".json" in mined_rules_file:
            json_dict = {}
            json_dict["model"] = min_cost_candidate.write_rule_model_to_json_dict(skip_standard=True)
            json_dict["total_encoding_cost"] = min_cost_encoding.total_enc_cost
            json_dict["F1"] = F1_score_non_redundant[0]
            json_dict["recall"] = F1_score_non_redundant[1]
            json_dict["precision"] = F1_score_non_redundant[2]
            json_dict["F1_simple"] = F1_score_simple[0]
            json_dict["recall_simple"] = F1_score_simple[1]
            json_dict["precision_simple"] = F1_score_simple[2]
            json_dict["loss"] = min_cost_loss
            json_dict["miner_runtime"] = runtime
            json_dict["hypercompressed_model"] = hypercompressed.write_rule_model_to_json_dict(skip_standard=True)
            with open(mined_rules_file, "w") as json_file:
                json.dump(json_dict, json_file)

    # load optional test data!
    test_rule_models_json = input_data["test_models"]
    test_model_enc_file = input_data["test_models_encoding_file"]
    if not test_model_enc_file is None:
        std_model = RuleModel()
        std_model.load_standard_rule_model(seq_data.alphabet_ids)
        with open(test_model_enc_file, "w") as out_file:
            out_file.write("Results for given test models are (in order of appearance in input file):")
            model_count = 0
            for model in test_rule_models_json:
                model_count += 1
                test_model = RuleModel()
                test_model.shallow_copy_rule_model(std_model)
                test_model.load_rule_model_from_json_dict(model)  
                encoding_lens = secret_encode(test_model, seq_data, reload_triggers_and_candidates=False)
                out_file.write("\nResult for model " + str(model_count) + ":")
                encoding_lens.print_encoding_cost(out_file=out_file, detailed=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='modes of operation', dest='mode', help='specify mode of operation: gen, mine, eval, test')
    gen_parser = subparsers.add_parser("gen")
    mine_parser = subparsers.add_parser("mine")
    eval_parser = subparsers.add_parser("eval")
    test_parser = subparsers.add_parser("test")

    test_parser.add_argument('input_file', type=str, help='required: path to input json file')
    gen_parser.add_argument('input_file', type=str, help='required: path to input json file for gen data')
    mine_parser.add_argument('input_file', type=str, help='required: path to input json file for hyper data')
    mine_parser.add_argument('seq_file', type=str, help='required: path to sequence.txt')
    mine_parser.add_argument('out_file', type=str, help='required: path to output.txt or output.json')
    mine_parser.add_argument('--strategy', type=str, choices=['neigh', 'combi', 'freq', 'freq_no_gap'], default="neigh", help='optional: specify eval metric to use')
    eval_parser.add_argument('true_file', type=str, help='required: path to true_model.json')
    eval_parser.add_argument('mined_file', type=str, help='required: path to mined_model.json')
    eval_parser.add_argument('--metric', type=str, choices=['simple', 'nonredundant', 'augment'], default="simple", help='optional: specify eval metric to use')
    eval_parser.add_argument('--not-skip-standard', action='store_true', help='optional: do not skip standard rules (take care to compare correctly in this case)')
    args = parser.parse_args()
   
    if args.mode == "test": 
        with open(args.input_file, 'r') as json_file:
            input_data = json.load(json_file)
            secret_test(input_data)
    elif args.mode == "eval":
        eval_metric = args.metric
        skip_standard = not args.not_skip_standard
        true_model_json_path = args.true_file
        mined_model_json_path = args.mined_file
        # TO-DO: currently expecting only json, handle .txt later!
        with open(true_model_json_path, 'r') as json_file:
            true_model_json = json.load(json_file)
            true_rule_model = RuleModel()
            true_rule_model.load_rule_model_from_json_dict(true_model_json["model"])
        with open(mined_model_json_path, 'r') as json_file:
            mined_model_json = json.load(json_file)
            mined_rule_model = None
            if "model" in mined_model_json.keys() and not mined_model_json["model"] is None:
                mined_rule_model = RuleModel()
                mined_rule_model.load_rule_model_from_json_dict(mined_model_json["model"])
        F1_score, recall, precision = evaluate(true_rule_model, mined_rule_model, eval_metric, skip_standard)  
        #TO-DO: output will be only printed to console now, write to mined rule model file instead?
        print("recall: ", recall)
        print("precision: ", precision)
        print("F1: ", F1_score)
    elif args.mode == "gen":
        with open(args.input_file, 'r') as json_file:
            input_data = json.load(json_file)
            generator = input_parser.parse_gen_data(input_data)
            generator.generate_data()
    elif args.mode == "mine":
        strategy = args.strategy
        with open(args.input_file, 'r') as json_file:
            input_data = json.load(json_file)
            input_parser.parse_hyper_params(input_data)
        #seq_data : SequentialData = input_parser.parse_sequence(args.seq_file)
        seq_data = input_parser.parse_sequence(args.seq_file)
        mined_model, runtime, hypercompressed = secret_mine(seq_data, mining_strategy=strategy)
        mined_cost = secret_encode(mined_model, seq_data, reload_triggers_and_candidates=False)
        if ".txt" in args.out_file:
            with open(args.out_file, "w") as out_file:
                out_file.write("\n-------------------------------\nResult for MINED model: ... ")
                out_file.write("\nminer_runtime: " + str(runtime))
                out_file.write("\ntotal encoding cost: " + str(mined_cost.total_enc_cost))
                mined_model.print_rule_model(out_file, skip_standard=True)
        elif ".json" in args.out_file:
            json_dict = {}
            json_dict["model"] = mined_model.write_rule_model_to_json_dict(skip_standard=True)
            json_dict["total_encoding_cost"] = mined_cost.total_enc_cost
            json_dict["miner_runtime"] = runtime
            json_dict["hypercompressed_model"] = hypercompressed.write_rule_model_to_json_dict(skip_standard=True)
            with open(args.out_file, "w") as json_file:
                json.dump(json_dict, json_file)

# note: test mode requires seq_data to be present in input.json, but evaluates wrt true model including encoding loss after mining! 