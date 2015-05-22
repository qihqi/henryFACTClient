import henry.model.Documento;
import henry.printing.GenericPrinter;

public class MinoristaPrinter extends GenericPrinter{
    @Override
    public boolean printFactura(Documento documento) {
        return false;
    }

    @Override
    public void printContent(String content, double x, double y) {

    }
}
