from MemoryModel import MemorySnapshot

def alloc_verify_1page(start, end, width=64):
	alloc_dist = end - start + 1
	expected_val = (2 ** alloc_dist) - 1
	expected_val = expected_val << (width - 1 - end)
	expected_dict = {0: expected_val}
	return expected_dict

def test_1depth_1page():
	m = MemorySnapshot()
	start, end = 10, 15
	assert m.malloc(start, end)
	expected = alloc_verify_1page(start, end)
	assert m.pages == expected

def test_2depth_1page():
	m = MemorySnapshot(max_depth=2)
	start, end = 10, 15
	assert m.malloc(start, end)
	expected = {0: alloc_verify_1page(start, end)}
	assert m.pages == expected

def test_1depth_noCol_below():
	m = MemorySnapshot()
	start, end = 8, 15
	assert m.malloc(10, 15)
	assert m.malloc(8, 9)
	expected = alloc_verify_1page(start, end)
	assert m.pages == expected

def test_2depth_noCol_below():
	m = MemorySnapshot(max_depth=2)
	start, end = 8, 15
	assert m.malloc(10, 15)
	assert m.malloc(8, 9)
	expected = {0: alloc_verify_1page(start, end)}
	assert m.pages == expected

def test_1depth_col_below():
	m = MemorySnapshot()
	start, end = 7, 15
	assert m.malloc(8, 15)
	assert m.malloc(7, 8) == False
	expected = alloc_verify_1page(start, end)
	assert m.pages == expected
	assert m.malloc(6, 8) == False
	expected = alloc_verify_1page(start - 1, end)
	assert m.pages == expected

def test_2depth_col_below():
	m = MemorySnapshot(max_depth=2)
	start, end = 7, 15
	assert m.malloc(8, 15)
	assert m.malloc(7, 8) == False
	expected = {0: alloc_verify_1page(start, end)}
	assert m.pages == expected
	assert m.malloc(6, 8) == False
	expected = {0: alloc_verify_1page(start - 1, end)}
	assert m.pages == expected

def test_1depth_noCol_above():
	m = MemorySnapshot()
	start, end = 15, 18
	assert m.malloc(15, 16)
	assert m.malloc(17, 18)
	expected = alloc_verify_1page(start, end)
	assert m.pages == expected

def test_2depth_noCol_above():
	m = MemorySnapshot(max_depth=2)
	start, end = 15, 18
	assert m.malloc(15, 16)
	assert m.malloc(17, 18)
	expected = {0: alloc_verify_1page(start, end)}
	assert m.pages == expected

def test_1depth_col_above():
	m = MemorySnapshot()
	start, end = 10, 16
	assert m.malloc(10, 15)
	assert m.malloc(15, 16) == False
	expected = alloc_verify_1page(start, end)
	assert m.pages == expected
	assert m.malloc(15, 17) == False
	expected = alloc_verify_1page(start, end + 1)
	assert m.pages == expected

def test_2depth_col_above():
	m = MemorySnapshot(max_depth=2)
	start, end = 10, 16
	assert m.malloc(10, 15)
	assert m.malloc(15, 16) == False
	expected = {0: alloc_verify_1page(start, end)}
	assert m.pages == expected
	assert m.malloc(15, 17) == False
	expected = {0: alloc_verify_1page(start, end + 1)}
	assert m.pages == expected

def test_1depth_noCol_multipage():
	m = MemorySnapshot()
	start, end = 10, 15
	assert m.malloc(10, 15)
	expected = alloc_verify_1page(start, end)
	expected[0] += 1
	expected[64] = 1 << 63
	assert m.malloc(63, 64)
	assert m.pages == expected

def test_2depth_noCol_multipage():
	m = MemorySnapshot(max_depth=2)
	start, end = 10, 15
	assert m.malloc(10, 15)
	expected = {0: alloc_verify_1page(start, end)}
	expected[0][0] += 1
	expected[0][64] = 1 << 63
	assert m.malloc(63, 64)
	assert m.pages == expected

def test_1depth_col_multipage():
	m = MemorySnapshot()
	start, end = 10, 15
	assert m.malloc(10, 15)
	assert m.malloc(63, 64)
	assert m.malloc(63, 128) == False
	expected = alloc_verify_1page(start, end)
	expected[0] += 1
	expected[64] = (1 << 64) - 1
	expected[128] = 1 << 63
	assert m.pages == expected

def test_2depth_col_multipage():
	m = MemorySnapshot(max_depth=2)
	start, end = 10, 15
	assert m.malloc(10, 15)
	assert m.malloc(63, 64)
	assert m.malloc(63, 128) == False
	expected = {0: alloc_verify_1page(start, end)}
	expected[0][0] += 1
	expected[0][64] = (1 << 64) - 1
	expected[0][128] = 1 << 63
	assert m.pages == expected

def test_2depth_noCol_multiHighLevelPage():
	m = MemorySnapshot(max_depth=2)
	start, end = 63, 128
	assert m.malloc(start, end)
	expected = {0: {0: 1}}
	expected[0][64] = (1 << 64) - 1
	expected[0][128] = 1 << 63
	assert m.pages == expected
	start, end = 4030, 4096
	assert m.malloc(start, end)
	expected[0][3968] = 3
	expected[0][4032] = (1 << 64) - 1
	expected[4096] = {4096: 1 << 63}
	assert m.pages == expected
