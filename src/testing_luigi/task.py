import luigi

class MyTask(luigi.Task):

    def output(self):
        return luigi.LocalTarget("count.csv")

    def requires(self):
        return None

    def run(self):
        with self.output().open("w") as out_file:
           	out_file.write('Hello world')

class HepTask(luigi.Task):
    test = luigi.Parameter(significant=False)

    def output(self):
        return None

    def requires(self):
        return MyTask()

    def run(self):
        print()
        with self.input().open() as input_file:
            print(''.join(input_file.readlines()))
        if self.test:
            print(self.test, 'is a', type(self.test))
        print()
