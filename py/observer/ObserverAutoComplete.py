# Generic Common Database Routines for PyQt5 Framework

from PyQt5.QtCore import pyqtSlot, pyqtProperty, QObject, QVariant
from py.observer.ObserverData import ObserverData
from enum import Enum
import logging
import unittest


class ACDataTypes(Enum):
    none = 0
    observers = 1
    vessels = 2
    fisheries = 3
    captains = 4
    ports = 5
    vessellogbooks = 6
    catch_categories = 7
    trawl_gear_types = 8
    first_receivers = 9
    species = 10
    bs_sample_methods = 11
    fg_gear_types = 12
    avg_soak_times = 13
    # ...


class ACAllowable():
    @property
    def type_names(self):
        return 'observers', 'vessels', 'fisheries', 'captains', \
               'ports', 'vessel_logbooks', 'catch_categories', \
               'trawl_gear_types', 'first_receivers', 'species', \
               'bs_sample_methods', 'fg_gear_types', 'avg_soak_times'


class ObserverAutoComplete(QObject):
    def __init__(self, db):  # requires ObserverData
        super(ObserverAutoComplete, self).__init__()
        self._logger = logging.getLogger(__name__)
        self._suggestions = []  # Returned fresults from search
        self._suggestion_data = []  # Data to choose from
        self._current_loaded_data = ACDataTypes.none  # Only load data once
        self._db = db
        self._full_search = False

    @pyqtProperty(QVariant)
    def suggestions(self):
        return self._suggestions

    @pyqtSlot()
    def clear_suggestions(self):
        self._logger.debug("Suggestions clear")
        self._current_loaded_data = ACDataTypes.none
        self._suggestion_data = []

    @pyqtSlot(int, bool, name='suggestFisheriesByProgID')
    def suggest_fisheries_by_progid(self, program_id, is_fg):
        # special case - needs Program ID
        self._current_loaded_data = ACDataTypes.fisheries
        self._logger.debug("Loading fisheries")
        self._suggestion_data = self._db.get_fisheries_by_program_id(program_id, is_fg)

    @pyqtSlot(int, name='suggestCaptainsByVesselId')
    def suggest_captains_by_vesselid(self, vessel_id):
        # special case - needs Vessel ID
        self._db.captain_vessel_id = vessel_id
        self.suggest('captains')

    @pyqtSlot(str)
    def suggest(self, suggestion):
        # Load Data on demand
        allowable = ACAllowable().type_names
        if suggestion.lower() not in allowable:
            self._logger.warning('Unrecognized suggestion type: ' + suggestion)
        if suggestion.lower() == 'observers':
            self._current_loaded_data = ACDataTypes.observers
            self._logger.debug("Loading observer names")
            self._suggestion_data = self._db.observers
        elif suggestion.lower() == 'vessels':
            self._current_loaded_data = ACDataTypes.vessels
            self._logger.debug("Loading vessel names")
            self._suggestion_data = self._db.vessels
        elif suggestion.lower() == 'ports':
            self._current_loaded_data = ACDataTypes.ports
            self._logger.debug("Loading port names")
            self._suggestion_data = self._db.ports
        elif suggestion.lower() == 'captains':
            self._current_loaded_data = ACDataTypes.captains
            self._logger.debug(f'Loading captains')
            self._suggestion_data = self._db.captains
        elif suggestion.lower() == 'vessel_logbooks':
            self._current_loaded_data = ACDataTypes.vessellogbooks
            self._logger.debug("Loading vessel logbook names")
            self._suggestion_data = self._db.vessel_logbook_names
        elif suggestion.lower() == 'catch_categories':
            self._current_loaded_data = ACDataTypes.catch_categories
            self._logger.debug("Loading catch category codes")
            self._suggestion_data = self._db.catch_categories
        elif suggestion.lower() == 'trawl_gear_types':
            self._current_loaded_data = ACDataTypes.trawl_gear_types
            self._logger.debug("Loading trawl gear types")
            self._suggestion_data = self._db.trawl_gear_types
        elif suggestion.lower() == 'fg_gear_types':
            self._current_loaded_data = ACDataTypes.fg_gear_types
            self._logger.debug("Loading FG gear types")
            self._suggestion_data = self._db.fg_gear_types
        elif suggestion.lower() == 'avg_soak_times':
            self._current_loaded_data = ACDataTypes.avg_soak_times
            self._logger.debug("Loading avg soak times")
            self._suggestion_data = self._db.soaktimes
        elif suggestion.lower() == 'first_receivers':
            self._current_loaded_data = ACDataTypes.first_receivers
            self._logger.debug("Loading first receivers")
            self._suggestion_data = self._db.first_receivers
        elif suggestion.lower() == 'species':
            self._current_loaded_data = ACDataTypes.species
            self._logger.debug("Loading species")
            self._suggestion_data = self._db.species
        elif suggestion.lower() == 'bs_sample_methods':
            self._current_loaded_data = ACDataTypes.bs_sample_methods
            self._logger.debug("Loading BS Sample Methods")
            self._suggestion_data = self._db.bs_sample_methods
        else:  # Unknown type
            self._current_loaded_data = ACDataTypes.none

        # To what lists should common word abbreviations be applied to the suggestion list
        # before display and if applicable, full_search.
        # Note: full space-EOL-delimited word are compared, not substrings.
        abbreviate_types = {ACDataTypes.trawl_gear_types, ACDataTypes.fg_gear_types}
        if self._current_loaded_data in abbreviate_types:
            self._abbreviate_suggestions = True
        else:
            self._abbreviate_suggestions = False

        # Please enumerate anticipated case alternatives of each word.
        # Limitation: only spaces are considered word delimiters:
        # For example, to abbreviate "small" in "trawl (small footrope" , please specify "(small".
        # TODO: Handle case alternatives in code if this enumeration becomes burdensome.
        # WIBNI: A separate dictionary of abbreviations for each ACDataType.
        common_word_abbreviations = {
            'Inches': 'In',
            'inches': 'in',
            'miscellaneous': 'misc',
            'Groundfish': 'GF',
            'small': 'SM',
            '(small': '(SM',
            'large': 'LG',
            '(large': '(LG',
        }

        # Apply the abbreviations to the currently loaded data
        # TODO: Consider applying these abbreviations once, in __init__, to full set of suggestions.
        if self._abbreviate_suggestions:
            self._suggestion_data = ObserverAutoComplete._abbreviate_suggestions(
                    self._suggestion_data, common_word_abbreviations)

        full_search_types = {ACDataTypes.observers,
                             ACDataTypes.first_receivers, ACDataTypes.vessels,
                             ACDataTypes.catch_categories}
        if self._current_loaded_data in full_search_types:
            self._full_search = True  # search beyond a first word match
        else:
            self._full_search = False

        self.search()

    @staticmethod
    def _calculate_when_full_search_kicks_in(n_suggestions):
        """ Full-search on all the words can be time-consuming,
            especially when the user has only typed one or two letters.
            Depending on the number of suggestions, start full-search
            when the user has typed one, two, or three letters.
        """
        FULL_SEARCH_ON_FIRST_LETTER_MAX_SUGGESTIONS = 100
        FULL_SEARCH_ON_SECOND_LETTER_MAX_SUGGESTIONS = 10000 # Enables a full search on all current categories
        if n_suggestions <= FULL_SEARCH_ON_FIRST_LETTER_MAX_SUGGESTIONS:
            return 1
        if n_suggestions <= FULL_SEARCH_ON_SECOND_LETTER_MAX_SUGGESTIONS:
            return 2
        return 3

    @pyqtSlot(QVariant)
    def search(self, partial_str=''):
        self._suggestions = []
        if self._current_loaded_data == ACDataTypes.none:
            return
        self._logger.debug('AutoComplete input: ' + partial_str)

        # Show whole list for short things like fisheries, logbook names, gear types. Even catch categories
        show_whole_list = {ACDataTypes.captains, ACDataTypes.fisheries, ACDataTypes.vessellogbooks,
                           ACDataTypes.trawl_gear_types, ACDataTypes.fg_gear_types, ACDataTypes.bs_sample_methods,
                           ACDataTypes.catch_categories, ACDataTypes.avg_soak_times}
        if self._current_loaded_data not in show_whole_list and partial_str == "":
            self._suggestions = ['']  # or list all
            return

        # Depending on the length of the suggestion list, apply the full-search mode
        # when the partial string is at "long enough" relative to the number of suggestions.
        # Concern addressed: matching single character strings yields too many alternatives
        # with a long suggestion list.
        full_search_min_substr_length = ObserverAutoComplete._calculate_when_full_search_kicks_in(
                len(self._suggestion_data))
        do_full_search = self._full_search and (len(partial_str) >= full_search_min_substr_length)

        # Check for substring match starting at beginning of suggestion.
        # In addition, if full search enabled and substring is long enough (e.g. two characters),
        # check for substring match starting anywhere in suggestion.
        partial_str_lc = partial_str.lower()
        self._suggestions = [
            sug for sug in self._suggestion_data
            if sug.lower().startswith(partial_str_lc) or
                    (do_full_search and sug.lower().find(partial_str_lc) > 0)
        ]

        if self._current_loaded_data == ACDataTypes.captains \
                and len(self._suggestions) == 0 and len(partial_str) == 0:
            self._suggestions.append('No skipper is associated with vessel.\nPlease add name in comments\nand contact Neil Riley to add to DB.')
        self._logger.debug('Suggestion count: ' + str(len(self._suggestions)))

    @staticmethod
    def _apply_abbreviations(line, common_abbreviations):
        """Replace full words in abbreviation dictionary with their abbreviations
            Splits the lines on spaces, so other delimiters are considered parts of a word (e.g. "(small").
            Skips the first word of the line - does not abbreviate - because first word considered a code (key) word.
        """
        line_words = line.split(' ')
        for full_word, abbrev in common_abbreviations.items():
            if full_word in line:
                # Skip first word - it's a key
                for i in range(1, len(line_words)):
                    if line_words[i] == full_word:
                        line_words[i] = abbrev
        line_with_abbrevs = ' '.join(line_words)
        return line_with_abbrevs

    @staticmethod
    def _abbreviate_suggestions(suggestion_list, common_abbreviations):
        abbreviated_suggestion_list = []
        for suggestion in suggestion_list:
            abbreviated_suggestion = ObserverAutoComplete._apply_abbreviations(suggestion, common_abbreviations)
            abbreviated_suggestion_list.append(abbreviated_suggestion)
        return abbreviated_suggestion_list


