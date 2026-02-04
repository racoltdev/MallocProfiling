alternating_stream_entropy.py:
    This file calculates a fragmentation metric related to information entropy, given a trace file. In reality, this metric diverges quite strongly from traditional entropy interpretations, and may better be understood as the assumed complexity of finding a suitable free space for allocating any size block by an allocator. An ideal entropy based fragmentation metric would attempt to measure the probability of the arrangment of allocated and free blocks - more precisely, how many ways there are to permute the allocated and free blocks within the available memory region. Calculating the permutations across realistic memory samples is prohibitively computationally expensive, so instead similar entropy based metrics perform some estimation of this value. [1] substitutes the permutation based probability with a ratio of the size of each free block over the total number of blocks. My method is extremely similar, except it account for the size of all blocks (free or not), and the total number of all blocks. Additionally, some method of encoding this information must be used, since it is unreasonable to treat free and allocated blocks the same way when calculating fragmentation. Both are useful, but they do have fundamental differences in regards to the work an allocator will have to do to perform an allocation. The information is encoded as a stream of integers, the first always being positive. Following values will have their sign swapped if they match the allocation status of the previous. For example, a memory region with 2 alloocated blocks of size 1, followed by 2 free blocks of size 3 would be encoded into a stream as [1, -1, -3, 3].





1: Entropy-Based Algorithms for Best Basis Selection
Ronald R. Coifman and Mladen Victor Wickerhauser
