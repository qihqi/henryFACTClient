package henry;

/**
 * Created by han on 12/15/13.
 */
import java.awt.event.FocusAdapter;
import java.awt.event.FocusEvent;
import java.math.BigDecimal;
import java.io.InputStream;
import java.util.Scanner;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;

public class Helpers {
    /** Imprimir centavos como dolares en 2 decimales
     *
     * @param cents centavos
     * @return lo equivalente en dolares
     */
    public static String displayAsMoney(int cents) {
        return String.format("%d.%02d", cents / 100, cents % 100);
    }

    public static String displayMilesimas(int milesimas) {
        int enteros = milesimas / 1000;
        int decimales = milesimas % 1000;
        if (decimales == 0) {
            return String.format("%d", enteros);
        }
        int digitos = 3;
        while (decimales % 10 == 0) {
            decimales = decimales / 10;
            digitos--;
        }
        String formatter = "%d.%0" + digitos + "d";
        return String.format(formatter, enteros, decimales);
    }

    public static int parseMilesimasFromString(String s) {
        BigDecimal d = new BigDecimal(s).multiply(new BigDecimal(1000));
        return d.intValue();
    }
    public static int parseCentavosFromString(String s) {
        BigDecimal d = new BigDecimal(s).multiply(new BigDecimal(1000));
        return d.intValue();
    }
    public static String streamToString(InputStream stream) {
        Scanner scanner = new Scanner(stream).useDelimiter("\\A");
        return scanner.hasNext() ? scanner.next() : null;
    }

    //This class gives TextField ability to select all text
    //when gain focus
    public static class HighlightFocusListener extends FocusAdapter {
        private JTextField text;
        public HighlightFocusListener(JTextField t) {
            text = t;
        }
        @Override
        public void focusGained(FocusEvent e) {
            SwingUtilities.invokeLater(new Runnable() {
                @Override
                public void run() {
                    text.selectAll();
                }
            });
        }
    }
}
