package henry.printing;

import henry.model.Documento;

import javax.print.Doc;
import javax.print.DocFlavor;
import javax.print.DocPrintJob;
import javax.print.PrintService;
import javax.print.PrintException;
import javax.print.PrintServiceLookup;
import javax.print.SimpleDoc;

public class MinoristaPrinter extends GenericPrinter{

    private char[][] data;

    public MinoristaPrinter(Config config) {
        super(config);
        double[] tamano = config.getImpression().getTamano();
        data = new char[(int) tamano[1]][(int) tamano[0]];
    }

    private byte[] getBytesFromMatrix(char[][] data) {
        StringBuffer buffer = new StringBuffer();
        for (char[] x : data) {
            buffer.append(x).append('\n');
        }
        String content = buffer.toString();
        System.out.println(content);
        return content.getBytes();
    }

    @Override
    public boolean printFactura(Documento documento) {
        System.out.println("MinoristaPrinter::printFactura");

        // clean bytes before printing
        for (char[] x : data) {
            for (int i = 0; i < x.length; i++) {
                x[i] = ' ';
            }
        }
        setDocumento(documento);
        PrintService defaultprinter = PrintServiceLookup.lookupDefaultPrintService();
        DocPrintJob job = defaultprinter.createPrintJob();
        DocFlavor  flavour = DocFlavor.BYTE_ARRAY.AUTOSENSE;
        printTitle();
        printClient(documento.getCliente());
        printContent(0, 1);  // current page number, width of a character
        printValues();
        byte[] b = getBytesFromMatrix(data);
        Doc doc = new SimpleDoc(b, flavour, null);
        try {
            job.print(doc, null);
            return true;
        } catch (PrintException e1) {
            e1.printStackTrace();
        }
        return false;
    }

    @Override
    public void printContent(String content, double x, double y, double maxLength) {
        int posx = (int) x;
        int posy = (int) y;
        if ( posy >= data.length) {
            posy = data.length - 1;
        }
        int contentLength = content.length() > maxLength ? (int) maxLength : content.length();
        int length = (contentLength + posx >= data[posy].length) ?
                data[posy].length - posx - 1 : contentLength;
        System.arraycopy(content.toCharArray(), 0, data[posy], posx, length);
    }
}
