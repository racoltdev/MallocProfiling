alternating_stream_entropy.py:
    This file calculates a fragmentation metric related to information entropy, given a trace file. In reality, this metric diverges quite strongly from traditional entropy interpretations, and may better be understood as the assumed complexity of finding a suitable free space for allocating any size block by an allocator. An ideal entropy based fragmentation metric would attempt to measure the probability of the arrangment of allocated and free blocks - more precisely, how many ways there are to permute the allocated and free blocks within the available memory region. Calculating the permutations across realistic memory samples is prohibitively computationally expensive, so instead similar entropy based metrics perform some estimation of this value. [2], [7] substitutes the permutation based probability with a ratio of the size of each free block over the total number of blocks. My method is extremely similar, except it accounts for the size of all blocks (free or not), and the total number of all blocks. Additionally, some method of encoding this information must be used, since it is unreasonable to treat free and allocated blocks the same way when calculating fragmentation. Both are useful, but they do have fundamental differences in regards to the work an allocator will have to do to perform an allocation. The information is encoded as a stream of integers, the first always being positive. Following values will have the same sign as the previous value if they match the allocation state (allocated vs free) of the previous block. For example, a memory region with 3 alloocated blocks of size 1, followed by 2 free blocks of size 3 would be encoded into a stream as [1, -1,, 1, 3, -3].

ebfm: Implements ebfm as shown in [2], [7]

Sawicki_Arduino.py:
	This is an equation posited by Adam Sawicki in [3] and (similarly) implemented by arduino to measure allocator performance following [4]. I cannot find academic use of this forumala, although it shares some similarities to the RSS formula used in [5], which is, of course, uncited and unexplained.

external_fragmentation.py
	This is the common definition of fragmentation, originally developed by [6] \(as far as i can tell\). It's even listed on wikipedia as *the* fragmentation metric \(the page then ignores any other existing or used measures, but that's wikipedia for you\). It is dependent only on the size of the largest free block and the total free memory. This metric obviously has problems, but its common.

ssfm.py
	Implemented as per [2]. Attempts to combine various existing metrics into something that is more stable against various edge cases.




1: Entropy-Based Algorithms for Best Basis Selection
Ronald R. Coifman and Mladen Victor Wickerhauser
https://ieeexplore.ieee.org/document/119732
Note: I'll keep this reference here even though I don't directly use it since it is referenced by [2] for ebfm. This does discuss entropy, but more as a way of deciding optimal allocations along frequency space, I think. I don't understand this paper at all and it only seems to be related in that both this and [2] consider entropy in the context of frequency allocations. 

2: A novel fragmentation metric and fragmentation-aware adaptive routing and spectrum allocation algorithm in elastic optical network
Ruchi Srivastava, Yatindra Nath Singh
https://www.sciencedirect.com/science/article/pii/S1068520025001932#b14

Sawicki / Arduino method
Adam Sawicki, david gauchard (d-a-v github user)
3: https://asawicki.info/news_1757_a_metric_for_memory_fragmentation
4: https://github.com/esp8266/Arduino/pull/5090

5: Fragmentation metrics and fragmentation-aware algorithm for spectrally/spatially flexible optical networks
Piotr Lechowicz, Massimo Tornatore, Adam Wªodarczyk, Krzysztof Walkowiak
https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9055890

6: The Memory Fragmentation Problem: Solved?
Mark S. Johnstone, Paul R. Wilson
https://dl.acm.org/doi/epdf/10.1145/301589.286864

7: Simulation Results of Shannon Entropy based Flexgrid Routing and Spectrum Assignment on a Real Network Topology
Paul Wright, Michael C. Parker, Andrew Lord
https://www.researchgate.net/publication/261042470_Simulation_Results_of_Shannon_Entropy_based_Flexgrid_Routing_and_Spectrum_Assignment_on_a_Real_Network_Topology/link/54abba570cf2bce6aa1d9d72/download?_tp=eyJjb250ZXh0Ijp7ImZpcnN0UGFnZSI6InB1YmxpY2F0aW9uIiwicGFnZSI6InB1YmxpY2F0aW9uIn19

8: Beyond RSS: Towards Intelligent Dynamic Memory Management (Work in Progress)
Christos Panagiotis Lamprakos, Sotirios Xydis, Peter Kourzanov, Manu Perumkunnil, Francky Catthoor, Dimitrios Soudris
https://dl.acm.org/doi/10.1145/3617651.3622989
Note: metric used is roughly `{sum of free space} / {size of memory available to the program}`. Intended for modern systems with virtual memory, paging.

data collected using mtrace_malloc \(https://github.com/racoltdev/malloc/tree/master\)

