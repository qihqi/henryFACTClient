package henry.api;

import henry.model.Cliente;
import henry.model.Documento;
import henry.model.Producto;

import java.util.ArrayList;
import java.util.List;

public class FacturaInterfaceImplSQL implements FacturaInterface {

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
        List<Producto> result = new ArrayList<>();
        result.add(getProductoPorCodigo(""));
        return result;
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
    public void guardarDocumento(Documento doc) {

    }

    @Override
    public Documento getPedidoPorCodigo(String codigo) {
        return null;
    }

    @Override
    public List<Cliente> buscarCliente(String prefijo) {
        List<Cliente> result = new ArrayList<>();
        result.add(getClientePorCodigo(""));
        return result;
    }

}