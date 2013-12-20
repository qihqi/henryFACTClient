package henry.model;

import lombok.Getter;
import lombok.Setter;

public class Producto {
    @Getter @Setter private String codigo;
    @Getter @Setter private String nombre;
    //precios en unidad de centavos
    @Getter @Setter private int precio1;
    @Getter @Setter private int precio2;
    @Getter @Setter private int threshold;

    @Override
    public String toString() {
        return nombre;
    }
}
