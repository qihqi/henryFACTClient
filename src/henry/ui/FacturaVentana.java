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
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.KeyEvent;
import java.util.List;

@SuppressWarnings({"serial", "WeakerAccess"})
public class FacturaVentana extends JFrame {


    private ItemContainer contenido;
    private JLabel numeroLabel;
    private JTextField pago;
    private JTextField pedidoField;
    private ClientePanel cliente;

    final private FacturaInterface api;
    private Usuario usuario;

    private int numero = 0;
    private static final String []
            PAGO_LABEL = {"efectivo", "tarjeta", "cheque", "deposito", "credito", "varios"};
    private String formaPago = "efectivo";
    private GenericPrinter printer;

    private SimpleDialog dialog = new SimpleDialog();

    private boolean isFactura;

    public FacturaVentana(
            final FacturaInterface api,
            Usuario usuario,
            GenericPrinter printer,
            boolean isFactura) {
        this.api = api;
        this.usuario = usuario;
        this.printer = printer;
        this.isFactura = isFactura;

        SearchDialog<Producto> prodSearchDialog = new SearchDialog<>(new SearchEngine<Producto>() {
            @Override
            public List<Producto> search(String prefijo) {
                return api.buscarProducto(prefijo);
            }

            @Override
            public String toString() {
                return "Producto";
            }
        });
        ItemPanelFactory itemFactory = new ItemPanelFactory(api, prodSearchDialog);

        System.out.println("creating itemcontainer");
        JPanel panel = new JPanel();
        getContentPane().add(panel);
        panel.setLayout(new MigLayout("", "[][][][]", ""));

        //mostrador de numero de factura;
        numero = usuario.getLastFactura();
        numeroLabel = new JLabel();

        System.out.println("creating itemcontainer");
        contenido = new ItemContainer(itemFactory);
        SearchDialog<Cliente> clienteSearchDialog = new SearchDialog<>(new SearchEngine<Cliente>() {
            @Override
            public List<Cliente> search(String prefijo) {
                return api.buscarCliente(prefijo);
            }

            @Override
            public String toString() {
                return "Cliente";
            }
        });
        cliente = new ClientePanel(this.api, clienteSearchDialog, contenido);

        JButton buscarPorCliente = new JButton("");
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


        KeyboardFocusManager.getCurrentKeyboardFocusManager()
                .addKeyEventDispatcher(new HotKeyDispatcher(this, contenido, cliente));
    }

    // This class is called when we load a note using it's id
    private class LoadPedidoActionListener implements ActionListener {

        @Override
        public void actionPerformed(ActionEvent e) {
            Documento doc;
            try {
                doc = api.getPedidoPorCodigo(pedidoField.getText());
            }
            catch (FacturaInterface.NotFoundException e1) {
                pedidoField.requestFocus();
                pedidoField.selectAll();
                contenido.setMessage("Nota de pedido no encontrado");
                return;
            }
            contenido.clear();
            cliente.clear();
            cliente.bindCliente(doc.getCliente());
            contenido.update(doc);
        }
    }

    private void guardarFactura() {
        Documento doc = contenido.getDocumento();
        doc.setCliente(cliente.getCliente());
        doc.setUser(usuario);
        doc.setFormaPago(formaPago);
        if (isFactura) {
            if (!validateFactura(doc)) {
                return;
            }
            doc.setCodigo(numero);
            int id = api.guardarDocumento(doc, isFactura);
            if (id > 0) {
                if (!api.commitDocument(id)) {
                    api.commitDocument(id); // if this magically fails, retry once;
                }
                if (printer.printFactura(doc)) {
                    clear();
                    contenido.setMessage("");
                    numero++;
                    numeroLabel.setText("" + numero);
                }
            }
            else {
                contenido.setMessage("Factura no se guardo");
            }
        }
        else {
            int codigo = api.guardarDocumento(doc, false);
            if (codigo > 0) {
                dialog.setText("El codigo es " + codigo);
                dialog.setVisible(true);
                clear();
                dialog.setModalityType(Dialog.ModalityType.APPLICATION_MODAL);
                contenido.setMessage("Nota de pedido que se hizo fue " + codigo);
            }
            else {
                contenido.setMessage("Nota de pedido no fue guardada, guarde de nuevo");
            }
        }
    }

    // This class is used to handle the event of clicking "aceptar"
    private class AceptarActionLister implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            FacturaVentana.this.guardarFactura();
        }
    }

    private boolean validateFactura(Documento doc) {
        // check that has cliente
        if (doc.getCliente() == null) {
            dialog.setText("Por favor ingrese cliente");
            dialog.setVisible(true);
            return false;
        }
        if (doc.getTotal() == 0) {
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
            dialog.setModalityType(Dialog.ModalityType.MODELESS);
            dialog.setText("El cambio es \n" + displayAsMoney(pagado - total));
            dialog.setVisible(true);
        }
        return true;
    }

    private void focusPagoField() {
        pago.requestFocus();
        pago.selectAll();
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
                formaPago = button.getText();
            }
        }
    }


    private static class HotKeyDispatcher implements KeyEventDispatcher {
        private final FacturaVentana factura;
        ItemContainer contenido;
        ClientePanel cliente;

        public HotKeyDispatcher(FacturaVentana factura, ItemContainer contenido, ClientePanel cliente) {
            this.factura = factura;
            this.contenido = contenido;
            this.cliente = cliente;
        }
        @Override
        public boolean dispatchKeyEvent(KeyEvent e) {
            if (e.getID() == KeyEvent.KEY_RELEASED) {
                return false;
            }
            switch(e.getKeyCode()) {
                case KeyEvent.VK_F5:
                    cliente.showSearchDialog();
                    break;
                case KeyEvent.VK_F6:
                    contenido.triggerSearchOnLastItem();
                    break;
                case KeyEvent.VK_F7:
                    factura.focusPagoField();
                    break;
                case KeyEvent.VK_F8:
                    factura.guardarFactura();
                    break;
                case KeyEvent.VK_F9:
                    factura.clear();
                    break;
                default:
                    return false;
            }

            return true;
        }
    }
}
