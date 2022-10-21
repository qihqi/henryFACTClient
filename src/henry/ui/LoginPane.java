package henry.ui;

import henry.api.FacturaInterfaceRest;
import henry.model.Usuario;
import henry.printing.Config;
import henry.printing.FacturaPrinter;
import henry.printing.GenericPrinter;
import henry.printing.MinoristaPrinter;
import henry.printing.MatrixPrinter;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;
import javax.swing.border.EmptyBorder;
import net.miginfocom.swing.MigLayout;

import static henry.Helpers.streamToString;

@SuppressWarnings("serial")
class LoginPane extends JPanel implements ActionListener{

    private static final String CONFIG_PATH = "config.json";
    private JLabel message;
    private JTextField user;
    private JPasswordField pass;
    private JComboBox<String> serverbox;
    private Config config;
    /**
     * Create the panel.
     */
    public LoginPane(String configpath) {
        setBorder(new EmptyBorder(5, 5, 5, 5));
        setLayout(new MigLayout("", "[100][200]", ""));

        message = new JLabel();

        String configpath1 = configpath == null ? CONFIG_PATH : configpath;

        JLabel userLabel = new JLabel("Usuario: ");
        JLabel passLabel = new JLabel("Clave: ");

        JLabel serverLabel = new JLabel("Servidor: ");
        config = loadConfig(configpath1);
        serverbox = new JComboBox<>(config.getServersOpts());

        user = new JTextField();
        pass = new JPasswordField();
        
        add(userLabel);
        add(user, "wrap, width :200:");
        add(passLabel);
        add(pass, "wrap, width :200:");

        add(serverLabel);
        add(serverbox, "wrap, width :200:");

        JButton login = new JButton("Ingresar");
        add(login);
        add(message);
        
        login.addActionListener(this);
    }

    private Config loadConfig(String configpath) {
        try (InputStream stream = new FileInputStream(configpath)) {
            return Config.getConfigFromJson(streamToString(stream));
        } catch(IOException exception) {
            throw new RuntimeException(exception);
        }
    }

    @Override
    public void actionPerformed(ActionEvent e) {
        //almacenId in server uses index starting from 1
        String serverIp = serverbox.getSelectedItem().toString();

        String username = user.getText();
        String password = new String(pass.getPassword());
        FacturaInterfaceRest api = new FacturaInterfaceRest(serverIp);
        Usuario usuario = api.authenticate(username, password);
        if (usuario == null) {
            message.setText("Usuario o clave equivocado");
            user.setText("");
            pass.setText("");
            return;
        }
        api.setAlmacenId(usuario.getAlmacenId());
        System.out.println(serverbox.getSelectedItem());
        System.out.println("index " + serverbox.getSelectedIndex());
        GenericPrinter printer = null;
        MatrixPrinter mprinter = null;
        if (config.isSmallMatrixPrinter()) {
            mprinter = new MatrixPrinter(api);
        } else if (config.isMatrixPrinter()) {
            printer = new MinoristaPrinter(config);
            System.out.println("menorista printer");
        }
        else {
            printer = new FacturaPrinter(config);
            System.out.println("factura printer");
        }
        FacturaVentana factura = new FacturaVentana(
                api, usuario, printer, mprinter, config.isFactura());
        factura.setVisible(true);
        SwingUtilities.getWindowAncestor(this).dispose();
    }
}
