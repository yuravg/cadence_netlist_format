#!/usr/bin/env python

# Time-stamp: <2017-04-14 15:43:04>

"""
Work wiht configuration file by ConfigParser
"""

try:
    from configparser import ConfigParser
except ImportError:  # for version < 3.0
    from ConfigParser import ConfigParser

__version__ = '0.1.3'

config = ConfigParser()


class ConfigFile(object):
    """Work with configuration file,
    read and write key from/to configuration file

    Arguments:
    k -- keys of configuration file
        k = {'section0': {'key_name0':value0, 'key_name1':value1},
             'section1': {'key_name0':value0, 'key_name1':value1},
             'section2': {'key_name0':value0, 'key_name1':value1}
            }
    """

    def __init__(self, fname='fname.ini', k={}, verbosity=0):
        """Open configuration file name, read keys
        If configuration file has key, it's value will override initial valueq
        Keyword Arguments:
        fname     -- file name
        k         -- configuration keys
        verbosity -- verbosity for work with config file (1 - for enable verbosity)
        """
        if verbosity == 1:
            self.verbosity = 1
        else:
            self.verbosity = 0
        self.fname = fname
        config.optionxform = str
        config.read(fname)
        # override from file:
        for section in k:
            for i in k[section]:
                if config.has_option(section, i):
                    k[section][i] = config.get(section, i)
                    if self.verbosity:
                        print('read config: section: %s, keys: %s=%s' %
                              (section, i, k[section][i]))
        # get all section from file: kf - keys of file
        sections = config.sections()
        kf = {}
        for section in sections:
            ki = {}
            keys = list(config[section].keys())
            for i in keys:
                val = config.get(section, i)
                ki[i] = val
                kf[section] = ki
        self.k = kf
        self.update_keys(k)

    def update_keys(self, k):
        """Update configuration keys with new keys
        Keyword Arguments:
        k -- new key
        """
        keys_self = list(self.k.keys())
        keys_new = list(k.keys())
        eq_list = [i for i in self.k if i in k]
        new_key_list = list(set(keys_new) - set(keys_self))
        for i in eq_list:
            self.k[i].update(k[i])
        for i in new_key_list:
            self.k[i] = k[i]

    def edit_key_dict(self, k):
        """Edit configuration configuration keys, edit exist, add new
        Input keys in dictionary format
        Keyword Arguments:
        k --keys of configuration file
        """
        self.update_keys(k)
        if self.verbosity:
            for section in k:
                for i in k[section]:
                    print('Edit key: section: %s, keys: %s=%s' % (section, i, str(k[section][i])))

    def edit_key(self, section, kname, kval):
        """Edit key with usage them field name
        Keyword Arguments:
        sections -- sections of keys
        kname    -- name of keys
        kval     -- value of keys
        """
        if self.verbosity:
            print('Edit key: section: %s, keys: %s=%s' % (str(section), str(kname), str(kval)))
        self.k[str(section)][str(kname)] = kval

    def get_all_keys(self):
        """Returns all keys as dictionary
        """
        return self.k

    def get_key(self, section, name):
        """Returns key value from section and name
        Keyword Arguments:
        section -- section of key
        name    -- name for key
        """
        return self.k[section][name]

    # def del_key(self, id):
    #     """Delete key from configuration files
    #     Note: need usage method clear to delete from configuration file
    #     """
    #     print('Delete key: ' + str(id))
    #     del self.k[str(id)]

    # def clear(self):
    #     """Delete all not assigned key and sections from configuration files
    #     """
    #     print('Clear configuration file: ' + str(self.fname))
    #     config.clear()

    def write2file(self):
        """Write keys to configuration file
        """
        sections = config.sections()
        for section in sorted(self.k):
            if section not in sections:
                config.add_section(section)
            for i in sorted(self.k[section]):
                config.set(section, i, self.k[section][i])
        with open(self.fname, 'w') as configfile:
            config.write(configfile)

    def __str__(self):
        s = 'File name: %s' % str(self.fname)
        for section in sorted(self.k):
            s = '%s\nSection: %s:' % (s, section)
            for i in sorted(self.k[section]):
                s = '%s \'%s\'=%s' % (s, i, self.k[section][i])
        return '%s;' % s


if __name__ == '__main__':
    def write_template_file(fname):
        f = open(fname, 'w')
        f.write('[Default1]\n')
        f.write('name10 = orign10\n')
        f.write('name11 = orign11\n')
        f.write('\n')
        f.write('[Default0]\n')
        f.write('name01 = orign01\n')
        f.write('name00 = orign00\n')
        f.close()

    fname = 'configfile.ini'
    write_template_file(fname)
    from shutil import copyfile
    copyfile(fname, 'tmp_configfile.ini')
    key1 = {}
    key1 = {'Default0': {'name00': 'init00', 'name01': 'init01', 'name_empty': 'some_name'},
            'Feature': {'option1': 'init_option1'}}
    print('\nRun test:')
    c = ConfigFile(fname, key1, 1)
    print('--------------------------------------------------------')
    print('* Config: ' + str(c))
    print('--------------------------------------------------------')
    new_k1 = {'Default0': {'name00': 'edited00', 'name02': 'new_edit_value02'}}
    c.edit_key_dict(new_k1)
    new_k2 = {'Default0': {'name00': 'edited00_2'},
              'Default2': {'name99': '99', 'name02': 'edited02_0'}}
    c.edit_key_dict(new_k2)
    print('--------------------------------------------------------')
    print('* Config: ' + str(c))
    print('--------------------------------------------------------')
    # print('end of config file')
    print('Write2file')
    # c.sort_keys()
    c.edit_key('Default2', 'name99', 'new_name99')
    c.write2file()
    print('-------------')
    print('get_all_keys: %s' % c.get_all_keys())
    print('Some key[%s][%s] = %s' % ('Default0', 'name00', c.get_key('Default0', 'name00')))
    print('Done')
