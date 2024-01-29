from importlib import import_module


class CorrectionMethod:
    required_modules = []

    @classmethod
    def _prepare_imports_(cls):
        for requirement in cls.required_modules:
            if requirement not in sys.modules:
                import_module(requirement)

    def _do_magic_(**kwargs):
        pass  # Override this

    @classmethod
    def do_correction(cls, inital_value):
        cls._prepare_imports_()
        cls._do_magic_()
        pass


def pressure_correction(method: CorrectionMethod, **kwargs):
    print("Magic is happening")
    return method.do_corection(**kwargs)
