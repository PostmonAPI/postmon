# coding: utf-8
import os

import packtrack


def correios(track, backend=None):
    if backend is None:
        backend = os.getenv('ECT_BACKEND')
    encomenda = packtrack.Correios.track(track, backend=backend)
    if not encomenda:
        raise ValueError(u"Encomenda nao encontrada.")
    if not encomenda.status:
        raise ValueError(u"A encomenda ainda nao tem historico.")

    result = []
    for status in encomenda.status:
        historico = {
            'data': status.data,
            'local': status.local,
            'situacao': status.situacao,
            'detalhes': status.detalhes,
        }
        result.append(historico)
    return result
