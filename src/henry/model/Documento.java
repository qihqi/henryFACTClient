package henry.model;

import java.util.ArrayList;
import java.util.List;
import lombok.Getter;
import lombok.Setter;

public class Documento extends BaseModel {
    @Getter @Setter private Cliente cliente;
    @Getter private List<Item> items;

    @Getter @Setter private int total;
    @Getter @Setter private int descuento;
    @Getter @Setter private int subtotal;
    @Getter @Setter private int iva;

    public Documento() {
        items = new ArrayList<Item>();
    }
}
