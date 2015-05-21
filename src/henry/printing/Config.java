package henry.printing;

import static henry.Helpers.streamToString;
import com.google.gson.Gson;
import com.google.gson.annotations.SerializedName;
import lombok.Setter;
import lombok.Getter;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.FileInputStream;

public final class Config {
     public static class ContenidoConfig {
         @Getter
         int[] pos;
         @Getter
         int[] sp;
         @Getter
         int vsp;
    }

    public static class ImpressionConfig {
         @Getter
         double[] disp;
         @Getter
         double[] tamano;
         @Getter
         double[] ruc;
         @Getter
         double[] cliente;
         @Getter
         double[] remision;
         @Getter
         double[] direccion;
         @Getter 
         double[] fecha;
         @Getter
         double[] telf;
         @Getter @SerializedName("ruc_delta")
         double[] rucDelta;
         @Getter @SerializedName("direccion_delta")
         double[] direccionDelta;
         @Getter @SerializedName("fecha_delta")
         double[] fechaDelta;
         @Getter @SerializedName("telf_delta")
         double[] telfDelta;
         @Getter @SerializedName("cliente_delta")
         double[] clienteDelta;
         @Getter
         double[] bruto;
         @Getter
         double[] desc;
         @Getter
         double[] neto;
         @Getter
         double[] iva;
         @Getter
         double[] total;
         @Getter
         double[] title;
         @Getter
         int lineas;
         @Getter
         ContenidoConfig contenido;
    }

    @Getter
    @SerializedName("fontsize")
    int fontSize;
    @Getter
    @SerializedName("fontfamily")
    String fontFamily; 
    @Getter
    boolean factura;

    @Getter
    @SerializedName("factura_blanco")
    boolean facturaBlanco;
    @Getter
    int libre;

    @Getter
    ImpressionConfig impression;

    public static Config getConfigFromJson(String json) {
        return new Gson().fromJson(json, Config.class);
    }
    public static void main(String[] args) throws Exception {
        String content;
        try (InputStream stream = new FileInputStream(args[0])) {
            Config config = Config.getConfigFromJson(streamToString(stream));
            System.out.println(config.getImpression().getTitle()[0]);
        }
    }
}
