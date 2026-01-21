import numpy

# can verify memory with a chunk based bit map. Each range of memory addresses has a unique
# bit map, and each bit represents one byte. Each chunk 64 bits. Can make multilayered if needed.
# query with an address, address converted to chunk address like memalign, chunk addr looked up
# in a sparse structure like a dict, bit wise compare mapped addresses vs addresses about to be mapped.
#
# This also produces a pre-sorted data structure. Any serious implementation should do this.
#
# With some intelligence, this could even model the actual paging system used when the trace was collected.
class MemorySnapshot:
	_SYSTEM_PTR_SIZE = numpy.uintp().itemsize

	def __init__(self, max_depth=1, page_size=(8 * _SYSTEM_PTR_SIZE), verify=True):
		if max_depth < 1:
			raise ValueError(f"max_depth of {type(self).__name__} cannot be less than 1")
		if page_size < 2:
			raise ValueError(f"page_size of {type(self).__name__} cannot be less than 2")

		self.VERIFY = verify
		self.max_depth = max_depth
		self.page_size = page_size
		self.pages = {}
		self.alloc_blocks = {}

	def total_page_bytes(self, depth):
		return self.page_size ** (self.max_depth - depth)

	def align_to_page(self, address, depth):
		page_addr = address - (address % self.total_page_bytes(depth))
		return page_addr

	def get_page(self, address, max_depth=None):
		if max_depth is None:
			max_depth = self.max_depth

		parent_page = self.pages

		for depth in range(max_depth):
			page_addr = self.align_to_page(address, depth)
			new_page = parent_page.get(page_addr)
			if new_page is None:
				if depth == max_depth - 1:
					new_page = numpy.uintp(0)
				else:
					new_page = {}
			parent_page[page_addr] = new_page
			parent_page = new_page
		return parent_page

	def get_pages_in_range(self, start_address, end_address):
		start_page_address = self.align_to_page(start_address, self.max_depth - 1)
		return [self.get_page(x) for x in range(start_page_address, end_address + 1, self.page_size)]

	def _update_page(self, page, bit_mask, start_address, page_address=None):
		if page_address is None:
			page_address = self.align_to_page(start_address, self.max_depth - 1)

		page |= bit_mask
		parent_page = self.get_page(start_address, max_depth=self.max_depth - 1)
		parent_page[page_address] = page

	# This breaks convention!!!!! range is inclusive, inclusive
	# TODO replace end_address with a length instead so inclusive, exclusive notation is more natural
	def malloc(self, start_address, end_address):
		valid = True
		if self.alloc_blocks.get(start_address) is not None:
			print("[MemoryModel] Warn: Allocation table mangled by double allocation @ {0:#016x}".format(start_address))
		self.alloc_blocks[start_address] = end_address

		if (self.VERIFY):
			pages_to_verify = self.get_pages_in_range(start_address, end_address)

			# can probably make this better with bit shifting, but this works
			start_page = pages_to_verify[0]
			start_page_address = self.align_to_page(start_address, self.max_depth - 1)
			page_begin_offset = start_address - start_page_address
			# bit mask that is 0 until the page_begin_offset bit
			start_bit_mask = numpy.uintp(2 ** (self.page_size - page_begin_offset) - 1)

			end_page_address = self.align_to_page(end_address, self.max_depth - 1)
			page_end_offset = end_address - end_page_address
			# bit mask that is 1 until the page_end_offset bit
			end_bit_mask = ~ numpy.uintp(2 ** (self.page_size - 1 - page_end_offset) - 1)

			if len(pages_to_verify) > 1:
				if start_page & ~start_bit_mask != start_page:
					err = "[MemoryModel] Warn: Double allocation in range {0:#016x}, {1:#016x}"
					print(err.format(int(start_address), start_page_address + self.page_size))
					valid = False

				self._update_page(start_page, start_bit_mask, start_address, start_page_address)

				end_page = pages_to_verify[-1]
				if end_page & ~end_bit_mask != end_page:
					err = "[MemoryModel] Warn: Double allocation in range {0:#016x}, {1:#016x}"
					print(err.format(int(end_address), end_page_address + self.page_size))
					valid = False

				self._update_page(end_page, end_bit_mask, end_address, end_page_address)

				for i, p in enumerate(pages_to_verify[1:-1]):
					uintp_max = numpy.iinfo(numpy.uintp()).max
					bitmask = numpy.uintp(uintp_max)
					addr_offset = (i + 1) * self.page_size
					range_start = start_page_address + addr_offset
					if p & ~bitmask != p:
						err = "[MemoryModel] Warn: Double allocation in range {0:#016x}, {1:#016x}"
						err_range_end = range_start + self.page_size - 1
						print(err.format(range_start, err_range_end))
						valid = False

					self._update_page(p, bitmask, range_start, range_start)

			else:
				bit_mask = start_bit_mask & end_bit_mask
				if start_page & ~bit_mask != start_page:
					err = "[MemoryModel] Warn: Double allocation in range {0:#016x}, {1:#016x}"
					print(err.format(int(start_address), int(end_address)))
					valid = False

				self._update_page(start_page, bit_mask, start_address, start_page_address)

		return valid
