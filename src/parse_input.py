import json

from encoding.encoding_over_events import Encoding
from encoding.encoding_over_patterns import EncodingCausal
from rule_definition.window import Window
from rule_definition.rule_window import RuleWindow
from rule_definition.rule import Rule

from rule_definition.rule_model import RuleModel
from data_generator.generator import Generator
from sequential_data.sequential_data import SequentialData

import utils.constants as constants


def parse_hyper_params(input_data_json):
    constants.xy_win_gap_ratio_max = input_data_json["hyper_params"]["xy_win_gap_ratio_max"] or 2
    constants.delay_ratio_max = input_data_json["hyper_params"]["delay_ratio_max"] or constants.xy_win_gap_ratio_max
    constants.rule_tail_gap_ratio_max = input_data_json["hyper_params"]["rule_tail_gap_ratio_max"] or (constants.delay_ratio_max + constants.xy_win_gap_ratio_max)
    constants.trigger_order = input_data_json["hyper_params"]["trigger_order"] or 0
    # EncodingCausal.trigger_order = input_data_json["hyper_params"]["trigger_order"] or 0
    constants.causal_eqn_flag = input_data_json["hyper_params"]["encode_causal"] or False
    constants.encode_over_patterns = input_data_json["hyper_params"]["encode_over_patterns"] or False
    constants.candidate_order = input_data_json["hyper_params"]["candidate_order"] or 0
    constants.trigger_xwin_option = input_data_json["hyper_params"]["trigger_win_option"] or 0


def validate_gen_data(gen_data_json):
    if gen_data_json['alphabet_IDs'] is None and gen_data_json['alphabet_size'] is None:
        raise ValueError('either alph_size or alph_IDs expected as input if sequence is to be generated!')
    if gen_data_json["generator_rules_param"] is None and gen_data_json["generator_rules"] is None:
        raise ValueError('generator rules or generator specifications missing!')

#def parse_gen_data(input_data_json) -> Generator:
def parse_gen_data(input_data_json):
    gen_data_json = input_data_json["gen_data"]
    validate_gen_data(gen_data_json)
    generator = Generator()
    generator.load_gen_data_from_json_dict(gen_data_json)
    return generator


#def parse_sequence(sequence_file: str) -> SequentialData:
def parse_sequence(sequence_file):
    with open(sequence_file, 'r') as seq_file:
        seqs = []
        single_seq = []
        sequences = [line.rstrip('\n') for line in seq_file]
        for sequence in sequences:
            if ":" not in sequence:  # hack to skip lines of meta data printed by secret generator!!
                seq = [int(event.strip()) for event in sequence.split(',') if event]  # expecting only comma-separated IDs
                seqs.append(seq)
                single_seq = single_seq + seq
        alph_ids = set(single_seq)  # alphabet loaded from sequenceparse_sequence
        print("alphabt_size: ", len(alph_ids))
        seq_data = SequentialData()
        seq_data.load_sequential_data(alph_ids, seqs)
        return seq_data


#def parse_test_data(input_data_json) -> (SequentialData, RuleModel):
def parse_test_data(input_data_json):
    seq_data = None
    true_model = None
    
    seq_data_json = input_data_json["seq_data"]
    if not seq_data_json["given_sequences_file"] is None: # (expects .txt)
        seq_data = parse_sequence(seq_data_json["given_sequences_file"])
        true_model = RuleModel()
        if not seq_data_json["given_true_model_file"] is None and '.json' in seq_data_json["given_true_model_file"]:  # TO-DO: (expects .json) hanlde text?
            with open(seq_data_json["given_true_model_file"], 'r') as true_model_json_file:
                true_model_json = json.load(true_model_json_file)
                true_model.load_rule_model_from_json_dict(true_model_json["model"])
    else:
        generator = parse_gen_data(input_data_json)
        generator.generate_data()
        seq_data = SequentialData()
        seqs = []
        seqs.append(generator.generated_sequence)
        seq_data.load_sequential_data(generator.alphabet_ids, seqs)
        true_model = generator.gen_rule_model
    
    true_model.load_standard_rule_model(seq_data.alphabet_ids)   # might be already satisfied, still no harm in ensuring!                                   
    return (seq_data, true_model)

