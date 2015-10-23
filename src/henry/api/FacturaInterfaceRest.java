package henry.api;

import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.annotations.Expose;
import lombok.Setter;
import org.apache.http.HttpEntity;
import org.apache.http.NameValuePair;
import org.apache.http.client.config.RequestConfig;
import org.apache.http.client.entity.UrlEncodedFormEntity;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.methods.HttpPut;
import org.apache.http.client.utils.URIBuilder;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.BasicCookieStore;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.message.BasicNameValuePair;

import henry.model.Cliente;
import henry.model.Documento;
import henry.model.Item;
import henry.model.Producto;
import henry.model.Usuario;

import static henry.Helpers.streamToString;

public class FacturaInterfaceRest implements FacturaInterface {

    private static final String PROD_URL_PATH = "/api/alm/%d/producto";
    private static final String CLIENT_URL_PATH = "/api/cliente";
    private static final String VENTA_URL_PATH = "/api/pedido";
    private static final String FACTURA_URL_PATH = "/api/nota";
    private static final String PROD_URL = "/api/alm/%d/producto/%s";
    private static final String LOGIN_URL = "/api/authenticate";
    private static final String BARCODE_PATH = "/api/barcode";

    private CloseableHttpClient httpClient;
    private String baseUrl;
    private Gson gson;
    @Setter
    private int almacenId;
    private RequestConfig timeoutConfig;

    public FacturaInterfaceRest(String baseUrl) {
        int TIMEOUT_MILLIS = 30000;
        timeoutConfig = RequestConfig.custom()
            .setConnectionRequestTimeout(TIMEOUT_MILLIS)
            .setConnectTimeout(TIMEOUT_MILLIS)
            .setSocketTimeout(TIMEOUT_MILLIS)
            .build();

        BasicCookieStore cookieStore = new BasicCookieStore();
        httpClient = HttpClients.custom().setDefaultCookieStore(cookieStore).build();
        this.baseUrl = baseUrl;
        gson = new GsonBuilder()
                   .excludeFieldsWithoutExposeAnnotation()
                   .create();
    }

    @Override
    public Producto getProductoPorCodigo(String codigo) throws NotFoundException {
        try {
            String url = String.format(PROD_URL, almacenId, codigo);
            URI prodUri = new URIBuilder().setScheme("http")
                                          .setHost(baseUrl)
                                          .setPath(url)
                                          .build();
            String content = getUrl(prodUri);
            if (content == null) {
                throw new NotFoundException(String.format("Producto %s no encontrado", codigo));
            }
            return gson.fromJson(content, Producto.class);
        } catch (URISyntaxException e) {
            e.printStackTrace();
            return null;
        }
    }

    @Override
    public List<Producto> buscarProducto(String prefijo) {
        try {
            String url = String.format(PROD_URL_PATH, almacenId);
            URI prodUri = new URIBuilder().setScheme("http")
                    .setHost(baseUrl)
                    .setPath(url)
                    .setParameter("prefijo", prefijo).build();
            System.out.println(prodUri.toString());
            String content = getUrl(prodUri);
            if (content == null) {
                return new ArrayList<>();
            }
            Producto[] ps = gson.fromJson(content, Producto[].class);
            return Arrays.asList(ps);
        }
        catch (URISyntaxException ex) {
            ex.printStackTrace();
            return null;
        }
    }

    @Override
    public Cliente getClientePorCodigo(String codigo) throws NotFoundException {
        try {
            URI uri = new URIBuilder().setScheme("http")
                    .setHost(baseUrl)
                    .setPath(CLIENT_URL_PATH + "/" + codigo)
                    .build();
            String content = getUrl(uri);
            if (content == null) {
                throw new NotFoundException("cliente not found");
            }
            return gson.fromJson(content, Cliente.class);
        }
        catch (URISyntaxException e) {
            e.printStackTrace();
            throw new NotFoundException("");
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
            if (content == null) {
                return new ArrayList<>();
            }
            return Arrays.asList(gson.fromJson(content, Cliente[].class));
        }
        catch (URISyntaxException ex) {
            ex.printStackTrace();
            return null;
        }
    }

    static class Codigo {
        @Expose
        int codigo;
    }

