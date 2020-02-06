def select2_processor(idps):
    """
    A simple processor for Select2, to adjust the data ready to use for Select2.
    See https://select2.org/data-sources/formats
    """
    def change_idp(idp):
        idp['id'] = idp.pop('entity_id')
        idp['text'] = idp.pop('name')
        return idp

    return [change_idp(idp) for idp in idps]


