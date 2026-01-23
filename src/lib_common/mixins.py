class TypeMixin:
    @property
    def type(self) -> str:
        return self.__class__.__name__