    @Override
    public int guardarDocumento(Documento doc, boolean isFactura) {
        System.out.println("guardarDocumento");
        JsonObject factura = serializeDocumento(doc);
        String content = gson.toJson(factura);
        System.out.println(content);
        String path = isFactura ? FACTURA_URL_PATH : VENTA_URL_PATH;
        try {
            URI uri = new URIBuilder().setScheme("http").setHost(baseUrl)
                    .setPath(path).build();
            HttpPost req = new HttpPost(uri);
            req.setConfig(timeoutConfig);
            req.setEntity(new StringEntity(content));
            try (CloseableHttpResponse response = httpClient.execute(req)) {
                if (response.getStatusLine().getStatusCode() == 200) {
                    HttpEntity entity = response.getEntity();
                    String result = streamToString(entity.getContent());
                    return gson.fromJson(result, Codigo.class).codigo;
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        catch (URISyntaxException|UnsupportedEncodingException ex) {
            ex.printStackTrace();
        }
        return -1;

    }

    private JsonObject serializeDocumento(Documento doc) {
        JsonObject meta = new JsonObject();
        meta.add("client", gson.toJsonTree(doc.getCliente()));
        meta.addProperty("user", doc.getUser().getNombre());
        meta.addProperty("total", doc.getTotal());
        meta.addProperty("subtotal", doc.getSubtotal());
        meta.addProperty("discount", doc.getDescuento());

        meta.addProperty("tax_percent", doc.getIvaPorciento());
        meta.addProperty("discount_percent", doc.getDescuentoGlobalPorciento());

        meta.addProperty("almacen_id", almacenId);

        meta.addProperty("total", doc.getTotal());
        meta.addProperty("subtotal", doc.getSubtotal());
        meta.addProperty("tax", doc.getIva());
        meta.addProperty("discount", doc.getDescuento());
        meta.addProperty("codigo", "" + doc.getCodigo());
        meta.addProperty("paid_amount", doc.getPagado());
        meta.addProperty("change", doc.getCambio());
        meta.addProperty("payment_format", doc.getFormaPago());
        meta.addProperty("retension", doc.getRetension());

        JsonObject options = new JsonObject();
        options.addProperty("incrementar_codigo", true);

        JsonArray items = new JsonArray();
        for (Item i : doc.getItems()) {
            if (i.getProducto() != null) {
                items.add(gson.toJsonTree(i));
            }
        }
        JsonObject factura = new JsonObject();
        factura.add("meta", meta);
        factura.add("items", items);
        factura.add("options", options);
        return factura;
    }

    private Documento parseDocumento(JsonObject json) {
        Documento doc = new Documento();
        JsonObject metadata = json.get("meta").getAsJsonObject();
        JsonElement clientObj = metadata.get("client"); 
        if (clientObj != null) {
            String clientString = clientObj.toString();
            if (clientString.length() > 0) {
                doc.setCliente(gson.fromJson(clientString, Cliente.class));
            }
        }
        JsonArray items = json.get("items").getAsJsonArray();
        for (JsonElement e : items) {
            JsonObject obj = e.getAsJsonObject();
            Item item = gson.fromJson(obj.toString(), Item.class);
            if (item != null) {
                doc.addItem(item);
            }
        }
        JsonElement iva_porciento = metadata.get("iva_porciento");
        if (iva_porciento != null) {
            doc.setIvaPorciento(iva_porciento.getAsInt());
        }
        JsonElement descuentoGlobal= metadata.get("descuento_global_porciento");
        if (descuentoGlobal != null) {
            doc.setDescuentoGlobalPorciento(descuentoGlobal.getAsInt());
        }
        return doc;
    }

    @Override
    public Documento getPedidoPorCodigo(String codigo) throws NotFoundException {
        try {
            URI uri = new URIBuilder().setScheme("http")
                    .setHost(baseUrl)
                    .setPath(VENTA_URL_PATH + "/" + codigo).build();
            String content = getUrl(uri);
            if (content == null) {
                throw new NotFoundException(String.format("Pedido numero %s no encontrado", codigo));
            }
            JsonObject documentObject = gson.fromJson(content, JsonObject.class);
            return parseDocumento(documentObject);
        }
        catch (URISyntaxException ex) {
            ex.printStackTrace();
            return null;
        }
    }

    public boolean commitDocument(int docId) {
        URI uri = null;
        try {
            uri = new URIBuilder().setScheme("http")
                .setHost(baseUrl)
                .setPath(String.format("%s/%d", FACTURA_URL_PATH, docId))
                .build();
        } catch (URISyntaxException e) {
            e.printStackTrace();
        }
        HttpPut req = new HttpPut(uri);
        try (CloseableHttpResponse response = httpClient.execute(req)) {
            return (response.getStatusLine().getStatusCode() == 200);
        }
        catch (IOException e) {
            e.printStackTrace();
        }
        return false;
    }

    @Override
    public Usuario authenticate(String username, String password) {
        try {
            URI uri = new URIBuilder().setScheme("http")
                    .setHost(baseUrl)
                    .setPath(LOGIN_URL).build();
            HttpPost req = new HttpPost(uri);
            req.setConfig(timeoutConfig);
            NameValuePair[] params = new NameValuePair[]{
                new BasicNameValuePair("username", username),
                new BasicNameValuePair("password", password),
            };
            req.setEntity(new UrlEncodedFormEntity(Arrays.asList(params)));
            try (CloseableHttpResponse response = httpClient.execute(req)) {
                HttpEntity entity = response.getEntity();
                String result = streamToString(entity.getContent());
                System.out.println(result);
                JsonObject obj = new Gson().fromJson(result, JsonObject.class);
                boolean status = obj.get("status").getAsBoolean();
                if (status) {
                    Usuario user = new Usuario();
                    user.setNombre(username);
                    user.setAlmacenId(obj.get("bodega_factura_id").getAsInt());
                    user.setLastFactura(obj.get("last_factura").getAsInt());
                    return user;
                }

            } catch (IOException e) {
                e.printStackTrace();
            }
        } catch (URISyntaxException | UnsupportedEncodingException e) {
            e.printStackTrace();
        }
        return null;
    }

    public Item getItemFromBarcode(String barcode) {
        try {
            URI uri = new URIBuilder().setScheme("http")
                .setHost(baseUrl)
                .setPath(BARCODE_PATH + "/" + barcode).build();
            String content = getUrl(uri);
            if (content == null) {
                return null;
            }
            Item result = gson.fromJson(content, Item.class);
            result.setCantidad(result.getCantidad() * 1000);
            return result;
        }
        catch (URISyntaxException e) {
            e.printStackTrace();
            return null;
        }
    }

    private String getUrl(URI uri) {
        HttpGet req = new HttpGet(uri);
        req.setConfig(timeoutConfig);
        try (CloseableHttpResponse response = httpClient.execute(req)) {
            HttpEntity entity = response.getEntity();
            if (response.getStatusLine().getStatusCode() == 200) {
                return streamToString(entity.getContent());
            }
        }
        catch (IOException e) {
        }
        return null;
    }
}

