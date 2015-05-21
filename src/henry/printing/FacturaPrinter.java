package henry.printing;

import henry.printing.Config.ImpressionConfig;
import henry.model.Documento;
import henry.model.Cliente;
import henry.model.Item;

import lombok.Setter;

import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.print.Book;
import java.awt.print.PageFormat;
import java.awt.print.Paper;
import java.awt.print.Printable;
import java.awt.print.PrinterException;
import java.awt.print.PrinterJob;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Date;
import java.text.SimpleDateFormat;

public class FacturaPrinter implements Printable  {

    @Setter
    private Documento documento;
    private Config config;
    private Font font;
    private SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd");
    
    public FacturaPrinter(Config config) {
        this.config = config;
        font = new Font(config.getFontFamily(),
                        Font.PLAIN, 
                        config.getFontSize());
    }

    public boolean printFactura() {
        PrinterJob job = PrinterJob.getPrinterJob();
        job.setPrintable(this);
        boolean ok = job.printDialog();
        System.out.println("printing");
        if (ok) {
            try {
                setPaperSize(job);
                job.print();
            } catch (PrinterException e) {
                e.printStackTrace();
                return false;
            }
        }
        return true;
    }
    
    @Override
    public int print(Graphics g, PageFormat fmt, int page)
            throws PrinterException 
    {
        int totalPages = 
              (documento.getItems().size() - 1) 
            / config.getImpression().getLineas() 
            + 1;
        if (page >= totalPages ) //>= porq es 0 indexed
            return NO_SUCH_PAGE;
        g.setFont(font);
        int lineWidth = g.getFontMetrics(font).getHeight();
        Graphics2D g2d = (Graphics2D)g;
        g2d.translate(fmt.getImageableX(), fmt.getImageableY());
        
        printTitle(g2d, documento.getCodigo());
        printClient(g2d, documento.getCliente());
        /*
        if (printContent(g2d, page, lineWidth)) {// ya no hay mas paginas
            printValues(g2d);
            printFirma(g2d);
        }

        */
       
        return PAGE_EXISTS;
    }

    private void printTitle(Graphics2D g2d, int codigo) {
        if (!config.isFacturaBlanco()) {//titulos ya estan impresas
            return;
        }
        double[] titlePos = config.getImpression().getTitle();
        String value = (config.isFactura() ? "Orden De Despacho: " :
                                             "Nota De Pedido: ") + codigo;
        g2d.drawString(value, (float) titlePos[0], (float) titlePos[1]);
        
    }

    private void drawElement(Graphics2D g2d,
            double[] pos, double[] delta, String label, String content) {
        if (content == null) {
            content = "";
        }
        if (config.isFacturaBlanco()) {
            content = String.format("%s: %s", label.toUpperCase(), content);
            pos[0] += delta[0];
            pos[1] += delta[1];
        }
        g2d.drawString(content, (float) pos[0], (float) pos[1]);
    }
    
