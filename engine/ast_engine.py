import glob

from engine.SecurityNodeVisitor import SecurityNodeVisitor


class Engine(object):
    def __init__(self, code_dir: str):
        self.code_dir = code_dir
        self.modules = dict()

    def run(self):
        glob_pattern = f'{self.code_dir}/**/*.py'
        for source_file in glob.glob(glob_pattern, recursive=True):
            module_path = source_file.replace('.py', '').replace('__init__', '').replace(self.code_dir,
                                                                                         '').removeprefix(
                '/').removesuffix('/')
            module_name = module_path.replace('/', '.')
            module = SecurityNodeVisitor.parse_module(source_file)
            print(module_name, module_path, source_file, module)


if __name__ == '__main__':
    engine = Engine("/Users/owefsad/PycharmProjects/bandit")
    engine.run()