class TestObserverAutoComplete(unittest.TestCase):
    """
    Test basic autocompletion
    """

    def setUp(self):
        testdata = ObserverData()
        self.ac = ObserverAutoComplete(db=testdata)

    def test_clear(self):
        self.assertIsNotNone(self.ac)
        self.ac.clear_suggestions()
        self.assertEqual(len(self.ac._suggestion_data), 0)

    def test_observers_goodstr(self):
        self.ac.suggest('observers')
        self.ac.search('eric')
        testing = self.ac.suggestions
        self.assertGreaterEqual(len(testing), 9)

        self.ac.search('a')
        testing = self.ac.suggestions
        self.assertGreater(len(testing), 10)

    def test_observers_badstr(self):
        self.ac.suggest('badname')
        self.assertIsNotNone(self.ac)
        self.ac.search('xzx')
        testing = self.ac.suggestions
        self.assertEqual(len(testing), 0)

    def test_full_search_first_two_words(self):
        # Pre-conditions
        assert self.ac is not None

        n_expected_results = 1
        expected_only_result = 'ALBA Albatross Unid'
        self.ac.suggest('catch_categories')
        self.ac.search('ALBA Albatross')
        testing_one_word = self.ac.suggestions
        self.assertEqual(n_expected_results, len(testing_one_word))
        self.assertEqual(expected_only_result, testing_one_word[0])

    def test_full_search_second_and_third_words(self):
        # Pre-conditions
        assert self.ac is not None

        n_expected_results = 1
        expected_only_result = 'ALBA Albatross Unid'
        self.ac.suggest('catch_categories')
        self.ac.search('Albatross Unid') # Skip first word - code "ALBA"
        actual_suggestions = self.ac.suggestions
        self.assertEqual(n_expected_results, len(actual_suggestions))
        self.assertEqual(expected_only_result, actual_suggestions[0])

    def test_full_search_substring_match_in_later_words(self):
        # Pre-conditions
        assert self.ac is not None

        n_expected_results = 7
        expected_first_result = 'Albers Seafoods CRESCENT CITY'
        self.ac.suggest('first_receivers')
        self.ac.search('crescent city') # Skip first two words "Albers' and 'Seafoods'
        actual_suggestions = self.ac.suggestions
        self.assertEqual(n_expected_results, len(actual_suggestions))
        self.assertEqual(expected_first_result, actual_suggestions[0])

    def test_full_search_substring_match_in_large_suggestion_list(self):
        """ The full search of substr in all the suggestion doesn't kick in
            until the user has entered two or three characters. Current limits
            Start full search:
            - on first character if suggestion list is no more than 100 lines.
            - on second character if no more than 10000 lines.
            - on third character for larger lists.

            All current lists are less than 10,000 lines,
            so full-search should kick in after two letters.

            catch_categories has about 222 entries.
            vessels has about 2001 entries.
            Test that match in later words not found until two characters are specified in substring.
        """
        # Pre-conditions
        assert self.ac is not None

        suggestion_expected_only_with_full_search = "BLACKJACK - OR079ADG"
        self.ac.suggest('vessels')

        self.ac.search('O')
        one_letter_suggestions = self.ac.suggestions
        self.assertEqual(52, len(one_letter_suggestions))
        self.assertNotIn(suggestion_expected_only_with_full_search, one_letter_suggestions)

        self.ac.search('OR')
        two_letter_suggestions = self.ac.suggestions
        self.assertEqual(416, len(two_letter_suggestions))
        self.assertIn(suggestion_expected_only_with_full_search, two_letter_suggestions)

        self.ac.search('OR0')
        three_letter_suggestions = self.ac.suggestions
        self.assertEqual(13, len(three_letter_suggestions))
        self.assertIn(suggestion_expected_only_with_full_search, three_letter_suggestions)

    def test_list_first_ten_entries_of_each_suggestion_list(self):
        """Not a test, just a synopsis of the various ACAllowable types."""
        for suggestion_list_type in ACAllowable().type_names:
            self.ac.suggest(suggestion_list_type)
            print("Suggestion Type: {}, Number of entries: {}".format(
                suggestion_list_type, len(self.ac._suggestion_data)))
            for line in self.ac._suggestion_data[:5]:
                print("\t{}".format(line))
            print("...")
            for line in self.ac._suggestion_data[-5:]:
                print("\t{}".format(line))

