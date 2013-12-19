package henry.api;

import henry.model.Cliente;
import henry.model.Producto;

import java.util.List;

public class FacturaInterfaceImpl implements FacturaInterface {

    @Override
    public Producto getProductoPorCodigo(String codigo) {
        Producto producto = new Producto();
        producto.setCodigo("123");
        producto.setPrecio1(200);
        producto.setPrecio2(150);
        producto.setThreshold(3000);
        producto.setNombre("producto de prueba");
        return producto;
    }

    @Override
    public List<Producto> buscarProducto(String prefijo) {
        return null;
    }

    @Override
    public Cliente getClientePorCodigo(String codigo) {
        Cliente cliente = new Cliente();
        cliente.setCodigo("NA");
        cliente.setApellidos("Cliente General");
        cliente.setNombres("Cliente General");
        return cliente;
    }

    @Override
    public List<Cliente> buscarCliente(String prefijo) {
        return null;
    }
}