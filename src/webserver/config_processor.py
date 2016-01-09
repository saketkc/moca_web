#!/usr/bin/env python

try:
    import configparser
    conf = configparser.ConfigParser()
except ImportError:
    import ConfigParser
    conf = ConfigParser.ConfigParser()

def read_config(section):
    conf.readfp(open('application.cfg'))
    assert section in conf.sections()
    return conf._sections[section]

if __name__ == '__main__':
    config(section)

