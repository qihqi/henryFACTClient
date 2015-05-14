package henry.ui;

import henry.api.FacturaInterface;
import henry.model.Documento;
import henry.model.Item;
import net.miginfocom.swing.MigLayout;

import javax.swing.ButtonGroup;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JRadioButton;
import javax.swing.JTextField;
import java.awt.Color;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

@SuppressWarnings("serial")
public class FacturaVentana extends JFrame {
    private JPanel panel;

    private Documento documento;
    
    private ItemContainer contenido;
    private JLabel numeroLabel;
    private JTextField pago;
    private JTextField pedidoField;
    private ClientePanel cliente;
    
    private long numero = 0;
    private static final String []
            PAGO_LABEL = {"efectivo", "tarjeta", "cheque", "deposito", "credito", "varios"};
//    private static final String [] 
//            FORMAS_DE_PAGO = {Factura.EFECTIVO,
//                              Factura.TARGETA_CREDITO,
//                              Factura.CHEQUE,
//                              Factura.DEPOSITO,
//                              Factura.CREDITO,
//                              Factura.VARIOS};
    private String formaPago = "";//Factura.EFECTIVO;
    /**
     * Create the application.
     */
    public FacturaVentana(Documento documento) {
        this.documento = documento;
        System.out.println("creating itemcontainer");
        panel = new JPanel();
        getContentPane().add(panel);
        panel.setLayout(new MigLayout("", "[][][][]",""));
        
        //mostrador de numero de factura;
        
        numero = documento.getUser().getLastFactura();
        numeroLabel = new JLabel("" + numero);
        
        System.out.println("creating itemcontainer");
        contenido = new ItemContainer(true);
        cliente = new ClientePanel(documento.getCliente());

        JButton buscarPorCliente = new JButton("Buscar por Cliente");
        pedidoField = new JTextField();
        
        //poner llamador de nota de pedido
        panel.add(new JLabel("No. de Pedido:"));
        panel.add(pedidoField, "width :300:");
        
        //poner boton q busca por cliente
        panel.add(buscarPorCliente);
        
        //poner numero de factura
        panel.add(new JLabel("No. de Factura: "));
        panel.add(numeroLabel, "cell 3 0, wrap, width :100:");
        
        panel.add(cliente, "wrap, span");
        panel.add(contenido, "wrap, span");
        JButton aceptar = new JButton("aceptar");
        JButton cancelar = new JButton("cancelar");
        
        
        //Formas de Pago
        ButtonGroup group = new ButtonGroup();
        JPanel buttons = new JPanel();
        buttons.setLayout(new MigLayout());
        for (int i = 0; i < PAGO_LABEL.length; i++) {
            JRadioButton rad = new JRadioButton(PAGO_LABEL[i]);
            if (i == 0) 
                rad.setSelected(true);
            final int index = i;
            rad.addActionListener(new ActionListener() {
                @Override
                public void actionPerformed(ActionEvent arg0) {
        //            formaPago = FORMAS_DE_PAGO[index];
                }
            });
            
            buttons.add(rad);
            group.add(rad);
        }
        
        JLabel label = new JLabel("A Pagar");
        pago = new JTextField();
        
        panel.add(label, "width :100:");
        panel.add(pago, "width :300:");
        panel.add(aceptar, "width :100:");
        panel.add(cancelar, "width :100:, wrap");
        panel.add(buttons, "span, wrap");
    
        JLabel hotkeys = new JLabel("F5=Buscar Cliente  F6=Buscar Producto " +
                "F7=Pagar  F8=Aceptar  F9=Cancelar");
        panel.add(hotkeys, "span");
        
        setTitle("Orden de Despacho");
        panel.setBackground(Color.RED);
        setBounds(100, 100, 735, 655);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

        // actions
        aceptar.addActionListener(new AceptarActionLister());
        cancelar.addActionListener(new CancelarActionListener());
        pedidoField.addActionListener(new LoadPedidoActionListener());
    }

    private class LoadPedidoActionListener implements ActionListener {

        @Override
        public void actionPerformed(ActionEvent e) {
            Documento doc = FacturaInterface.INSTANCE.getPedidoPorCodigo(pedidoField.getText());
            contenido.clear();
            cliente.setCliente(doc.getCliente());
            for (Item i : doc.getItems()) {
                i.addListener(doc);
            }
            documento = doc;
            contenido.update(doc);
        }
    }

    private class AceptarActionLister implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            Documento doc = contenido.getDocumento();
            // doc.setCliente(cliente.getCliente());
             //System.out.println("" + cliente.getCliente() == null);
            FacturaInterface.INSTANCE.guardarDocumento(contenido.getDocumento());
        }
    }
    private class CancelarActionListener implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            contenido.clear();
        }
    }
}
