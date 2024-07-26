class LindaInternalError(Exception):
    pass


class LindaNAs(LindaInternalError):
    pass


class LindaNoValues(LindaInternalError):
    pass


class LindaWrongData(LindaInternalError):
    pass


class GlindaP2PError(Exception):
    pass
