package henry.ui;

import static henry.Helpers.displayAsMoney;

import henry.api.FacturaInterface;
import henry.model.Documento;
import henry.model.Usuario;
import henry.model.Producto;
import henry.model.Cliente;
import henry.api.SearchEngine;
import henry.printing.GenericPrinter;
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
import java.util.List;

@SuppressWarnings("serial")
public class FacturaVentana extends JFrame {
    private JPanel panel;

    private Documento documento;
    
    private ItemContainer contenido;
    private JLabel numeroLabel;
    private JTextField pago;
    private JTextField pedidoField;
    private ClientePanel cliente;

    final private FacturaInterface api;
    private int almacenId;
    Usuario usuario;
    
    private int numero = 0;
    private static final String []
            PAGO_LABEL = {"efectivo", "tarjeta", "cheque", "deposito", "credito", "varios"};
    private String formaPago = "efectivo";
    private GenericPrinter printer;

    private SearchDialog<Producto> prodSearchDialog = 
        new SearchDialog<>(new SearchEngine<Producto>() {
            @Override
            public List<Producto> search(String prefijo) {
                return api.buscarProducto(prefijo);
            }

            @Override
            public String toString() {
                return "Producto";
            }
        });
    private SearchDialog<Cliente> clienteSearchDialog = 
        new SearchDialog<>(new SearchEngine<Cliente>() {
            @Override
            public List<Cliente> search(String prefijo) {
                return api.buscarCliente(prefijo);
            }

            @Override
            public String toString() {
                return "Cliente";
            }
        });

    private SimpleDialog dialog = new SimpleDialog();

    private boolean isFactura;

    public FacturaVentana(
            final FacturaInterface api, 
            int almacenId, 
            Usuario usuario, 
            GenericPrinter printer,
            boolean isFactura) {
        this.api = api;
        this.almacenId = almacenId;
        this.usuario = usuario;
        this.printer = printer;
        this.documento = new Documento();
        this.isFactura = isFactura;

        ItemPanelFactory itemFactory = new ItemPanelFactory(api, prodSearchDialog);

        System.out.println("creating itemcontainer");
        panel = new JPanel();
        getContentPane().add(panel);
        panel.setLayout(new MigLayout("", "[][][][]",""));
        
        //mostrador de numero de factura;
        numero = usuario.getLastFactura();
        numeroLabel = new JLabel();
        
        System.out.println("creating itemcontainer");
        contenido = new ItemContainer(true, documento, itemFactory);
        cliente = new ClientePanel(this.api, clienteSearchDialog, contenido);

        JButton buscarPorCliente = new JButton("Buscar por Cliente");
        pedidoField = new JTextField();
        
        //poner llamador de nota de pedido
        panel.add(new JLabel("No. de Pedido:"));
        panel.add(pedidoField, "width :300:");
        
        //poner boton q busca por cliente
        panel.add(buscarPorCliente);
        
        setTitle("Nota de Pedido");
        String displayFacturaText = "";
        if (isFactura) {
            setTitle("Orden de Despacho");
            //poner numero de factura
            panel.setBackground(Color.RED);
            displayFacturaText = "No. de Factura: ";
            numeroLabel.setText("" + numero);
        }
        panel.add(new JLabel(displayFacturaText));
        panel.add(numeroLabel, "cell 3 0, wrap, width :100:");
        
        panel.add(cliente, "wrap, span");
        panel.add(contenido, "wrap, span");
        JButton aceptar = new JButton("aceptar");
        JButton cancelar = new JButton("cancelar");
        
        
        //Formas de Pago
        ButtonGroup group = new ButtonGroup();
        JPanel buttons = new JPanel();
        buttons.setLayout(new MigLayout());
        ActionListener formaDePagoListener = new FormaDePagoListener();
        for (int i = 0; i < PAGO_LABEL.length; i++) {
            JRadioButton rad = new JRadioButton(PAGO_LABEL[i]);
            if (i == 0) {
                rad.setSelected(true);
            }
            final int index = i;
            rad.addActionListener(formaDePagoListener);
            
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
        

        setBounds(100, 100, 735, 655);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

        // actions
        aceptar.addActionListener(new AceptarActionLister());
        cancelar.addActionListener(new CancelarActionListener());
        pedidoField.addActionListener(new LoadPedidoActionListener());
    }

    // This class is called when we load a note using it's id
    private class LoadPedidoActionListener implements ActionListener {

        @Override
        public void actionPerformed(ActionEvent e) {
            Documento doc = null;
            try {
                doc = api.getPedidoPorCodigo(pedidoField.getText());
            } catch (FacturaInterface.NotFoundException e1) {
                pedidoField.requestFocus();
                pedidoField.selectAll();
                contenido.setMessage("Nota de pedido no encontrado");
                return;
            }
            contenido.clear();
            cliente.clear();
            cliente.bindCliente(doc.getCliente());
            documento = doc;
            contenido.update(doc);
        }
    }

    // This class is used to handle the event of clicking "aceptar"
    private class AceptarActionLister implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            Documento doc = contenido.getDocumento();
            doc.setCliente(cliente.getCliente());
            doc.setUser(usuario);
            doc.setFormaPago(formaPago);
            if (isFactura) {
                if (!validateFactura(doc)) {
                    return;
                }
                doc.setCodigo(numero);
                if (api.guardarDocumento(doc, isFactura) > 0) {
                    if (printer.printFactura(doc)) {
                        numero++;
                        numeroLabel.setText("" + numero);
                    }
                    clear();
                } 
                else {
                    contenido.setMessage("Factura no se guardo");
                }
            }
            else {
                int codigo = api.guardarDocumento(doc, isFactura);
                dialog.setText("El codigo es " + codigo);
                dialog.setVisible(true);
                clear();
                contenido.setMessage("Nota de pedido que se hizo fue " + codigo);
            }
        }
    }

    private boolean validateFactura(Documento doc) {
        // check that has cliente
        if (doc.getCliente() == null) {
            dialog.setText("Por favor ingrese cliente");
            dialog.setVisible(true);
            return false;
        }
        if (formaPago.equals("efectivo")) {
            int pagado;
            try {
                pagado = (int) Math.round(
                        Double.parseDouble(pago.getText()) * 100);
                doc.setPagado(pagado);
            } 
            catch(NumberFormatException exception) {
                dialog.setText("Ingrese un numero \nen el valor pagado");
                dialog.setVisible(true);
                return false;
            }
            int total = doc.getTotal();
            if (pagado < total) {
                dialog.setText("El valor pagado debe\nser mayor al total");
                dialog.setVisible(true);
                return false;
            }
            dialog.setText("El cambio es \n" + displayAsMoney(pagado - total));
            dialog.setVisible(true);
        }
        return true;
    }

    private void clear() {
        contenido.clear();
        cliente.clear();
    }

    private class CancelarActionListener implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            FacturaVentana.this.clear();
        }
    }

    private class FormaDePagoListener implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            if (e.getSource() instanceof JRadioButton) {
                JRadioButton button = (JRadioButton) e.getSource();
                String text = button.getText();
                formaPago = text;
            }
        }
    }
}
