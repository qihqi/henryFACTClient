package henry.api;

import henry.model.Cliente;
import henry.model.Producto;

import java.util.List;

public class FacturaInterfaceImpl implements FacturaInterface {

    @Override
    public Producto getProductoPorCodigo(String codigo) {
        Producto producto = new Producto();
        producto.setCodigo("123");
        producto.setPrecio1(1);
        producto.setPrecio2(2);
        producto.setThreshold(3);
        producto.setNombre("producto de prueba");
        return producto;
    }

    @Override
    public List<Producto> buscarProducto(String prefijo) {
        return null;
    }

    @Override
    public Cliente getClientePorCodigo(String codigo) {
        return null;
    }

    @Override
    public List<Cliente> buscarCliente(String prefijo) {
        return null;
    }
}