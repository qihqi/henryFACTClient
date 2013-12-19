package henry.model;

import lombok.Getter;
import lombok.Setter;

public class Cliente extends BaseModel {
    @Getter @Setter
    private String codigo;

    @Getter @Setter
    private String nombres;

    @Getter @Setter
    private String apellidos;

    @Getter @Setter
    private String direccion;

    @Getter @Setter
    private String ciudad;

    @Getter @Setter
    private String tipo;

    @Getter @Setter
    private String telefono;
}

