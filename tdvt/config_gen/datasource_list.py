"""
    Register datasources for use with TDVT runner.

"""

import configparser
import glob
import os.path
import logging

from ..resources import *
from .test_config import TestConfig,TestSet,build_config_name,build_tds_name

def LoadTest(config):
    """ Parse a datasource test suite config into a TestConfig object.
    [Datasource]
    Name = bigquery
    LogicalQueryFormat = bool_
    CommandLineOverride =

    [StandardTests]
    LogicalExclusions_Calcs = 
    LogicalExclusions_Staples = Filter.Trademark
    ExpressionExclusions_Standard = string.char,dateparse

    [LODTests]
    LogicalExclusions_Staples = 
    ExpressionExclusions_Calcs = 

    [StaplesDataTest]

    [UnionTest]

    [MedianTests]

    [PercentileTests]

    [NewExpressionTest1]
    Name = expression_test_dates.
    TDS = cast_calcs.bigquery_sql_dates.tds
    Exclusions = string.ascii
    TestPath = exprtests/standard/ 
    
    [LogicalConfig]
    Name = mydb_config
    key = value

    """
    CALCS_TDS = 'cast_calcs.'
    STAPLES_TDS = 'Staples.'

    standard_tests = 'StandardTests'
    lod_tests = 'LODTests'
    staples_data_test = 'StaplesDataTest'
    new_expression_test = 'NewExpressionTest'
    new_logical_test = 'NewLogicalTest'
    union_test = 'UnionTest'
    datasource_section = 'Datasource'
    regex_test = 'RegexTest'
    median_test = 'MedianTests'
    percentile_test = 'PercentileTests'
    logical_config = 'LogicalConfig'

    KEY_EXCLUSIONS = 'Exclusions'

    #Check the ini sections to make sure there is nothing that is unrecognized. This should be empty by the time we are done.
    all_ini_sections = config.sections()

    #This is required.
    dsconfig = config[datasource_section]
    all_ini_sections.remove(datasource_section)
    config_name = dsconfig['Name']
    test_config = TestConfig(config_name, dsconfig['LogicalQueryFormat'], dsconfig.get('MaxThread', '0'), dsconfig.get('MaxSubThread', '0'), dsconfig.get('CommandLineOverride', ''))

    #Add the standard test suites.
    if standard_tests in config.sections():
        try:
            standard = config[standard_tests]
            all_ini_sections.remove(standard_tests)
            
            test_config.add_logical_test('logical.calcs.', CALCS_TDS, standard.get('LogicalExclusions_Calcs', ''), test_config.get_logical_test_path('logicaltests/setup/calcs/setup.*.'))
            test_config.add_logical_test('logical.staples.', STAPLES_TDS, standard.get('LogicalExclusions_Staples', ''), test_config.get_logical_test_path('logicaltests/setup/staples/setup.*.'))
            test_config.add_expression_test('expression.standard.', CALCS_TDS, standard.get('ExpressionExclusions_Standard', ''), 'exprtests/standard/')
        except KeyError as e:
            logging.debug(e)
            pass

    #Add the optional LOD tests.
    if lod_tests in config.sections():
        try:
            lod = config[lod_tests]
            all_ini_sections.remove(lod_tests)
            test_config.add_logical_test('logical.lod.', STAPLES_TDS, lod.get('LogicalExclusions_Staples', ''), test_config.get_logical_test_path('logicaltests/setup/lod/setup.*.'))
            test_config.add_logical_test('logical.lod.calcs.', CALCS_TDS, lod.get('LogicalExclusions_Calcs', ''), test_config.get_logical_test_path('logicaltests/setup/lod_calcs/setup.*.'))
            test_config.add_expression_test('expression.lod.', CALCS_TDS, lod.get('ExpressionExclusions_Calcs', ''), 'exprtests/lodcalcs/setup.*.txt')
        except KeyError as e:
            logging.debug(e)
            pass

    #Add the optional Staples data check test.
    if staples_data_test in config.sections():
        try:
            staples_data = config[staples_data_test]
            all_ini_sections.remove(staples_data_test)
            test_config.add_expression_test('expression.staples.', STAPLES_TDS, '', 'exprtests/staples/setup.*.txt')
        except KeyError as e:
            logging.debug(e)
            pass

    #Add the optional Union test.
    if union_test in config.sections():
        try:
            union = config[union_test]
            all_ini_sections.remove(union_test)
            test_config.add_logical_test('logical.union.', CALCS_TDS, '', test_config.get_logical_test_path('logicaltests/setup/union/setup.*.'))
        except KeyError as e:
            logging.debug(e)
            pass

    #Add the optional Regex test.
    if regex_test in config.sections():
        try:
            regex = config[regex_test]
            all_ini_sections.remove(regex_test)
            test_config.add_expression_test('expression.regex.', CALCS_TDS, regex.get(KEY_EXCLUSIONS, ''), 'exprtests/regexcalcs')
        except KeyError as e:
            logging.debug(e)
            pass

    #Add the optional Median test.
    if median_test in config.sections():
        try:
            median = config[median_test]
            all_ini_sections.remove(median_test)
            test_config.add_expression_test('expression.median.', CALCS_TDS, median.get(KEY_EXCLUSIONS, ''), 'exprtests/median')
        except KeyError as e:
            logging.debug(e)
            pass

    #Add the optional Percentile test.
    if percentile_test in config.sections():
        try:
            percentile = config[percentile_test]
            all_ini_sections.remove(percentile_test)
            test_config.add_expression_test('expression.percentile.', CALCS_TDS, percentile.get(KEY_EXCLUSIONS, ''), 'exprtests/percentile')
        except KeyError as e:
            logging.debug(e)
            pass

    #Optional logical config settings.
    if logical_config in config.sections():
        try:
            cfg = config[logical_config]
            all_ini_sections.remove(logical_config)
            cfg_data = {}
            name = cfg.get('Name', '')
            cfg_data[name] = {}
            for k in cfg:
                if k == 'Name':
                    continue
                else:
                    cfg_data[name][k] = cfg[k]
            test_config.add_logical_config(cfg_data)
        except KeyError as e:
            logging.debug(e)
            pass

    #Add any extra expression tests.
    for section in config.sections():
        sect = config[section]
        #Allow wildcard substitution .
        tds_name = sect.get('TDS', '').replace('*', config_name)
        if new_expression_test in section or sect.get('Type', '') == 'expression':
            try:
                all_ini_sections.remove(section)
                test_config.add_expression_test(sect.get('Name',''), tds_name, sect.get(KEY_EXCLUSIONS,''), sect.get('TestPath',''))
            except KeyError as e:
                logging.debug(e)
                pass

        #Add any extra logical tests.
        elif new_logical_test in section or sect.get('Type', '') == 'logical':
            try:
                all_ini_sections.remove(section)
                test_config.add_logical_test(sect.get('Name',''), tds_name, sect.get(KEY_EXCLUSIONS,''), sect.get('TestPath',''))
            except KeyError as e:
                logging.debug(e)
                pass

    if all_ini_sections:
        logging.debug("Found unparsed sections in the ini file.")
        for section in all_ini_sections:
            logging.debug("Unparsed section: {0}".format(section))

    logging.debug(test_config)
    return test_config
        
