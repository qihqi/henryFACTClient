package henry.printing;

import henry.model.Documento;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.print.Book;
import java.awt.print.PageFormat;
import java.awt.print.Paper;
import java.awt.print.Printable;
import java.awt.print.PrinterException;
import java.awt.print.PrinterJob;

public class FacturaPrinter extends GenericPrinter implements Printable  {

    private Font font;
    private Graphics2D g2d;

    public FacturaPrinter(Config config) {
        super(config);
        font = new Font(config.getFontFamily(),
                        Font.PLAIN, 
                        config.getFontSize());
    }

    @Override
    public int print(Graphics g, PageFormat fmt, int page)
            throws PrinterException 
    {
        g2d = (Graphics2D) g;
        int totalPages = 
              (documento.getItems().size() - 1) 
            / config.getImpression().getLineas() 
            + 1;
        if (page >= totalPages ) { //>= porq es 0 indexed
            return NO_SUCH_PAGE;
        }
        g.setFont(font);
        int lineWidth = g.getFontMetrics(font).getHeight();
        g2d.translate(fmt.getImageableX(), fmt.getImageableY());
        
        printTitle();
        printClient(documento.getCliente());
        int linestart = (int) config.getImpression().getDireccion()[1] + 10;
        g2d.drawLine(0, linestart, 500, linestart);
        if (printContent(page, lineWidth)) {// ya no hay mas paginas
            printValues();
            int totalLine = (int) (config.getImpression().getBruto()[1] - 10);
            g2d.drawLine(0, totalLine, 500, totalLine);
            printFirma();
        }
        return PAGE_EXISTS;
    }

    @Override
    public boolean printFactura(Documento documento) {
        setDocumento(documento);
        PrinterJob job = PrinterJob.getPrinterJob();
        job.setPrintable(this);
        boolean ok = job.printDialog();
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
    public void printContent(String content, double x, double y) {
        g2d.drawString(content, (float) x, (float) y);
    }

    private void setPaperSize(PrinterJob job) {
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
