package henry.model;

import lombok.Getter;

public class Usuario extends BaseModel {
    @Getter private String nombre;
    @Getter private String clave;
}
