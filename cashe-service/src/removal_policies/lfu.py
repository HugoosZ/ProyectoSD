class LFUCache:
    def __init__(self, capacity=100):
        self.data = {}
        self.freq = {}
        self.capacity = capacity

    def get(self, key):
        if key not in self.data:
            return None
        self.freq[key] += 1
        return self.data[key]

    def set(self, key, value):
        if len(self.data) >= self.capacity and key not in self.data:
            lfu_key = min(self.freq, key=lambda k: self.freq[k])
            self.data.pop(lfu_key)
            self.freq.pop(lfu_key)

        self.data[key] = value
        self.freq[key] = self.freq.get(key, 0) + 1