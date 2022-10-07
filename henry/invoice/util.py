from decimal import Decimal
from typing import Optional, Dict, cast, List

from henry.xades import xades
from henry.invoice.dao import Invoice
from henry.invoice.dao import Invoice, SRINota, load_nota
from henry import constants


def compute_access_code(inv: Invoice, is_prod: bool):
    timestamp = inv.meta.timestamp
    fecha = '{:02}{:02}{:04}'.format(timestamp.day, timestamp.month, timestamp.year)
    tipo_comp = '01'  # 01 = factura
    ruc = inv.meta.almacen_ruc
    numero = '{:09}'.format(int(inv.meta.codigo))  # num de factura
    codigo_numero = '12345678' # puede ser lo q sea de 8 digitos
    tipo_emision = '1'
    serie = '001001'
    ambiente = '1' # 1 = prueba 2 = prod

    access_key_48 = ''.join([fecha, tipo_comp, ruc, ambiente, serie, numero, codigo_numero, tipo_emision])

    access_key = access_key_48 + str(xades.generate_checkcode(access_key_48))
    return access_key


_ALM_ID_TO_INFO = {
    1: {
        'ruc': constants.RUC,
        'name': constants.NAME,
    },
    3: {
        'ruc': constants.RUC_CORP,
        'name': constants.NAME_CORP,
    },
    99: {
        'ruc': 'RUCRUCRUC',
        'name': 'NAMENAMENAME',
    }
}

class IdType:
    RUC = '04'
    CEDULA = '05'
    CONS_FINAL = '07'


def guess_id_type(client_id):
    if len(client_id) == 10:
        return IdType.CEDULA
    if len(client_id) > 10:
        return IdType.RUC
    return IdType.CONS_FINAL


def inv_to_sri_dict(inv: Invoice, sri_nota: SRINota) -> Optional[Dict]:
    """Return the dict used to render xml."""
    assert inv.meta
    assert inv.meta.client
    assert inv.meta.timestamp is not None
    if inv.meta.almacen_id is None:
        return None
    info = _ALM_ID_TO_INFO.get(inv.meta.almacen_id)
    if info is None:
        return None
    tipo_ident = guess_id_type(inv.meta.client.codigo)
    # 99 para consumidor final
    id_compra = '99' if tipo_ident == IdType.CONS_FINAL else inv.meta.client.codigo
    ts = inv.meta.timestamp
    access = sri_nota.access_code
    if access is None:
        access = compute_access_code(inv, False)
    res = {
      'ambiente': 1,
      'razon_social': info['name'],
      'ruc': info['ruc'],
      'clave_acceso': access,
      'codigo': '{:09}'.format(inv.meta.codigo),
      'dir_matriz': 'Boyaca 1515 y Aguirre',
      'fecha': '{:02}/{:02}/{:04}'.format(ts.day, ts.month, ts.year),
      'tipo_identificacion_comprador': tipo_ident,
      'id_comprador': id_compra,
      'razon_social_comprador': inv.meta.client.fullname,
      'subtotal': Decimal(inv.meta.subtotal or 0) / 100,
      'iva': Decimal(inv.meta.tax or 0) / 100,
      'descuento': Decimal(inv.meta.discount or 0) / 100,
      'total': Decimal(inv.meta.total or 0) / 100,
      'tax_percent': inv.meta.tax_percent,
      'detalles': []
    }
    for item in inv.items:
        assert item.prod is not None
        assert item.prod.precio1 is not None
        assert item.prod.precio2 is not None
        assert item.cant is not None
        assert item.prod.cant_mayorista is not None
        if item.cant > item.prod.cant_mayorista:
            desc = (item.prod.precio1 - item.prod.precio2) * item.cant
        else:
            desc = Decimal(0)
        total_sin_impuesto = item.prod.precio1 * item.cant - desc
        total_impuesto = Decimal('0.12') * total_sin_impuesto
        item_dict = {
            'id': item.prod.pid,
            'nombre': item.prod.nombre,
            'cantidad': item.cant,
            'precio': Decimal(item.prod.precio1) / 100,
            'descuento': Decimal(desc) / 100,
            'total_sin_impuesto': Decimal(total_sin_impuesto) / 100,
            'total_impuesto': Decimal(total_impuesto) / 100
        }
        cast(List, res['detalles']).append(item_dict)
    return res


def get_or_generate_xml_paths(sri_nota: SRINota, file_manager, jinja_env, dbapi):

    if not sri_nota.xml_inv_location or not sri_nota.xml_inv_signed_location:
        inv = load_nota(sri_nota, file_manager)
        xml_dict = inv_to_sri_dict(inv, sri_nota)
        if xml_dict is None:
            return None, None
        xml_text = jinja_env.get_template(
            'invoice/factura_2_0_template.xml').render(xml_dict)
        xml_inv_location = '{}.xml'.format(sri_nota.access_code)
        file_manager.put_file(xml_inv_location, xml_text)
        sri_nota.xml_inv_location = xml_inv_location

        xml_inv_signed_location = '{}-signed.xml'.format(sri_nota.access_code)
        signed_xml = xades.sign_xml(xml_text).decode('utf-8')
        file_manager.put_file(xml_inv_signed_location, signed_xml)

        dbapi.update(sri_nota, {
            'xml_inv_location': xml_inv_location,
            'xml_inv_signed_location': xml_inv_signed_location,
        })

    return sri_nota.xml_inv_location, sri_nota.xml_inv_signed_location



