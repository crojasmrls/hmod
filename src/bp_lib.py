class BimodalPredictor:
    def __init__(self):
        self.bipc = {}
        self.pht = {}
        self.btb = {}

    def read_entry(self, tag, index):
        try:
            target = self.btb[index]
        except KeyError:
            return False, None
        return self.branch_take(tag, index), target

    def branch_take(self, tag, index):
        confidence = self.pht[index]
        return confidence >= 2 and tag == self.bipc[index]

    def write_entry(self, tag, index, hit, target):
        self.bipc[index] = tag
        self.btb[index] = target
        try:
            confidence = self.pht[index]
        except KeyError:
            if hit:
                self.pht[index] = 0
            else:
                self.pht[index] = 1
        else:
            if hit:
                if confidence < 2:
                    self.pht[index] = max(confidence - 1, 0)
                else:
                    self.pht[index] = min(confidence + 1, 3)
            else:
                if confidence < 2:
                    self.pht[index] = confidence + 1
                else:
                    self.pht[index] = confidence - 1
