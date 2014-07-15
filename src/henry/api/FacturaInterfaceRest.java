package henry.api;

import com.google.gson.GsonBuilder;
import com.google.gson.TypeAdapter;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonWriter;
import henry.model.Cliente;
import henry.model.Documento;
import henry.model.Producto;
import org.apache.http.*;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.ResponseHandler;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.client.utils.URIBuilder;
import org.apache.http.conn.ClientConnectionManager;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.message.BasicNameValuePair;
import org.apache.http.params.HttpParams;
import org.apache.http.protocol.HttpContext;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;
import com.google.gson.Gson;

import java.io.IOException;
import java.io.InputStream;
import java.io.StringReader;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.*;


/**
 * Created by han on 12/30/13.
 */
public class FacturaInterfaceRest implements FacturaInterface {

    private static final String PROD_URL_PATH = "/api/producto";
    private static final String CLIENT_URL_PATH = "/api/cliente";
    private static final String VETNA_URL_PATH= "/api/pedido";

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
            URI prodUri = new URIBuilder().setScheme("http")
                                          .setHost(baseUrl)
                                          .setPath(PROD_URL_PATH)
                                          .setParameter("id", codigo)
                                          .setParameter("bodega_id", "1")
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
                    .setPath(CLIENT_URL_PATH)
                    .setParameter("id", codigo).build();
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

    }

    @Override
    public Documento getPedidoPorCodigo(String codigo) {
        try {
            URI uri = new URIBuilder().setScheme("http")
                    .setHost(baseUrl)
                    .setPath(VETNA_URL_PATH)
                    .setParameter("id", codigo).build();
            String content = getUrl(uri);
            return parser.parse(content, Documento.class);
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