class TestAbbreviating(unittest.TestCase):
    """
    Test the abbreviating static methods in ObserverAutoComplete
    """
    def test_simple_case(self):
        test_lines = [
            "CODE1 The precipitation in Hispania descends primarily on the peneplain.",
            "CODE2 The length of GroundFish (inches)",
        ]
        abbreviations = {
            "precipitation": "rain",
            "Hispania": "Spain",
            "descends": "falls",
            "primarily": "mainly",
            "peneplain.": "plain.", # Note the need for including punctuation.
            "(inches)": "(in)",     # Note the need for including delimiters not separated by space.
            "GroundFish": "GF",
        }
        expected_abbreviated_lines = [
            "CODE1 The rain in Spain falls mainly on the plain.",
            "CODE2 The length of GF (in)",
        ]
        actual_abbreviated_lines = ObserverAutoComplete._abbreviate_suggestions(test_lines, abbreviations)
        self.assertEqual(2, len(actual_abbreviated_lines))
        self.assertEqual(expected_abbreviated_lines, actual_abbreviated_lines)

    def test_first_word_is_not_abbreviated(self):
        test_lines = [
            "CODE1 This line is the description for CODE1",
            "GroundFish is being used as a code word. Only in the description will GroundFish be abbreviated.",
        ]
        abbreviations = {
            "CODE1": "code-1",
            "GroundFish": "GF",
        }
        expected_abbreviated_lines = [
            "CODE1 This line is the description for code-1",
            "GroundFish is being used as a code word. Only in the description will GF be abbreviated.",
        ]
        actual_abbreviated_lines = ObserverAutoComplete._abbreviate_suggestions(test_lines, abbreviations)
        self.assertEqual(2, len(actual_abbreviated_lines))
        self.assertEqual(expected_abbreviated_lines, actual_abbreviated_lines)


if __name__ == '__main__':
    unittest.main()
