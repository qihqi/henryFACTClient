package henry.api;

import java.util.List;
import henry.model.Producto;
import henry.model.Cliente;

public interface FacturaInterface {
    Producto getProductoPorCodigo(String codigo);
    List<Producto> buscarProducto(String prefijo);
    
    Cliente getClientePorCodigo(String codigo);
    List<Cliente> buscarCliente(String prefijo);

    public static final FacturaInterface INSTANCE = new FacturaInterfaceImpl();
}
