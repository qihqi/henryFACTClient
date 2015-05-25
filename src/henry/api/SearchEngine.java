package henry.api;

import henry.model.Cliente;
import henry.model.Producto;

import java.util.List;

/**
 * Created by han on 12/19/13.
 */
public interface SearchEngine<T> {
    List<T> search(String prefijo);
}
