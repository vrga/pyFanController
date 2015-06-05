import configparser


class ConfigLoader(object):
    """
    Class to load, and prepare configs for further consumption
    """

    def __init__(self, config_path):
        """
        :param config_path: path to config file
        :type config_path: str
        """
        self.config = configparser.ConfigParser()
        self.config.read(config_path)

    def get(self, section):
        """
        get configuration section.
        :param section: name of the config section you want to get
        :type section: str
        :return:
        """
        return self.config[section]
