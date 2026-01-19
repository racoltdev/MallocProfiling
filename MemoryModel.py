import numpy

# can verify memory with a chunk based bit map. Each range of memory addresses has a unique
# bit map, and each bit represents one byte. Each chunk 63 bits. Can make multilayered if needed.
# query with an address, address converted to chunk address like memalign, chunk addr looked up
# in a sparse structure like a dict, bit wise compare mapped addresses vs addresses about to be mapped.
#
# This also produces a pre-sorted data structure. Any serious implementation should do this.
#
# With some intelligence, this could even model the actual paging system used when the trace was collected.
class MemorySnapshot:
	_system_ptr_size = numpy.uintp().itemsize

	def __init__(self, max_depth=1, page_size=(8 * _system_ptr_size), verify=True):
		if max_depth < 1:
			raise ValueError(f"max_depth of {type(self).__name__} cannot be less than 1")
		if page_size < 2:
			raise ValueError(f"page_size of {type(self).__name__} cannot be less than 2")

		self.VERIFY = verify
		self.max_depth = max_depth
		self.page_size = page_size
		self.pages = {}
		self.blocks = {}

	def total_page_bytes(self, depth):
		return self.page_size ** (self.max_depth - depth)

	def align_to_page(self, address, depth):
		page_addr = address - (address % self.total_page_bytes(depth))
		print(self.total_page_bytes(depth))
		return page_addr

	def get_page(self, address, max_depth=None):
		if max_depth is None:
			max_depth = self.max_depth

		page = self.pages
		for depth in range(max_depth):
			page_addr = self.align_to_page(address, depth)
			new_page = page.get(page_addr, {})
			if new_page == {}:
				page[page_addr] = new_page
			page = new_page
		return page

	def malloc(self, start_address, end_address):
		if (self.VERIFY):
			start_page = self.pages
			end_page = self.pages
			start_page_addr, end_page_addr = 0, 0
			nearest_shared_parent = self.pages
			pages_to_verify = [self.pages]
			depth = 0

			while True:
				pass
				#for page in pages_to_verify:
				#	

				#total_page_bytes = self.total_page_bytes(depth)
				#pages_to_verify = [x for x in range(start_page_addr, end_page_addr + 1, total_page_bytes)]


			for depth in range(0, self.max_depth):
				start_page_addr = self.align_to_page(start_address, depth)
				print(start_page_addr)
				start_page = start_page.get(start_page_addr, {})

				end_page_addr = self.align_to_page(end_address, depth)
				print(end_page_addr)
				end_page = end_page.get(end_page_addr, {})

				total_page_bytes = self.total_page_bytes(depth)
				pages_to_verify = [x for x in range(start_page_addr, end_page_addr + 1, total_page_bytes)]

				print(pages_to_verify)

	# If python doesn't check a list is sorted before sorting, this can be optimized
