from ckonlpy.utils import installpath
from ckonlpy.utils import loadtxt
from ._evaluator import SimpleEvaluator
from pprint import pprint

class SimpleTemplateTagger:

    def __init__(self, dictionary, templates=None, evaluator=None, tagset=None):

        if not evaluator:
            evaluator = SimpleEvaluator(tagset=tagset)

        if not tagset:
            tagset = {}

        self.dictionary = dictionary
        self.templates = _initialize_templates(templates, dictionary, tagset)
        self.evaluator = evaluator
        self.debug = False

    def pos(self, eojeol, perfect_match=True):

        if not eojeol:
            return []

        n = len(eojeol)
        wordpos_nested_list = _match_words(eojeol, self.dictionary)
        matcheds = _match_templates(wordpos_nested_list, self.templates, self.debug)
        if perfect_match:
            matcheds = [matched for matched in matcheds
                if ((matched[0][2] == 0) and (matched[-1][3] == n))]
        if not matcheds:
            return []
        matcheds = self.evaluator.select(matcheds)
        words = _append_unmatched(matcheds, eojeol)
        return words

    def add_a_template(self, a_template):
        if type(a_template) != tuple:
            a_template = tuple(a_template)
        if (a_template in self.templates) == False:
            self.templates.append(a_template)

    def set_evaluator(self, my_weight_tuple, my_evaluate_function, test=True):
        self.evaluator.weight = my_weight_tuple
        self.evaluator.evaluate = my_evaluate_function

        if not test:
            return

        for test_candidate in test_candidates:
            print('candidate')
            pprint(test_candidate)
            print('score = {}\n'.format(self.evaluator.evaluate(test_candidate)))

"""
test_candidates = [
    [('DB손보', 'Nic', 0, 4), ('윤경민', 'Name', 4, 7)],
    [('DB', 'Alpha', 0, 2), ('손보', 'Noun', 2, 4), ('윤경민', 'Name', 4, 7)],
    [('DB', 'Alpha', 0, 2), ('손보', 'Noun', 2, 4), ('윤', 'Noun', 4, 5), ('경민', 'Noun', 5, 7)],
    [('DB손보', 'Nic', 0, 4), ('윤', 'Noun', 4, 5), ('경민', 'Noun', 5, 7),]
]
"""
"""
test_candidates = [
    [('김윤호', 'Name', 0, 4)],
    [('김윤호', 'Norm', 0, 4)],
    [('김', 'Norm', 0, 1),('윤호', 'Name', 1, 4)],
    [('김', 'Norm', 0, 1),('윤호', 'Norm', 1, 4)],
]
"""
test_candidates = [
    [('국민', 'Nic', 0, 2),('최승언', 'Name', 2, 5)],
    [('국민', 'Nic', 0, 2),('최승언', 'Norm', 2, 5)],
    [('국민', 'Norm', 0, 2),('최승언', 'Norm', 2, 5)],
    [('국민', 'Norm', 0, 2),('최승언', 'Name', 2, 5)],
    [('주식', 'Norm', 0, 2),('회사', 'Norm', 2, 4),('닉컴퍼니', 'Norm', 4, 8)],
    [('주식회사', 'Nic', 0, 4),('닉컴퍼니', 'Norm', 4, 8)],
    [('배민', 'Norm', 0, 2),('페이', 'Norm', 2, 4),('머니', 'Norm', 4, 6)],
    [('배민', 'Norm', 0, 2),('페이머니', 'Nic', 2, 6)],
]



def _initialize_templates(templates, dictionary, tagset):
    if not templates:
        templatespath = '%s/data/templates/twitter_templates0' % installpath
        templates = loadtxt(templatespath)
        templates = [tuple(template.split()) for template in templates]

    single_words = [(pos, ) for pos in dictionary._pos2words
                    if not (pos in tagset)]
    templates += [template for template in single_words
                  if not template in templates]

    return templates

def _match_words(eojeol, dictionary):
    n = len(eojeol)

    matched = []
    for b in range(n):
        sublist = []
        for e in range(b+1, min(n, b + dictionary._max_length) + 1):
            word = eojeol[b:e]
            for tag in dictionary.get_tags(word):
                sublist.append((word, tag, b, e))
        matched.append(sublist)
    return matched

def _match_templates(wordpos_nested_list, templates, debug=False):

    n = len(wordpos_nested_list)
    matcheds = []

    # for each begin position
    for wordpos_list in wordpos_nested_list:
        # for each (word, pos, begin, end)
        for wordpos in wordpos_list:
            # for each template
            for template in templates:
                if template[0] == wordpos[1]:
                    # skip a syllable single word
                    if len(template) == 1 and len(wordpos[0]) == 1:
                        continue
                    expandeds = _expand(
                        wordpos, template, wordpos_nested_list, n, debug)
                    matcheds += expandeds

    return matcheds

def _expand(wordpos, template, wordpos_nested_list, n, debug):

    def get_matched_wordpos(wordpos_list, tag):
        return [wordpos for wordpos in wordpos_list if wordpos[1] == tag]

    # Initialize candidates
    candidates = [[wordpos]]

    # Expansion
    for match_tag in template[1:]:
        candidates_ = []
        for candidate in candidates:
            last_index = candidate[-1][3]
            if last_index >= n:
                continue
            expandables = get_matched_wordpos(
                wordpos_nested_list[last_index], match_tag)
            for expandable in expandables:
                expanded = [c for c in candidate] + [expandable]
                candidates_.append(expanded)
        candidates = candidates_

    if debug and candidates:
        print('\ntemplate = {}'.format(template))
        for candidate in candidates:
            print(candidate)

    return candidates

def _append_unmatched(matcheds, eojeol):

    n = len(eojeol)
    words = [word for match, _, _, _ in matcheds for word in match]
    if not words:
        return [(eojeol, None, 0, n)]

    begin = 0
    unmatcheds = []
    for word in words:
        if begin == word[2]:
            begin = word[3]
            continue
        unmatcheds.append((eojeol[begin:word[2]], None, begin, word[2]))
        begin = word[3]
    if begin < n:
        unmatcheds.append((eojeol[begin:], None, begin, n))

    words += unmatcheds
    words = sorted(words, key=lambda x:x[2])
    return words