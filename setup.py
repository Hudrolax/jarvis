class Dependence:
    __modules = []

    @staticmethod
    def append(module_name: str):
        if isinstance(module_name, str):
            Dependence.__modules.append(module_name)
        else:
            raise Exception("Wrong type for append function!")

    @staticmethod
    def install(package):
        import subprocess
        subprocess.call(['pip', 'install', package])

    @staticmethod
    def init():
        for module in Dependence.__modules:
            Dependence.install(module)

if __name__ == '__main__':
    Dependence.append('pyTelegramBotAPI')
    Dependence.init()