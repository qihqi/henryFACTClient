package henry.ui;

import henry.api.FacturaInterface;
import henry.api.FacturaInterfaceImplSQL;
import henry.api.SearchEngine;
import henry.model.BaseModel;
import henry.model.Item;
import henry.model.Producto;
import net.miginfocom.swing.MigLayout;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;

import static henry.Helpers.displayAsMoney;
import static henry.Helpers.displayMilesimas;

/** This Class represents a row in a nota de venta o factura
 *
 */
@SuppressWarnings("serial")
public class ItemPanel extends JPanel implements BaseModel.Listener {
    private JTextField codigo;
    private JTextField cantidad;
    private JTextField nombre;
    private JTextField precio;
    private JTextField subtotal;

    private ItemContainer parent;
    private Item item;

    public ItemPanel(ItemContainer parent_, Item item) {
        parent = parent_;
        this.item = item;
        item.addListener(this);
        initUI();
    }

    //this class notifies the parent about currently selected item
    private class ReFocusListener extends MouseAdapter {
        @Override
        public void  mouseClicked(MouseEvent e) {
            //parent.setCurrent(thisPanel);
        }
    }

    //This class gives TextField ability to select all text
    //when gain focus
    private static class HighlightFocusListener extends FocusAdapter {
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

    private class ProductoLoader implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            String code = codigo.getText();
            Producto prod = FacturaInterface.INSTANCE.getProductoPorCodigo(code);
            if (prod != null) {
                item.setProducto(prod);
                item.notifyListeners();
                cantidad.requestFocus();
            } else {
                codigo.requestFocus();
            }
        }
    }

    private class CantidadUpdater implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            String cantString = cantidad.getText();
            int cantReal = (int) Math.round(Double.parseDouble(cantString) * 1000);
            item.setCantidad(cantReal);
            item.notifyListeners();

            parent.shiftEvent(ItemPanel.this);
            parent.scrollDown();
        }
    }

    private class SearchProducto implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            SearchDialog<Producto> dialog = new SearchDialog<>(SearchEngine.PRODUCTO);
            dialog.setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE);
            dialog.setVisible(true);
            Producto result = dialog.getResult();
            item.setProducto(result);
            item.notifyListeners();
        }
    }
    public void initUI() {
        codigo = new JTextField();
        cantidad = new JTextField();
        nombre = new JTextField();
        nombre.setEditable(false);
        precio = new JTextField();
        precio.setEditable(false);
        subtotal = new JTextField();
        subtotal.setEditable(false);

        JButton buscar = new JButton("Bus");
        buscar.setFont(new Font("Dialog", Font.BOLD, 10));
        buscar.addActionListener(new SearchProducto());
        final JButton newPrice = new JButton();

        codigo.addFocusListener(new HighlightFocusListener(codigo));
        codigo.addMouseListener(new ReFocusListener());
        codigo.addActionListener(new ProductoLoader());

        cantidad.addFocusListener(new HighlightFocusListener(cantidad));
        cantidad.addMouseListener(new ReFocusListener());
        cantidad.addActionListener(new CantidadUpdater());

        setLayout(new MigLayout());
        add(buscar, "width :30:");
        add(codigo, "width :100:");
        add(cantidad, "width :80:");
        add(nombre, "width :200:");
        add(precio, "width :80: ");
        add(subtotal, "width :100:");
        add(newPrice, "width :15:,height :20:");
    }

    public void focus() {
        codigo.requestFocus();
    }

    public void clear() {}

    public void onDataChanged() {
        System.out.println("onDataChagned");
        Producto prod = item.getProducto();
        codigo.setText(prod.getCodigo());
        cantidad.setText(displayMilesimas(item.getCantidad()));
        precio.setText(displayAsMoney(prod.getPrecio1()));
        nombre.setText(prod.getNombre());
        subtotal.setText(displayAsMoney(item.getSubtotal()));
    }

}
