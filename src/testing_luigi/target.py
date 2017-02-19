import luigi

class MyTarget(luigi.Target):

    def __init__(self):
        self.__exists = False

    def exists(self):
        """
        Does this Target exist?
        """
        return self.__exists

    def create(self):
        self.__exists = True
