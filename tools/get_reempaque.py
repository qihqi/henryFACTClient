from henry.config import sessionfactory
from henry.constants import CONN_STRING
from henry.base.schema import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

poli_session = sessionmaker(
        bind=create_engine(CONN_STRING[:-5]+'policentro'))


def get_reempaque(session):
    for x in session.query(NTransform):
        yield x.origin_id, x.dest_id, x.multiplier

def get_nombres(session, dest):
    for x in session.query(NProducto):
        dest[x.codigo.upper().strip()] = x.nombre

def main2():
    ps = poli_session()
    hs = sessionfactory()
    henry_prod = {}
    get_nombres(hs, henry_prod)
    poli_prod = {}
    get_nombres(ps, poli_prod)

    henry_prod = henry_prod.viewkeys()
    poli_prod = poli_prod.viewkeys()
    print 'henry', len(henry_prod), 'poli', len(poli_prod)
    print 'intersection', len(henry_prod & poli_prod), 'union', len(henry_prod | poli_prod)

def main():
    ps = poli_session()
    hs = sessionfactory()
    prods = {}
    get_nombres(ps, prods)
    get_nombres(hs, prods)
    poli = {x[0]: x for x in get_reempaque(ps)}
    henry = {x[0]: x for x in get_reempaque(hs)}

    for x in poli:
        toprint = []
        toprint.extend((poli[x][0], prods[poli[x][0].upper().strip()]))
        toprint.extend((poli[x][1], prods[poli[x][1].upper().strip()], str(poli[x][2])))
        if x in henry:
            toprint.extend((henry[x][0], prods[henry[x][0].upper()]))
            toprint.extend((henry[x][1], prods[henry[x][1].upper()], str(henry[x][2])))
        print '\t'.join(toprint)
main2()
