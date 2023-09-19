import glob
import os

from engine.SecurityNodeVisitor import SecurityNodeVisitor
from model.literal_access import LiteralAccess


class Engine(object):
    def __init__(self, code_dir: str):
        self.code_dir = code_dir
        self.modules = dict()
        self.web_framework = None
        self.framework_properties = dict()

    def run(self):
        glob_pattern = f'{self.code_dir}/**/*.py'
        for source_file in glob.glob(glob_pattern, recursive=True):
            module_path = source_file.replace('.py', '').replace('__init__', '').replace(self.code_dir,
                                                                                         '').removeprefix(
                '/').removesuffix('/')
            module_name = module_path.replace('/', '.')
            module = SecurityNodeVisitor.parse_module(source_file)
            self.modules[module_name] = module
            print(module_name, module_path, source_file, module)

    def detected_web_framework(self):
        if self.is_django():
            self.web_framework = "Django"
        pass

    def is_django(self):
        """
        如何判断一个 Python 项目是否未 Django 项目？
        1、项目主目录中存在 manage.py 文件
        2、manage.py 文件中存在 os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_sample.settings')
        3、引入 execute_from_command_line：from django.core.management import execute_from_command_line
        4、执行 execute_from_command_line(sys.argv)
        :return:
        """
        manage_path = os.path.join(self.code_dir, "manage.py")
        app_setting_module = SecurityNodeVisitor.parse_module(manage_path)
        if self.exist_execute_from_command_line(app_setting_module) and self.exist_execute_from_command_line_call(
                app_setting_module):
            status, app_name, app_setting = self.get_custom_app_setting(app_setting_module)
            if status:
                self.framework_properties['DjangoAppSetting'] = app_setting
                self.framework_properties['DjangoApp'] = app_name
                return True
        return False

    @staticmethod
    def exist_execute_from_command_line(module):
        for packageName in module.imports:
            for packageValue in module.imports[packageName]:
                if packageValue.name.startswith(
                        'django.core.management.') and packageValue.alias == 'execute_from_command_line':
                    return True
        return False

    @staticmethod
    def get_custom_app_setting(module):
        """
        获取 Django APP，逻辑需要进一步细化，否则会出现漏掉的情况
        :param module:
        :return:
        """
        for key in module.func_access:
            if key.startswith('os.environ.setdefault(') is False:
                continue

            func_call = module.func_access[key]
            if len(func_call.args) != 2:
                continue

            # 检查 key 是否为 "DJANGO_SETTINGS_MODULE"
            env_key = func_call.args[0]
            if isinstance(env_key, LiteralAccess) is False or env_key.l_value != 'DJANGO_SETTINGS_MODULE':
                continue

            # 获取 app 及 app.settings
            if isinstance(func_call.args[1], LiteralAccess):
                app_setting = func_call.args[1].l_value
                app_name = '.'.join(app_setting.split('.')[:-1])
                return True, app_name, app_setting
        return False, None, None

    @staticmethod
    def exist_execute_from_command_line_call(module):
        for key in module.func_access:
            if key.startswith('execute_from_command_line('):
                return True
        return False


if __name__ == '__main__':
    engine = Engine("/Users/owefsad/PycharmProjects/django_sample")
    engine.run()
    engine.detected_web_framework()

    print(engine.modules)