    private void printClient(Graphics2D g2d, Cliente cliente) {
        int x = 0;
        int y = 0;
        ImpressionConfig impConfig = config.getImpression();

        drawElement(g2d, impConfig.getRuc(), impConfig.getRucDelta(),
                    "RUC", cliente.getCodigo());
        drawElement(g2d, impConfig.getCliente(), impConfig.getClienteDelta(),
                    "cliente", cliente.toString());
        drawElement(g2d, impConfig.getTelf(), impConfig.getTelfDelta(),
                    "telf", cliente.getTelefono());
        String direccion = cliente.getDireccion();
        if (direccion == null) {
            direccion = "";
        }
        if (direccion.length() > 20) {
            direccion = direccion.substring(0, 20);
        }
        drawElement(g2d, impConfig.getDireccion(), impConfig.getDireccionDelta(),
                    "direccion", direccion);
        drawElement(g2d, impConfig.getFecha(), impConfig.getFechaDelta(),
                    "fecha", format.format(new Date()));
        
        if (config.isFacturaBlanco()) {
            g2d.drawLine(x, (int) y, x+500,(int)y);
        }
    }
/*
    private boolean printContent(Graphics2D g2d, int page, int lineWidth) {
        int start = page * lines;
                
        int end;
        boolean endOfPage;
        if (start + lines > items.size()) {
            end = items.size(); 
            endOfPage = true;
        }
        else { 
            end = (start + lines);
            endOfPage = false;
        }
        double [] pos = Config.getConfig().getImpresionPos("contenido");
        
        final double LEFT_EDGE = pos[0];
        System.out.println(lineWidth);
        List<Item> items = documento.getItem();
        for (int i = start; i < end; i++) {
            for (int j = 0; j < 5; j++) {
                g2d.drawString(getItemValue(j, items.get(i)), 
                               (float) pos[0], (float) pos[1]);
                if (j < 4)
                    pos[0] += spacing[j];
            }
            pos[0] = LEFT_EDGE;
            pos[1] += lineWidth;
            lastItemY = (float) pos[1];
        }
        return endOfPage;
    }
    
    private static String getItemValue(int pos, Item v) {
        switch (pos) {
        case 0:
                return v.getProducto().getCodigo();
        case 1:
            return displayMilesimas(v.getCantidad);
        case 2:
            String nombre = v.getProducto().getNombre();
            if (nombre > 55)
                return shorten(nombre);
            return nombre;
        case 3:
            return displayAsMoney(v.getPrecio());
        case 4:
            return displayAsMoney(v.getTotal());
        }
        return null;
    }
    
    private static String shorten(String s) {
        String [] words = s.split("[ ]+");
        String result = "";
        for (String w : words) {
            if (w.length() > 6)
                result += w.substring(0, 5);
            else 
                result += w;
            result += ' ';
    }
        return result;
    }
    
    private void printValues(Graphics2D g2d) {
        String [] titles = { "bruto", "neto", "desc", "iva", "total" };
        String [] labels = {"Valor Bruto", "Valor Neto", "Descuento", "IVA", "Total"};
        String [] values = { 
            displayAsMoney(documento.getSubtotal()), //valor bruto = neto + desc 
            displayAsMoney(documento.getTotalNeto()),
            displayAsMoney(documento.getDescuento()),
            displayAsMoney(documento.getIva()), //iva = total - subtotal
            displayAsMoney(documento.getTotal())};
        float realPos = 0;
        int linePos = (int) Config.getConfig().getImpresionPos("direccion")[0]-60;
        g2d.drawLine(linePos, (int) lastItemY + 10, linePos + 500, (int) lastItemY + 10);
        for (int i = 0; i < titles.length; i++) {
            double [] pos;
            pos = Config.getConfig().getImpresionPos(titles[i]);

            if (facturaBlanco) {
                
                if (realPos == 0) 
                    realPos = lastItemY + 20;
                else 
                    realPos += 15;    
                
                pos[1] = realPos;
                g2d.drawString(labels[i] + ": ", (float) pos[0] - libre, (float) pos[1]); 
            }    
            g2d.drawString(values[i], (float) pos[0], (float) pos[1]); 
        }
        
    }
    
    private void printFirma(Graphics2D g2d) {
        String [] label = {"Despachador", "Verificador", "Seguridad"};
        if (Config.getConfig().isFactura())
            label[0] = "Cliente";
        for (int i = 0; i < label.length; i++){
            String key = "firma" + (1+i);
            double [] pos = Config.getConfig().getImpresionPos(key);
            g2d.drawLine((int) pos[0], (int) pos[1], (int) pos[0] + 120, (int) pos[1]);
            g2d.drawString(label[i], (float) pos[0], (float) pos[1] + 20);
        }
    }
    
    //print the titles
    
    */
    
    public void setPaperSize(PrinterJob job) {
        
        if (config.isFacturaBlanco()) {
            return;
        }
        
        double[] size = config.getImpression().getTamano();
        PageFormat fmt = job.defaultPage();
        Paper paper = fmt.getPaper();
        paper.setImageableArea(0, 0, (float) size[0], size[1]);
        fmt.setPaper(paper);
        // fmt = job.pageDialog(fmt);
        Book book = new Book();
        book.append(this, fmt);
        job.setPageable(book);
    }
}
