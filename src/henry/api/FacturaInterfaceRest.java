package henry.api;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import henry.model.Cliente;
import henry.model.Documento;
import henry.model.Item;
import henry.model.Producto;
import org.apache.http.HttpEntity;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.utils.URIBuilder;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;

import java.io.IOException;
import java.io.InputStream;
import java.io.UnsupportedEncodingException;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.Arrays;
import java.util.List;
import java.util.Scanner;

import static henry.Helpers.displayAsMoney;
import static henry.Helpers.parseMilesimasFromString;
import static henry.Helpers.parseCentavosFromString;


/**
 * Created by han on 12/30/13.
 */
public class FacturaInterfaceRest implements FacturaInterface {

    private static final String PROD_URL_PATH = "/api/producto";
    private static final String CLIENT_URL_PATH = "/api/cliente";
    private static final String VENTA_URL_PATH = "/api/nota";
    private static final String PROD_URL = "/api/alm/%s/producto/%s";

    private Parser parser;
    private CloseableHttpClient httpClient;
    private String baseUrl;

    public FacturaInterfaceRest(String baseUrl) {
        parser = new Parser();
        httpClient = HttpClients.createDefault();
        this.baseUrl = baseUrl;
    }

    @Override
    public Producto getProductoPorCodigo(String codigo) {
        try {
            String url = String.format(PROD_URL, "1", codigo);
            URI prodUri = new URIBuilder().setScheme("http")
                                          .setHost(baseUrl)
                                          .setPath(url)
                                          .build();
            String content = getUrl(prodUri);
            return parser.parse(content, Producto.class);
        } catch (URISyntaxException e) {
            e.printStackTrace();
            return null;
        }
    }

    public static void main(String [] s) throws Exception {
        Parser parser = new Parser();
        System.out.println(parser.parse(
              "{\"apellidos\": \"Consumidor Final\", \"nombres\": \"\", \"ciudad\": null, \"codigo\": \"NA\", \"direccion\": null}",
              Cliente.class));

    }


    @Override
    public List<Producto> buscarProducto(String prefijo) {
        try {
            URI prodUri = new URIBuilder().setScheme("http")
                    .setHost(baseUrl)
                    .setPath(PROD_URL_PATH)
                    .setParameter("prefijo", prefijo)
                    .setParameter("bodega_id", "1").build();
            System.out.println(prodUri.toString());
            String content = getUrl(prodUri);
            return Arrays.asList(parser.parse(content, Producto[].class));
        }
        catch (URISyntaxException ex) {
            ex.printStackTrace();
            return null;
        }
    }

    @Override
    public Cliente getClientePorCodigo(String codigo) {
        try {
            URI uri = new URIBuilder().setScheme("http")
                    .setHost(baseUrl)
                    .setPath(CLIENT_URL_PATH + "/" + codigo)
                    .build();
            String content = getUrl(uri);
            return parser.parse(content, Cliente.class);
        }
        catch (URISyntaxException e) {
            e.printStackTrace();
            return null;
        }
    }

    @Override
    public List<Cliente> buscarCliente(String prefijo) {
        try {
            URI uri = new URIBuilder().setScheme("http")
                    .setHost(baseUrl)
                    .setPath(CLIENT_URL_PATH)
                    .setParameter("prefijo", prefijo).build();
            String content = getUrl(uri);
            return Arrays.asList(parser.parse(content, Cliente[].class));
        }
        catch (URISyntaxException ex) {
            ex.printStackTrace();
            return null;
        }
    }

    @Override
    public void guardarDocumento(Documento doc) {
        System.out.println("guardarDocumento");
        JsonObject meta = new JsonObject();
        meta.addProperty("client_id", doc.getCliente().getCodigo());
        meta.addProperty("user", "");
        meta.addProperty("total", displayAsMoney(doc.getTotal()));
        meta.addProperty("subtotal", displayAsMoney(doc.getSubtotal()));
        meta.addProperty("discount", doc.getDescuento());
        meta.addProperty("bodega", 1);
        meta.addProperty("almacen", 1);
        JsonArray items = new JsonArray();
        for (Item i : doc.getItems()) {
            if (i.getProducto() != null) {
                items.add(prodToJsonArray(i.getProducto(), i.getCantidad()));
                System.out.println("items added");
            } else {
                System.out.println("items is null");
            }
        }
        JsonObject factura = new JsonObject();
        factura.add("meta", meta);
        factura.add("items", items);

        Gson gson = new Gson();
        String content = gson.toJson(factura);
        System.out.println(content);
        try {
            URI uri = new URIBuilder().setScheme("http").setHost(baseUrl)
                    .setPath(VENTA_URL_PATH).build();
            HttpPost req = new HttpPost(uri);
            req.setEntity(new StringEntity(content));
            try (CloseableHttpResponse response = httpClient.execute(req)) {
                HttpEntity entity = response.getEntity();
                String result = toString(entity.getContent());
                System.out.println(result);
            } catch (IOException e) {
                e.printStackTrace();
            }

        }
        catch (URISyntaxException|UnsupportedEncodingException ex) {
            ex.printStackTrace();
        }

    }

    private static JsonArray prodToJsonArray(Producto producto, int cantidad) {
        JsonArray p = new JsonArray();
        p.add(new JsonPrimitive(producto.getCodigo()));
        p.add(new JsonPrimitive(cantidad));
        p.add(new JsonPrimitive(producto.getNombre()));
        p.add(new JsonPrimitive(producto.getPrecio1()));
        return p;
    }

    @Override
    public Documento getPedidoPorCodigo(String codigo) {
        try {
            URI uri = new URIBuilder().setScheme("http")
                    .setHost(baseUrl)
                    .setPath(VENTA_URL_PATH + "/" + codigo).build();
            String content = getUrl(uri);
            System.out.println(content);

            JsonObject documentObject = new Gson().fromJson(content, JsonObject.class);
            Documento doc = new Documento();
            JsonObject metadata = documentObject.get("meta").getAsJsonObject();
            doc.setCliente(parser.parse(metadata.get("client").toString(), Cliente.class));
            JsonArray items = documentObject.get("items").getAsJsonArray();
            for (JsonElement e : items) {
                JsonArray ja = e.getAsJsonArray();
                Item item = new Item();
                Producto p = new Producto();

                p.setCodigo(ja.get(0).toString());
                item.setCantidad(parseMilesimasFromString(ja.get(1).toString()));
                p.setNombre(ja.get(2).toString());
                p.setPrecio1(parseCentavosFromString(ja.get(3).toString()));
                doc.addItem(item);
            }
            return doc; 
        }
        catch (URISyntaxException ex) {
            ex.printStackTrace();
            return null;
        }
    }

    private static String toString(InputStream stream) {
        Scanner scanner = new Scanner(stream).useDelimiter("\\A");
        return scanner.hasNext() ? scanner.next() : null;
    }

    private String getUrl(URI uri) {
        HttpGet req = new HttpGet(uri);
        try (CloseableHttpResponse response = httpClient.execute(req)) {
            HttpEntity entity = response.getEntity();
            String content = toString(entity.getContent());
            return content;
        }
        catch (IOException e) {
            return null;
        }

    }
}
