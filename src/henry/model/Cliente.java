package henry.model;

import lombok.Getter;

public class Cliente extends BaseModel {
    @Getter
    private String codigo;

    @Getter
    private String nombres;

    @Getter
    private String apellidos;

    @Getter
    private String direccion;

    @Getter
    private String ciudad;

    @Getter
    private String tipo;

    @Getter
    private String telefono;

    public void load(String codigo) {
    }

}

