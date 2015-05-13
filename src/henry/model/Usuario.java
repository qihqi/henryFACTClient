package henry.model;

import lombok.Getter;
import lombok.Setter;

public class Usuario extends BaseModel {
    @Getter private String nombre;
    @Getter private String clave;
    @Getter @Setter private int lastFactura;
    @Getter @Setter private int bodega;
}
