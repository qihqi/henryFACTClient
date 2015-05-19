package henry.ui;

import henry.api.FacturaInterface;
import henry.api.FacturaInterfaceRest;
import henry.model.Documento;
import henry.model.Usuario;
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

@SuppressWarnings("serial")
public class LoginPane extends JPanel implements ActionListener{

    private JLabel message;
    private JTextField user;
    private JPasswordField pass;
    private Runnable nextWindow;
    private Documento doc;
    private JComboBox serverbox;
    private JComboBox almacenbox;
    private static final String[] SERVER_OPTS = new String[] {"192.168.0.23"};
    private static final String[] ALMACEN_OPTS = new String[] {
        "quinal", "bodega", "corpesut"
    };
    /**
     * Create the panel.
     */
    public LoginPane() {
        setBorder(new EmptyBorder(5, 5, 5, 5));
        setLayout(new MigLayout("", "[100][200]", ""));

        message = new JLabel();
        
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
        String username = user.getText();
        String password = new String(pass.getPassword());
        Usuario usuario = FacturaInterface.INSTANCE.authenticate(username, password);
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
        FacturaInterface api = new FacturaInterfaceRest(
                serverbox.getSelectedItem().toString());
        FacturaVentana factura = new FacturaVentana(api, almacenId, usuario);
        factura.setVisible(true);
        SwingUtilities.getWindowAncestor(this).dispose();
    }
}
