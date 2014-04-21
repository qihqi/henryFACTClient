package henry.ui;

import javax.swing.*;
import java.awt.*;

@SuppressWarnings("serial")
public class Main extends JFrame {
    private LoginPane contentPane;
    private JPasswordField pass;
    private JTextField user;
    private JLabel message;

    public static void main(String[] args) {
        EventQueue.invokeLater(new Runnable() {
            public void run() {
                try {
                    //mapEnterToActionEvent();
                    //    registerHotkeys();
                    Main frame = new Main();
                    frame.setVisible(true);
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        });
    }

    public Main() {
        setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
        setBounds(100, 100, 393, 172);
        contentPane = new LoginPane(new Runnable () {
            @Override
            public void run() {
                FacturaVentana.main(null);
            }
        });

        //aqui le puse el listener
        setContentPane(contentPane);
    }
}
