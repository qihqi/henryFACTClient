package henry.api;

import henry.model.Cliente;
import henry.model.Documento;
import henry.model.Producto;

import java.util.List;

public interface FacturaInterface {
    Producto getProductoPorCodigo(String codigo);
    List<Producto> buscarProducto(String prefijo);
    
    Cliente getClientePorCodigo(String codigo);
    List<Cliente> buscarCliente(String prefijo);

    void guardarDocumento(Documento doc);
    Documento getPedidoPorCodigo(String codigo);

    public static final FacturaInterface INSTANCE = new FacturaInterfaceRest("192.168.0.23");
}
