from printer import printer

import numpy

# A sparse and efficient structure for modeling memory usage at a given point in time and verifying
# there is no overlap between allocated blocks.
# Supports multilevel paging to partially model realistic memory structures. Could be modified in the future
# to emulate more features of real memory.
class MemorySnapshot:
	_SYSTEM_PTR_SIZE = numpy.uintp().itemsize

	# TODO page_size other than 64 doesn't work
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
		self.events = 0

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

	def _malloc_update_page(self, page, bit_mask, start_address, page_address=None):
		if page_address is None:
			page_address = self.align_to_page(start_address, self.max_depth - 1)

		page |= bit_mask
		parent_page = self.get_page(start_address, max_depth=self.max_depth - 1)
		parent_page[page_address] = page

	def malloc(self, start_address, length):
		self.events += 1
		valid = True
		end_address = start_address + length - 1

		if self.alloc_blocks.get(start_address) is not None:
			print("[MemoryModel] Warn: Allocation table mangled by double allocation @ {0:#016x}".format(start_address))
		self.alloc_blocks[start_address] = length

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
					printer(err.format(int(start_address), start_page_address + self.page_size))
					valid = False

				self._malloc_update_page(start_page, start_bit_mask, start_address, start_page_address)

				end_page = pages_to_verify[-1]
				if end_page & ~end_bit_mask != end_page:
					err = "[MemoryModel] Warn: Double allocation in range {0:#016x}, {1:#016x}"
					printer(err.format(int(end_address), end_page_address + self.page_size))
					valid = False

				self._malloc_update_page(end_page, end_bit_mask, end_address, end_page_address)

				for i, p in enumerate(pages_to_verify[1:-1]):
					uintp_max = numpy.iinfo(numpy.uintp()).max
					bitmask = numpy.uintp(uintp_max)
					addr_offset = (i + 1) * self.page_size
					range_start = start_page_address + addr_offset
					if p & ~bitmask != p:
						err = "[MemoryModel] Warn: Double allocation in range {0:#016x}, {1:#016x}"
						err_range_end = range_start + self.page_size - 1
						printer(err.format(range_start, err_range_end))
						valid = False

					self._malloc_update_page(p, bitmask, range_start, range_start)

			else:
				bit_mask = start_bit_mask & end_bit_mask
				if start_page & ~bit_mask != start_page:
					err = "[MemoryModel] Warn: Double allocation in range {0:#016x}, {1:#016x}"
					printer(err.format(int(start_address), int(end_address)))
					valid = False

				self._malloc_update_page(start_page, bit_mask, start_address, start_page_address)

		return valid

	def _free_update_page(self, page, bitmask, start_address, page_address=None):
		if page_address is None:
			page_address = self.align_to_page(start_address, self.max_depth - 1)

		page &= bitmask
		parent_page = self.get_page(start_address, max_depth=self.max_depth - 1)
		if page == 0:
			del parent_page[page_address]
		else:
			parent_page[page_address] = page

	# if free(1), and some allocation exists starting @2, this will not remove the record from alloc_blocks
	# even if the length of the allocation @1 is greater than 1
	def free(self, start_address):
		self.events += 1
		valid = True
		length = self.alloc_blocks.get(start_address)

		# No allocation here, no work to be done
		if length is None:
			printer("[MemoryModel] Warn: Attempting to free an unallocated block @ {0:#016x}".format(start_address))
			return

		del self.alloc_blocks[start_address]
		end_address = start_address + length - 1

		if (self.VERIFY):
			pages_to_verify = self.get_pages_in_range(start_address, end_address)

			start_page = pages_to_verify[0]
			start_page_address = self.align_to_page(start_address, self.max_depth - 1)
			page_begin_offset = start_address - start_page_address
			# bit mask that is 1 until the page_begin_offset bit
			start_bit_mask = ~ numpy.uintp(2 ** (self.page_size - page_begin_offset) - 1)

			end_page_address = self.align_to_page(end_address, self.max_depth - 1)
			page_end_offset = end_address - end_page_address
			# bit mask that is 0 until the page_end_offset bit
			end_bit_mask = numpy.uintp(2 ** (self.page_size - 1 - page_end_offset) - 1)

			if len(pages_to_verify) > 1:
				if start_page | ~start_bit_mask != start_page:
					err = "[MemoryModel] Warn: Double allocation in range {0:#016x}, {1:#016x}"
					printer(err.format(int(start_address), start_page_address + self.page_size))
					valid = False

				self._free_update_page(start_page, start_bit_mask, start_address, start_page_address)

				end_page = pages_to_verify[-1]
				if end_page | ~end_bit_mask != end_page:
					err = "[MemoryModel] Warn: Double allocation in range {0:#016x}, {1:#016x}"
					printer(err.format(int(end_address), end_page_address + self.page_size))
					valid = False

				self._free_update_page(end_page, end_bit_mask, end_address, end_page_address)

				for i, p in enumerate(pages_to_verify[1:-1]):
					uintp_max = numpy.iinfo(numpy.uintp()).max
					bitmask = numpy.uintp(0)
					addr_offset = (i + 1) * self.page_size
					range_start = start_page_address + addr_offset
					if p | ~bitmask != p:
						err = "[MemoryModel] Warn: Double allocation in range {0:#016x}, {1:#016x}"
						err_range_end = range_start + self.page_size - 1
						printer(err.format(range_start, err_range_end))
						valid = False

					self._free_update_page(p, bitmask, range_start, range_start)

			else:
				bit_mask = start_bit_mask | end_bit_mask
				if start_page | ~bit_mask != start_page:
					err = "[MemoryModel] Warn: Double allocation in range {0:#016x}, {1:#016x}"
					printer(err.format(int(start_address), int(end_address)))
					valid = False

				self._free_update_page(start_page, bit_mask, start_address, start_page_address)

		return valid

	def print_dump(self):
		keys = list(self.alloc_blocks.keys())
		end = self.alloc_blocks.get(keys[-1]) + keys[-1]
		print([numpy.binary_repr(x, width=64) for x in self.get_pages_in_range(keys[0], end)])

# Event is a single value representing one point in time - ie a snapshot
# lifetime_analysis generates lifetime range overlap data, a snapshot cannot do that
def objects_to_snapshot(MemoryObjects, event=4):
	memory_snapshot = MemorySnapshot()
	sort_by_init = sorted(MemoryObjects.values(), key=lambda x: x.alloc_time)

	# TODO every allocated object should have size. Double check this

	for mem_object in sort_by_init:
		# Construct snapshot of memory at allocation event# "event"
		end_in_range = True if mem_object.dealloc_time is None else mem_object.dealloc_time > event

		if mem_object.alloc_time <= event and end_in_range:
			start_address = mem_object.address
			# Ignore any validation errors for now. Notifying in console is good enough
			memory_snapshot.malloc(start_address, mem_object.size)

	# no more allocations will occur. allocation list can be sorted and the memory model can be discarded
	# sort by location in memory
	memory_snapshot.alloc_blocks = dict(sorted(memory_snapshot.alloc_blocks.items()))

	return memory_snapshot
