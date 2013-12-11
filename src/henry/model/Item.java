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
        int precio = getPrecio();
        return (cantidad / 1000) * precio + ((cantidad % 1000) * precio) / 1000 ;
    }

    public int getPrecio() {
        return (cantidad >= producto.getThreshold()) ?
                producto.getPrecio1() : producto.getPrecio2();
    }

    public String getDisplayCantidad() {
        return String.format("%d.%d", cantidad / 1000, cantidad % 1000);
    }

    public String getDisplayPrecio() {
        int precio = getPrecio();
        return String.format("%d.%d", precio / 100, precio % 100);
    }

    public String getDisplaySubtotal() {
        int subtotal = getSubtotal();
        return String.format("%d.%d", subtotal / 100, subtotal % 100);
    }
}
