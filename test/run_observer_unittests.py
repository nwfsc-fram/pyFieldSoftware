import fnmatch
import os
import unittest


# modified from http://stackoverflow.com/questions/1732438/how-to-run-all-python-unit-tests-in-a-directory/24562019#24562019

def all_test_modules(root_dir, pattern):
    test_file_names = all_files_in(root_dir, pattern)
    return [path_to_module(str) for str in test_file_names]


def all_files_in(root_dir, pattern):
    matches = []

    for root, dirnames, filenames in os.walk(root_dir):
        for filename in fnmatch.filter(filenames, pattern):
            matches.append(os.path.join(root, filename))

    return matches


def path_to_module(py_file):
    return strip_leading_dots( \
        replace_slash_by_dot( \
            strip_extension(py_file)))


def strip_extension(py_file):
    return py_file[0:len(py_file) - len('.py')]


def replace_slash_by_dot(str):
    return str.replace('\\', '.').replace('/', '.')


def strip_leading_dots(str):
    while str.startswith('.'):
        str = str[1:len(str)]
    return str


if __name__ == '__main__':
    common_module_names = all_test_modules('../py/common', '*.py')
    # Remove LabelPrinter - imports serial module not included OPTECS
    common_modules_not_used_in_optecs = ['py.common.LabelPrinter']
    #print(common_module_names)
    for skip_this in common_modules_not_used_in_optecs:
        if skip_this in common_module_names:
            common_module_names.remove(skip_this)

    observer_module_names = all_test_modules('../py/observer', '*.py')
    print(observer_module_names)
    optecs_modules_to_skip = ['py.observer.GeneratePonyORM']
    for skip_this in optecs_modules_to_skip:
        if skip_this in observer_module_names:
            observer_module_names.remove(skip_this)
    main_module_names = all_test_modules('../', 'main_observer.py')

    common_tests = [unittest.defaultTestLoader.loadTestsFromName(mname) for mname
                    in common_module_names]
    """
    common_tests = []
    """
    observer_tests = [unittest.defaultTestLoader.loadTestsFromName(mname) for mname
                      in observer_module_names]
    main_tests = [unittest.defaultTestLoader.loadTestsFromName(mname) for mname
                  in main_module_names]

    fullSuite = unittest.TestSuite(common_tests + observer_tests + main_tests)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(fullSuite)
