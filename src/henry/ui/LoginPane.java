package henry.ui;

import static henry.Helpers.streamToString;
import henry.api.FacturaInterface;
import henry.api.FacturaInterfaceRest;
import henry.model.Documento;
import henry.model.Usuario;
import henry.printing.FacturaPrinter;
import henry.printing.Config;
import henry.printing.GenericPrinter;
import henry.printing.MinoristaPrinter;
import net.miginfocom.swing.MigLayout;

import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JTextField;
import javax.swing.JComboBox;
import javax.swing.border.EmptyBorder;
import javax.swing.SwingUtilities;
import java.awt.EventQueue;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.FileNotFoundException;
import java.io.IOException;

@SuppressWarnings("serial")
public class LoginPane extends JPanel implements ActionListener{

    static final String CONFIG_PATH = "config.json";
    private JLabel message;
    private JTextField user;
    private JPasswordField pass;
    private Runnable nextWindow;
    private Documento doc;
    private JComboBox serverbox;
    private JComboBox almacenbox;
    private String configpath;
    private static final String[] SERVER_OPTS = new String[] {
        "192.168.0.23", "localhost:8080"
    };
    private static final String[] ALMACEN_OPTS = new String[] {
        "quinal", "bodega", "corpesut"
    };
    /**
     * Create the panel.
     */
    public LoginPane(String configpath) {
        setBorder(new EmptyBorder(5, 5, 5, 5));
        setLayout(new MigLayout("", "[100][200]", ""));

        message = new JLabel();

        this.configpath = configpath == null ? CONFIG_PATH : configpath;

        JLabel userLabel = new JLabel("Usuario: ");
        JLabel passLabel = new JLabel("Clave: ");

        JLabel serverLabel = new JLabel("Servidor: ");
        JLabel almacenLabel = new JLabel("Vendido por: ");


        serverbox = new JComboBox(SERVER_OPTS);
        almacenbox = new JComboBox(ALMACEN_OPTS);

        user = new JTextField();
        pass = new JPasswordField();
        
        add(userLabel);
        add(user, "wrap, width :200:");
        add(passLabel);
        add(pass, "wrap, width :200:");

        add(serverLabel);
        add(serverbox, "wrap, width :200:");
        add(almacenLabel);
        add(almacenbox, "wrap, width :200:");
        
        JButton login = new JButton("Ingresar");
        add(login);
        add(message);
        
        login.addActionListener(this);

    }

    @Override
    public void actionPerformed(ActionEvent e) {
        FacturaInterface api = new FacturaInterfaceRest(
                serverbox.getSelectedItem().toString());
        String username = user.getText();
        String password = new String(pass.getPassword());
        Usuario usuario = api.authenticate(username, password);
        if (usuario == null) {
            message.setText("Usuario o clave equivocado");
            user.setText("");
            pass.setText("");
            return;
        }
        System.out.println(almacenbox.getSelectedItem());
        System.out.println(serverbox.getSelectedItem());
        int almacenId = almacenbox.getSelectedIndex();
        System.out.println("index " + serverbox.getSelectedIndex());


        GenericPrinter printer;
        Config config;
        try (InputStream stream = new FileInputStream(configpath)) {
            config = Config.getConfigFromJson(streamToString(stream));
            if (config.isMatrixPrinter()) {
                printer = new MinoristaPrinter(config);
                System.out.println("menorista printer");
            }
            else {
                printer = new FacturaPrinter(config);
                System.out.println("factura printer");
            }
        } 
        catch (FileNotFoundException exception) {
            throw new RuntimeException(exception);
        }
        catch(IOException exception) {
            throw new RuntimeException(exception);
        }
        FacturaVentana factura = new FacturaVentana(api, almacenId, usuario, printer, config.isFactura());
        factura.setVisible(true);
        SwingUtilities.getWindowAncestor(this).dispose();
    }
}
