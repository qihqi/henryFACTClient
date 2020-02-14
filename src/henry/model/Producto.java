package henry.model;

import com.google.gson.annotations.Expose;
import lombok.Getter;
import lombok.Setter;

/* Sample:
 * {"pid": 16731, 
 *   "nombre": "ARREGLO VIOLETA", 
 *   "almacen_id": 1, "codigo": "VIOLETA", 
 *   "precio1": 3247, "precio2": 3247, 
 *   "threshold": 0, "upi": null, "unidad": 
 *   "UNIDAD", "multiplicador": "1.000"} 
 * */

public class Producto {
    @Expose
    @Getter @Setter
    private String codigo;

    @Expose
    @Getter @Setter
    private String nombre;

    //precios en unidad de centavos
    @Expose
    @Getter @Setter
    private int precio1;

    @Expose
    @Getter @Setter
    private int precio2;

    @Expose
    @Getter @Setter
    private int threshold;

    @Expose
    @Getter @Setter
    private int almacenId;

    @Expose
    @Getter @Setter
    private String unidad;

    @Expose
    @Getter
    private String multiplicador;


    @Override
    public String toString() {
        return nombre;
    }
}
