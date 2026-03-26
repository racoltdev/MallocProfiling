import printer

import pickle
import os
from typing import Dict

class CacheItem:
	def __init__(self, usage_hash):
		self.usage_hash = usage_hash

	def pre_pickle(self):
		pass

	def post_pickle(self):
		pass

class _PickleTag:
	def __init__(self, seek_pos, usage_hash):
		self.seek_pos = seek_pos
		self.usage_hash = usage_hash

class Cache:
	def __init__(self, cache_file):
		self._main_cache : Dict[str, CacheItem] = {}
		self._stale_cache : Dict[str, CacheItem] = {}
		self._pickled_cache : Dict[str, _PickleTag] = {}
		self._cache_file = cache_file
		self._cachef = open(cache_file, "w+b")

	def _unpickle(self, key, pickle_tag, mutate=True):
		self._cachef.seek(pickle_tag.seek_pos)
		pickled_item = pickle.load(self._cachef)
		pickled_item.post_pickle()

		if mutate:
			self._main_cache[key] = pickled_item
			del self._pickled_cache[key]

		self._cachef.seek(0, 2)
		return pickled_item

	def get(self, key, usage_hash):
		cached_usage = None

		if key in self._main_cache:
			cache_item = self._main_cache[key]
			cached_usage = cache_item.usage_hash
			# stale, stage for pickling
			if cached_usage == usage_hash:
				self._stale_cache[key] = self._main_cache[key]
				del self._main_cache[key]
			# cache hit
			else:
				return self._main_cache[key]

		elif key in self._stale_cache:
			cache_item = self._stale_cache[key]
			cached_usage = cache_item.usage_hash
			# double stale, move to pickle
			if cached_usage == usage_hash:
				cache_item.pre_pickle()
				self._pickled_cache[key] = _PickleTag(self._cachef.tell(), cache_item.usage_hash)
				pickle.dump(cache_item, self._cachef)
				del self._stale_cache[key]
			# cache hit. no longer stale, recover to main cache
			else:
				self._main_cache[key] = cache_item
				del self._stale_cache[key]
				return cache_item

		elif key in self._pickled_cache:
			pickle_tag = self._pickled_cache[key]
			cached_usage = pickle_tag.usage_hash

			# cache hit. no longer stale, recover to main cache
			if cached_usage != usage_hash:
				return self._unpickle(key, pickle_tag)

		return cached_usage # None if does not exist in cache

	# Warn! Do not update() stale items!
	def update(self, key, cache_item):
		# this assumes update will only be called on items that have been retrieved by self.get
		# and determined to be not stale, or items that don't yet exist in the cache
		self._main_cache[key] = cache_item

	def all(self):
		for key, item in self._main_cache.items():
			yield (key, item)

		toprint = True
		for key, item in self._stale_cache.items():
			if toprint:
				printer.printer(f"stale pids:")
				toprint = False
			yield (key, item)

		toprint = True
		for key, pickle_tag in self._pickled_cache.items():
			if toprint:
				printer.printer(f"pickled pids:")
				toprint = False
			yield (key, self._unpickle(key, pickle_tag, mutate=False))

	def open_cache_file(self):
		self._cachef = open(self._cache_file, "w+b")

	def close_cache_file(self, destroy=False):
		self._cachef.close()
		if destroy:
			os.remove(self._cache_file)
