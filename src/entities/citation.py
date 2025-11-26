class Citation:
    def __init__(self, citation_id, entry_type, citation_key, fields):
        self._id = citation_id
        self._entry_type = entry_type
        self._citation_key = citation_key
        self._fields = fields

    @property
    def id(self):
        return self._id

    @property
    def entry_type(self):
        return self._entry_type

    @property
    def citation_key(self):
        return self._citation_key

    @property
    def fields(self):
        return self._fields

    def __str__(self):
        return f"@{self.entry_type}{{{self.citation_key}, {self.fields}}}"

    def __repr__(self):
        return f"{self.__class__!s}({self.__dict__!r})"
