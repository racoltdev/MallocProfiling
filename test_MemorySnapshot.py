from MemoryModel import MemorySnapshot

def alloc_verify_1page(start, length, width=64):
	end = start + length - 1
	expected_val = (2 ** length) - 1
	expected_val = expected_val << (width - 1 - end)
	expected_dict = {0: expected_val}
	return expected_dict

def test_1depth_1page():
	m = MemorySnapshot()
	start, length = 10, 6
	assert m.malloc(start, length)
	expected = alloc_verify_1page(start, length)
	assert m.pages == expected

def test_2depth_1page():
	m = MemorySnapshot(max_depth=2)
	start, length = 10, 6
	assert m.malloc(start, length)
	expected = {0: alloc_verify_1page(start, length)}
	assert m.pages == expected

def test_1depth_noCol_below():
	m = MemorySnapshot()
	start, end = 8, 15
	start, length = 8, 8
	assert m.malloc(10, 6)
	assert m.malloc(8, 2)
	expected = alloc_verify_1page(start, length)
	assert m.pages == expected

def test_2depth_noCol_below():
	m = MemorySnapshot(max_depth=2)
	start, length = 8, 8
	assert m.malloc(10, 6)
	assert m.malloc(8, 2)
	expected = {0: alloc_verify_1page(start, length)}
	assert m.pages == expected

def test_1depth_col_below():
	m = MemorySnapshot()
	start, length = 7, 9
	assert m.malloc(8, 8)
	assert m.malloc(7, 2) == False
	expected = alloc_verify_1page(start, length)
	assert m.pages == expected
	assert m.malloc(6, 3) == False
	expected = alloc_verify_1page(start - 1, length + 1)
	assert m.pages == expected

def test_2depth_col_below():
	m = MemorySnapshot(max_depth=2)
	start, length = 7, 9
	assert m.malloc(8, 8)
	assert m.malloc(7, 2) == False
	expected = {0: alloc_verify_1page(start, length)}
	assert m.pages == expected
	assert m.malloc(6, 3) == False
	expected = {0: alloc_verify_1page(start - 1, length + 1)}
	assert m.pages == expected

def test_1depth_noCol_above():
	m = MemorySnapshot()
	start, length = 15, 4
	assert m.malloc(15, 2)
	assert m.malloc(17, 2)
	expected = alloc_verify_1page(start, length)
	assert m.pages == expected

def test_2depth_noCol_above():
	m = MemorySnapshot(max_depth=2)
	start, length = 15, 4
	assert m.malloc(15, 2)
	assert m.malloc(17, 2)
	expected = {0: alloc_verify_1page(start, length)}
	assert m.pages == expected

def test_1depth_col_above():
	m = MemorySnapshot()
	start, length = 10, 7
	assert m.malloc(10, 6)
	assert m.malloc(15, 2) == False
	expected = alloc_verify_1page(start, length)
	assert m.pages == expected
	assert m.malloc(15, 3) == False
	expected = alloc_verify_1page(start, length + 1)
	assert m.pages == expected

def test_2depth_col_above():
	m = MemorySnapshot(max_depth=2)
	start, length = 10, 7
	assert m.malloc(10, 6)
	assert m.malloc(15, 2) == False
	expected = {0: alloc_verify_1page(start, length)}
	assert m.pages == expected
	assert m.malloc(15, 3) == False
	expected = {0: alloc_verify_1page(start, length + 1)}
	assert m.pages == expected

def test_1depth_noCol_multipage():
	m = MemorySnapshot()
	start, length = 10, 6
	assert m.malloc(start, length)
	expected = alloc_verify_1page(start, length)
	expected[0] += 1
	expected[64] = 1 << 63
	assert m.malloc(63, 2)
	assert m.pages == expected

def test_2depth_noCol_multipage():
	m = MemorySnapshot(max_depth=2)
	start, length = 10, 6
	assert m.malloc(start, length)
	expected = {0: alloc_verify_1page(start, length)}
	expected[0][0] += 1
	expected[0][64] = 1 << 63
	assert m.malloc(63, 2)
	assert m.pages == expected

def test_1depth_col_multipage():
	m = MemorySnapshot()
	start, length = 10, 6
	assert m.malloc(start, length)
	assert m.malloc(63, 2)
	assert m.malloc(63, 128 - 63 + 1) == False
	expected = alloc_verify_1page(start, length)
	expected[0] += 1
	expected[64] = (1 << 64) - 1
	expected[128] = 1 << 63
	assert m.pages == expected

def test_2depth_col_multipage():
	m = MemorySnapshot(max_depth=2)
	start, length = 10, 6
	assert m.malloc(start, length)
	assert m.malloc(63, 64)
	assert m.malloc(63, 128 - 63 + 1) == False
	expected = {0: alloc_verify_1page(start, length)}
	expected[0][0] += 1
	expected[0][64] = (1 << 64) - 1
	expected[0][128] = 1 << 63
	assert m.pages == expected

def test_2depth_noCol_multiHighLevelPage():
	m = MemorySnapshot(max_depth=2)
	start, length = 63, 128 - 63 + 1
	assert m.malloc(start, length)
	expected = {0: {0: 1}}
	expected[0][64] = (1 << 64) - 1
	expected[0][128] = 1 << 63
	assert m.pages == expected
	start, length = 4030, 4096 - 4030 + 1
	assert m.malloc(start, length)
	expected[0][3968] = 3
	expected[0][4032] = (1 << 64) - 1
	expected[4096] = {4096: 1 << 63}
	assert m.pages == expected
