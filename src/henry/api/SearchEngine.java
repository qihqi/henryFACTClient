package henry.api;

import henry.model.Cliente;
import henry.model.Producto;

import java.util.ArrayList;
import java.util.List;

/**
 * Created by han on 12/19/13.
 */
public interface SearchEngine<T> {
    List<T> search(String prefijo);

    public static final SearchEngine<Producto> PRODUCTO = new SearchEngine<Producto>() {
        @Override
        public List<Producto> search(String prefijo) {
            return FacturaInterface.INSTANCE.buscarProducto(prefijo);
        }

        @Override
        public String toString() {
            return "Producto";
        }
    };

    public static final SearchEngine<Cliente> CLIENTE = new SearchEngine<Cliente>() {
        @Override
        public List<Cliente> search(String prefijo) {
            return FacturaInterface.INSTANCE.buscarCliente(prefijo);
        }

        @Override
        public String toString() {
            return "Cliente";
        }
    };
}
