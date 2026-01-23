# from numba import int32
# from numba.experimental import jitclass

# spec = [
#     ('seq_index', int32), 
#     ('indices', int32[:])
# ]

# @jitclass(spec)
class Window():

    # xy_win_gap_ratio_max : int = 2  # x and y windows have same gap ratio?
    # delay_ratio_max : int = xy_win_gap_ratio_max  # as a ratio of max(x,y) or just y?
    # rule_tail_gap_ratio_max : int = xy_win_gap_ratio_max + delay_ratio_max  # tail refers to (delay + ywin_gaps) 

    def __init__(self, indices, seq_index=0): # TO-DO: hint type of indices as list[int] somehow..
        self.indices = indices.copy()  # shallow copy to avoid unexpected mutations
        self.seq_index = seq_index

    def get_seq_index(self) -> int:
        if not self.indices == None and len(self.indices) > 0:
            return self.seq_index
        else:
            print("error: attempt to get seq_index for empty x/y window")
            return None

    def get_start_index(self) -> int:
        if not self.indices == None and len(self.indices) > 0:
            return self.indices[0]
        else:
            print("error: attempt to get start_index for empty x/y window")
            return None
    
    def get_end_index(self) -> int:
        if not self.indices == None and len(self.indices) > 0:
            return self.indices[len(self.indices) - 1]
        else:
            print("error: attempt to get end_index for empty x/y window")
            return None
    
    def get_win_len(self) -> int:
        return self.indices[len(self.indices) - 1] - self.indices[0] + 1