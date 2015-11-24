from moca.configuration import ConfigurationParser

class TestConfigurationParser(object):
    def setup(self):
        self.config = ConfigurationParser('../data/application.cfg')

    def test_all_sections(self):
        genomes = self.config.get_all_genomes()
        print genomes
        assert genomes[0] == 'hg19'
