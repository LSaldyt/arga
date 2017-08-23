import json
from collections import defaultdict, namedtuple
from itertools   import zip_longest
from pprint      import pprint

from utils import flatten

from variable_dictionary import VariableDictionary

class ConceptMap(object):
    def __init__(self, filename):
        self.concepts = defaultdict(dict)
        with open(filename, 'r') as infile:
            self.concepts.update(json.load(infile))

    def __str__(self):
        return str(self.concepts)

    def shared_keys(self, *items):
        def get_keys (item):
            return set(self.concepts[item].keys())
        return set.intersection(*(get_keys(item) for item in items))

    def process_value(self, value):
        if isinstance(value, str):
            value = [value]
        elif isinstance(value, dict):
            raise NotImplementedError('Dictionary relations are more complex and not currently supported')
        return value

    def level_key_values(self, concept):
        def recursive_key_values(d):
            if isinstance(d, dict):
                # [[[..]]] potentially infinitely nested lists
                nested = [recursive_key_values(item) for item in d.values()]
                return [list(sorted(d.items(), key=lambda t:t[0]))] + [list(item) for item in zip(*flatten(nested))]
            else:
                return []
        return [[(concept, self.concepts[concept])]] + recursive_key_values(self.concepts[concept])

    def level_keys(self, concept):
        return [[k for k, v in kvs] for kvs in self.level_key_values(concept)]

    def level_values(self, concept):
        return [[v for k, v in kvs] for kvs in self.level_key_values(concept)]

    def difference(self, a, b):
        kvsA = self.level_key_values(a)
        kvsB = self.level_key_values(b)
        variables = VariableDictionary()
        diff = []
        for A, B in zip_longest(kvsA, kvsB, fillvalue=None):
            process = lambda l : [(k, None if isinstance(v, dict) else v) for k, v in l]
            A = process(A)
            B = process(B)
            aKeys   = {k for k, v in A}
            aValues = {v for k, v in A}
            bKeys   = {k for k, v in B}
            bValues = {v for k, v in B}

            uniqueKeys   = aKeys.symmetric_difference(bKeys)
            uniqueValues = aValues.symmetric_difference(bValues)
            
            print('unique:')
            print(uniqueKeys)
            print(uniqueValues)

            level = []
            for (kA, vA) in A:
                for (kB, vB) in B:
                    if kA == kB and vA == vB:
                        level.append((kA, vA))
                    elif kA == kB:
                        variables.add([vA, vB])
                        v = variables.get_identifier()
                        level.append((kA, v))
                    elif vA == vB:
                        variables.add([kA, kB])
                        v = variables.get_identifier()
                        level.append((v, vA))
                    else:
                        pass
                if kA in uniqueKeys and \
                        vA in uniqueValues:
                    variables.add([(kA, vA)])
                    v = variables.get_identifier()
                    level.append(v)
            diff.append(level)
        return diff, variables
