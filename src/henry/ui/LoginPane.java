package henry.ui;

import henry.api.FacturaInterface;
import henry.model.Documento;
import henry.model.Usuario;
import net.miginfocom.swing.MigLayout;

import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JTextField;
import javax.swing.border.EmptyBorder;
import java.awt.EventQueue;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.nio.charset.Charset;

@SuppressWarnings("serial")
public class LoginPane extends JPanel implements ActionListener{

    private JLabel message;
    private JTextField user;
    private JPasswordField pass;
    private Runnable nextWindow;
    private Documento doc;
    /**
     * Create the panel.
     */
    public LoginPane(Documento doc, Runnable next) {
        this.doc = doc;
        nextWindow = next;
        
        setBorder(new EmptyBorder(5, 5, 5, 5));
        setLayout(new MigLayout("", "[100][200]", ""));
        
        message = new JLabel();
        
        JLabel userLabel = new JLabel("Usuario: ");
        JLabel passLabel = new JLabel("Clave: ");
        
        user = new JTextField();
        pass = new JPasswordField();
        
        add(userLabel);
        add(user, "wrap, width :200:");
        add(passLabel);
        add(pass, "wrap, width :200:");
        
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
        doc.setUser(usuario);
        EventQueue.invokeLater(nextWindow);
    }
}
