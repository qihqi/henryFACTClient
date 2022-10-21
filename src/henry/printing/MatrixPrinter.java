package henry.printing;

import henry.model.Documento;
import henry.api.FacturaInterface;

import javax.print.Doc;
import javax.print.DocFlavor;
import javax.print.DocPrintJob;
import javax.print.PrintService;
import javax.print.PrintException;
import javax.print.PrintServiceLookup;
import javax.print.SimpleDoc;

public class MatrixPrinter {


    FacturaInterface api;
    public MatrixPrinter(FacturaInterface api_) {
        api = api_;
    }

    public boolean printFactura(int docId) {
        System.out.println("MatrixPrinter::printFactura");
        byte[] b = api.getPrintableInvoice(docId);

        PrintService defaultprinter = PrintServiceLookup.lookupDefaultPrintService();
        DocPrintJob job = defaultprinter.createPrintJob();
        DocFlavor  flavour = DocFlavor.BYTE_ARRAY.AUTOSENSE;
        Doc doc = new SimpleDoc(b, flavour, null);
        try {
            job.print(doc, null);
            return true;
        } catch (PrintException e1) {
            e1.printStackTrace();
        }
        return false;
    }
}
