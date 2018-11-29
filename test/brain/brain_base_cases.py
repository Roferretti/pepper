from pepper.brain.long_term_memory import LongTermMemory
from pepper.brain.utils.base_cases import statements

from pepper.brain.utils.helper_functions import phrase_update, phrase_cardinality_conflicts, phrase_negation_conflicts, \
    phrase_statement_novelty, phrase_type_novelty, phrase_subject_gaps, phrase_object_gaps


# Create brain connection
brain = LongTermMemory()

for elem in statements:
    x = brain.update(elem)

    print(elem['subject']['label'], elem['predicate']['type'], elem['object']['label'])
    print(phrase_cardinality_conflicts(x['cardinality_conflicts'], elem))
    print(phrase_negation_conflicts(x['negation_conflicts'], elem))
    print(phrase_statement_novelty(x['statement_novelty']))
    print(phrase_type_novelty(x['entity_novelty'], elem))
    print(phrase_subject_gaps(x['subject_gaps'], elem))
    print(phrase_object_gaps(x['object_gaps'], elem))
    print('\t\t\tFINAL SAY: '+phrase_update(x, proactive=True, persist=True))








