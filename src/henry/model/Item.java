package henry.model;

import lombok.Getter;
import lombok.Setter;

public class Item extends BaseModel {
    @Getter @Setter private int cantidad; //en milesimas
    @Getter @Setter private Producto producto;

    public Item() {
        cantidad = 0;
    }

    public int getSubtotal() {
        if (producto == null) {
            return 0;
        }
        int precio = producto.getPrecio1();
        return milesimaPorCentavos(cantidad, precio);
    }

    public int getDescuento() {
        if (producto == null) {
            return 0;
        }
        if (cantidad >= producto.getThreshold()) {
            int descUnit = producto.getPrecio1() - getProducto().getPrecio2();
            return milesimaPorCentavos(cantidad, descUnit);
        }
        else {
            return 0;
        }
    }

    private static int milesimaPorCentavos(int milesimas, int centavos) {
        return (milesimas / 1000) * centavos + ((milesimas % 1000) * centavos) / 1000 ;
    }
}
