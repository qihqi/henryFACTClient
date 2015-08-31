from decimal import Decimal
import csv
import datetime
from henry.config import sessionmanager
from henry.schema.legacy import NIngreso, NIngresoItem
from sqlalchemy.sql import func

dato_dict = {
'PIEN10': ('(X-3) bolitas,tubitos chaquIra DE varios modelos hecho DE vidrio PULIDO,PINTADO', '1.52'),
'TC8X17P': ('(X-3) TIRA  ECHO CON CASCARA DE CoNCHA', '2.3'),
'AAE15F': ('(X-1) clavo,argolla,ADEMAS,    gancho,bolita,tubito,surtidos hecho en  alambre DE HIERRO', '1.6'),
'ELAS10R': ('(X-2)ROLLO ELASTICo', '3.2', 12),
'TC10X3M': ('(X-3) TIRA  ECHO CON CASCARA DE CoNCHA', '2.3'),
'HILNY': ('(X-2)HILO NYLON ROLLO G', '5.77', 12),
'DIJPN': ('(X-3) bolitas,tubitos chaquIra DE varios modelos hecho DE vidrio PULIDO,PINTADO', '1.52'),
'DIAD1.1': ('(X-2)diADEMAS PLASTIC', '1.4'),
'ROSA21': ('(h-1) ramos de rosas , botones ,claveL,de ramos med', '3.1', 12),
'GIRX3TL': ('(H-1) ramos de TALLO LArGO', '4.74' , 12),
'VELC3': ('(X-2)belcro', '5.5'),
'RTX7PQ': ('(H-1) ramos de rosas , botones ,claveL,de ramos PEQUE\xc3\x91O', '1.15',12),
'GIRX3TM': ('(H-1) ramos de TALLO LArGO', '4.74',12),
'PIENROM': ('(X-3) bolitas,tubitos chaquIra DE varios modelos hecho DE vidrio PULIDO,PINTADO', '1.52'),
'MACCM': ('(h-1 ) ramo cadena plastic', '1.4',12),
'ROSA21TM': ('(h-1) ramos de rosas , botones ,claveL,de ramos med', '3.1',12),
'TULX5TL': ('(H-1) ramos de TALLO LArGO', '4.74',12),
'ROX14ESP': ('(H-1) ramos de rosas , botones ,claveL,de ramos PEQUE\xc3\x91O', '1.15',12),
'TCCUE': ('(X-3) TIRA  ECHO CON CASCARA DE CoNCHA', '2.3'),
'ELAS2': ('(X-2)ROLLO ELASTICo', '3.2',12),
'E11BPQ': ('(X-2) ENCAJES', '2.1'),
'PCCB06F': ('(x-2)bolitas,mariposa,argolla tubos,CRUZ, hecho DE plastico', '1.4'),
'BX36PE': ('(H-1) RAMO GRANDE', '7.6',12),
'CY1737': ('(X-1) ROLLO DE  CADENA EN ALUMINO', '1.75'),
'RESNIQF': ('(X-2)RESORTE PLASTIC', '4.2'),
'PEMADEF': ('(x-2)pepaS DE MADERA', '2.25'),
'CY1739': ('(X-1) ROLLO DE  CADENA EN ALUMINO', '1.75'),
'BX36GR': ('(H-1) RAMO GRANDE', '7.6'),
'HILNKG': ('(X-2)HILO NYLON TUBO ROLLO P', '2.08'),
'AAE1': ('(X-1) clavo,argolla,ADEMAS,    gancho,bolita,tubito,surtidos hecho en  alambre DE HIERRO', '1.6'),
'BX36ME': ('(H-1) RAMO GRANDE', '7.6'),
'CY1818': ('(X-1) ROLLO DE  CADENA EN ALUMINO', '1.75'),
'CLAVN': ('(X-1) clavo,argolla,ADEMAS,    gancho,bolita,tubito,surtidos hecho en  alambre DE HIERRO', '1.6')}



def main():
    with sessionmanager as session:
        ing = session.query(NIngreso, NIngresoItem).filter(
            NIngreso.id == NIngresoItem.ref_id).filter( 
            NIngresoItem.producto_id.in_(dato_dict.keys())).filter(
            NIngreso.fecha >= datetime.date(2012, 6, 1)).filter(
            NIngreso.fecha <= datetime.date(2013, 6, 30))

        by_date_item = {}
        for i,item in ing:
            v = dato_dict[item.producto_id.upper()]
            if len(v) == 2:
                disp, precio = v
                x = 1 
            else:
                disp, precio, x = v
            by_date_item[(i.fecha, disp)] = (item.cantidad / Decimal(x), precio)
        end = sorted(by_date_item.items(), key=lambda x: x[0][0])
        with open('/home/han/ventas.csv', 'w') as f:
            csvwriter = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for ((fecha, disp), (cant, precio)) in end:
                csvwriter.writerow([fecha, disp, '', '', '', cant.quantize(Decimal('0.001')), precio])



main()
