package henry.model;

import lombok.Getter;
import lombok.Setter;

public class Usuario extends BaseModel {
    @Getter @Setter private String nombre;
    @Getter @Setter private int lastFactura;
    @Getter @Setter private int bodega;
}
