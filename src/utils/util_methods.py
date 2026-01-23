def insert_event_in_pattern(pattern, event, position):
    if position >= -1 and position < len(pattern):
        return pattern[:position+1] + [event] + pattern[position+1:]
    else:
        print("error: invalid position to insert in pattern!")
        return pattern  # TO-DO: decide what to return in this case!


def find_subsequence(sub, sequence): 
    # finds first shortest subsequence
    # TO-DO: adapt to find all or minimal subsequencs if needed!
    seq_len = len(sequence) 
    sub_len = len(sub)
    start_index = 0
    while start_index <= (seq_len - sub_len):
        if sequence[start_index] == sub[0]:
            # potential window start
            indices = []
            indices.append(start_index)
            next_x_index = 1
            for forward_index in range(start_index + 1, seq_len):
                if next_x_index == sub_len:
                    # potential window end
                    break
                if sequence[forward_index] == sub[next_x_index]:
                    next_x_index += 1  
                    indices.append(forward_index)
            if next_x_index < sub_len:
                start_index += 1
                # TO-DO: keep track of next index matching self.x_pattern[0] in previous loop and jump to that index
                #        if none found, jump to forward_index
            else:
                return indices
                # below code to keep looking for subsequences (if needed to use in finding triggers!)
                # self.add_trigger_xwin(Window(indices))
                # start_index += 1
                # TO-DO: keep track of next index matching self.x_pattern[0] in previous loop and jump to that index
                #        if none found, jump to forward_index
        else:
            start_index += 1
    return None


def find_position_and_insert_in_list(oglist, val, desc=False):
    insert_pos = binary_search_position(oglist, val, desc)
    oglist.insert(insert_pos, val)  # val will be at insert_pos


#@jit(nopython=True)
def binary_search_position(oglist, val, desc=False) -> int:
    low = 0
    high = len(oglist) - 1

    while low <= high:
        mid = low + (high - low) // 2
        if oglist[mid] == val:
            return mid
        elif oglist[mid] < val:
            if desc:
                high = mid - 1
            else:
                low = mid + 1
        else:
            if desc:
                low = mid + 1
            else:
                high = mid - 1
    return low