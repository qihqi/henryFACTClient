package henry.api;

import henry.model.Cliente;
import henry.model.Documento;
import henry.model.Producto;
import org.apache.http.HttpEntity;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Map;
import java.util.Scanner;

/**
 * Created by han on 12/30/13.
 */
public class FacturaInterfaceRest implements FacturaInterface {
    private static final String PROD_URL = "http://localhost:8080/api/producto?id=%s&bodega_id=%s";
    private static final String CLIENT_URL = "http://localhost:8080/api/cliente?id=%s";

    private static final JSONParser parser = new JSONParser();

    private String toString(InputStream stream) {
        Scanner scanner = new Scanner(stream).useDelimiter("\\A");
        return scanner.hasNext() ? scanner.next() : null;
    }

    private String getUrl(String url) {
        CloseableHttpClient client = HttpClients.createDefault();
        HttpGet req = new HttpGet(url);
        try {
            CloseableHttpResponse response = client.execute(req);
            HttpEntity entity = response.getEntity();
            String content = toString(entity.getContent());
            return content;
        }
        catch (IOException e) {
            return null;
        }

    }

    @Override
    public Producto getProductoPorCodigo(String codigo) {
        String url = String.format(PROD_URL, codigo, 2);
        String content = getUrl(url);
        try {
            JSONObject json = (JSONObject) parser.parse(content);
            Map obj = (Map) json.get("result");
            Producto producto = new Producto();
            producto.setCodigo(obj.get("codigo").toString());
            producto.setNombre(obj.get("nombre").toString());
            producto.setPrecio2(((Number) obj.get("precio2")).intValue());
            producto.setPrecio1(((Number) obj.get("precio1")).intValue());
            int threshold = obj.get("threshold") == null ? -1 : ((Number) obj.get("threshold")).intValue();
            producto.setThreshold(threshold);

            return producto;
        } catch (ParseException e) {
            e.printStackTrace();
            return null;
        }
    }

    public static void main(String [] s) {
        FacturaInterface inter = new FacturaInterfaceRest();
        Producto p = inter.getProductoPorCodigo("000");
        System.out.println(p.getNombre());
        Cliente c = inter.getClientePorCodigo("NA");
        System.out.println(c.getApellidos());
    }

    @Override
    public List<Producto> buscarProducto(String prefijo) {
        return null;
    }

    @Override
    public Cliente getClientePorCodigo(String codigo) {
        String url = String.format(CLIENT_URL, codigo);
        String content = getUrl(url);
        try {
            JSONObject json = (JSONObject) parser.parse(content);
            Map obj = (Map) json.get("result");
            Cliente cliente = new Cliente();
            cliente.setCodigo(obj.get("codigo").toString());
            cliente.setNombres(obj.get("nombre").toString());
            cliente.setApellidos(obj.get("apellidos").toString());
            cliente.setDireccion(obj.get("direccion").toString());
            cliente.setTelefono(obj.get("telefono").toString());
            cliente.setCiudad(obj.get("ciudad").toString());
            return cliente;
        } catch (ParseException e) {
            e.printStackTrace();
            return null;
        }
    }

    @Override
    public List<Cliente> buscarCliente(String prefijo) {
        return null;
    }

    @Override
    public void guardarDocumento(Documento doc) {

    }
}
