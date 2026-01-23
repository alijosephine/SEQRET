import numba as nb
from numba import int32
from numba.typed import List
from numba.experimental import jitclass

# sample = [[1, 2],[3,4]]
# list_of_list = List(List(x) for x in sample)  

# # Explicitly define the types of the key and value:
# inner_dict = nb.typed.Dict.empty(
#     key_type=nb.typeof("freq"),
#     value_type=nb.typeof(1)
# )
# # assign your default values
# inner_dict["freq"] = 0

# # Explicitly define the types of the key and value:
# outer_dict = nb.typed.Dict.empty(
#     key_type=nb.typeof(1),
#     value_type=nb.typeof(inner_dict)
# )
# # assign your default values
# outer_dict[1] = inner_dict

# spec = [
#     ('single_sequence', int32[:]), 
#     #('frequency_dict', nb.typed.Dict),
#     ('alphabet_ids', int32[:]),
#     ('sequences', nb.typeof(sample)),
#     ('frequency_dict', nb.typeof(outer_dict)),
# ]

# @jitclass(spec)
class SequentialData():

    def __init__(self):
        self.alphabet_ids = []
        self.single_sequence = []
        self.sequences = []
        self.frequency_dict = {}
        self.max_sequence_size = 0


    def load_sequential_data(self, al_ids, seqs):
        self.load_alph_ids(al_ids)
        self.load_sequences(seqs)
        self.compute_frequency()
        self.set_max_sequence_size()


    def load_alph_ids(self, al_ids):
        if len(al_ids) == 0:
            raise ValueError('alphabet cnnot be empty.')
        if len(set(al_ids)) < len(al_ids):
            raise ValueError('alphabet cannot contain duplicates.')
        if -1 in al_ids or 0 in al_ids:
            raise ValueError('-1 and 0 are not allowed as alphabet IDs.')
        self.alphabet_ids = al_ids


    def load_sequence(self, seq):
        if len(seq) == 0:
            raise ValueError('sequence cannot be empty.')
        if self.get_alphabet_size() == 0 or not set(seq).issubset(set(self.alphabet_ids)):
            raise ValueError('sequence data does not match the alphabet (or alphabet missing)')
        self.single_sequence = self.single_sequence + seq


    def load_sequences(self, seqs):
        if len(seqs) == 0:
            raise ValueError('sequences cannot be empty.')
        for seq in seqs:
            self.load_sequence(seq)
            self.sequences.append(seq)


    def get_alphabet_size(self) -> int:
        return len(self.alphabet_ids)


    def get_num_sequences(self) -> int:
        return len(self.sequences)
    

    def get_all_sequences_size(self) -> int:
        # below code was only used to verify that single_sequence captures all_sequences_size!
        # all_sequences_size = 0
        # for seq in self.sequences:
        #     all_sequences_size += len(seq)
        # if not all_sequences_size == len(self.single_sequence):
        #     print("error: all_sequences_size doesn't match single_sequence_size")
        # return all_sequences_size  # if not keeping single_sequence
        return len(self.single_sequence)
    

    def get_max_sequence_size(self) -> int:
        return self.max_sequence_size
    

    def set_max_sequence_size(self) -> int:
        max_sequence_size = 0
        for seq in self.sequences:
            if len(seq) > max_sequence_size:
                max_sequence_size = len(seq)
        self.max_sequence_size = max_sequence_size

    
    def get_sequence_size(self, seq_index=0) -> int:
        if seq_index >= 0 and seq_index < self.get_num_sequences():
            return len(self.sequences[seq_index])
        else:
            print("error: invalid seq_index as param!!")
    

    def get_sequence(self, seq_index=0):
        if seq_index >= 0 and seq_index < self.get_num_sequences():
            if self.get_sequence_size(seq_index=seq_index) > 0:
                return self.sequences[seq_index]
            else:
                print("error: retrieving an empty sequence!")
        else:
            print("error: invalid seq_index as param!!")


    def get_sequences(self):
        if self.get_all_sequences_size() > 0:
            return self.sequences
        else:
            print("error: retrieving an empty sequence!")


    def get_single_sequence(self):
        if self.get_all_sequences_size() > 0:
            return self.single_sequence
        else:
            print("error: no sequences present or sequences are all empty!")


    # review if below methods belongs here or in miner class
    def init_frequency_dict(self):
        for id in self.alphabet_ids:
            self.frequency_dict[id] = {"freq": 0}  # dict in case needed to extend with neighbors, if not, a vector would suffice, just ensure that IDs are same as indices

    def compute_frequency(self):
        self.init_frequency_dict()
        for event in self.single_sequence:
            self.frequency_dict[event]["freq"] += 1
        self.frequency_dict = dict(sorted(self.frequency_dict.items(), key=lambda item: item[1]["freq"], reverse=True))
        # does frequency_dict.keys() now return the alphabet_ids in sorted order?!

    # def get_alphabet_by_frequency(self):  
    #     # does frequency_dict.keys() return the alphabet_ids in sorted order anyway?!
    #     # not used in current miner, so no need to change it now!
    #     return sorted(self.alphabet_ids, key=lambda id: self.frequency_dict[id]["freq"], reverse=True)