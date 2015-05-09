package henry.ui;

import henry.model.Documento;

import javax.swing.JFrame;
import java.awt.EventQueue;

@SuppressWarnings("serial")
public class Main extends JFrame {
    private LoginPane contentPane;
    private FacturaVentana factura;
    private Documento documento;

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
        System.out.println("main is exiting");
    }

    public Main() {
        setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
        setBounds(100, 100, 393, 172);

        documento = new Documento();
        factura = new FacturaVentana(documento);
        final FacturaVentana fact = factura;
        final Main self = this;
        contentPane = new LoginPane(documento, new Runnable () {
            @Override
            public void run() {
                fact.setVisible(true);
                self.dispose();
            }
        });


        //aqui le puse el listener
        setContentPane(contentPane);

        

    }
}