class TestRegistry(object):
    """Add a new datasource here and then add it to the appropriate registries below."""
    def __init__(self, ini_file):
        self.dsnames = {}
        self.suite_map = {}

        #Read all the datasource ini files and load the test configuration.
        ini_files = get_all_ini_files_local_first('config')
        for f in ini_files:
            logging.debug("Reading ini file [{}]".format(f))
            config = configparser.ConfigParser()
            #Preserve the case of elements.
            config.optionxform = str
            try:
                config.read(f)
            except configparser.ParsingError as e:
                logging.debug(e)
                continue

            self.add_test(LoadTest(config))

        self.load_ini_file(ini_file)

    def load_ini_file(self, ini_file):
        #Create the test suites (groups of datasources to test)
        registry_ini_file = get_ini_path_local_first('config/registry', ini_file)
        logging.debug("Reading registry ini file [{}]".format(registry_ini_file))
        self.load_registry(registry_ini_file)

    def load_registry(self, registry_ini_file):
        try:
            config = configparser.ConfigParser()
            config.read(registry_ini_file)
            ds = config['DatasourceRegistry']

            for suite_name in ds:
                self.suite_map[suite_name] = self.interpret_ds_list(ds[suite_name], False).split(',')

        except KeyError:
            #Create a simple default.
            self.suite_map['all'] = self.dsnames

    def interpret_ds_list(self, ds_list, built_list=None):
        if ds_list == '*':
            return ','.join([x for x in self.dsnames])
        return ds_list

    def add_test(self, test_config):
        self.dsnames[test_config.dsname] = test_config

    def get_datasource_info(self, dsname):
        if dsname in self.dsnames:
            return self.dsnames[dsname]
        return None

    def get_datasources(self, suite):
        ds_to_run = []
        if not suite:
            return
        for ds in suite.split(','):
            ds = ds.strip()
            if ds in self.suite_map:
                ds_to_run.extend(self.get_datasources(','.join(self.suite_map[ds])))
            elif ds:
                ds_to_run.append(ds)
        
        return ds_to_run

class WindowsRegistry(TestRegistry):
    """Windows specific test suites."""
    def __init__(self):
        super(WindowsRegistry, self).__init__('windows')


class MacRegistry(TestRegistry):
    """Mac specific test suites."""
    def __init__(self):
        super(MacRegistry, self).__init__('mac')

class LinuxRegistry(TestRegistry):
    """Linux specific test suites."""
    def __init__(self):
        super(LinuxRegistry, self).__init__('linux')
