package henry.ui;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.Rectangle;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Map;
import java.util.HashMap;
import java.util.ArrayList;

import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JViewport;

import henry.model.BaseModel;
import henry.model.Documento;
import henry.model.Item;
import net.miginfocom.swing.MigLayout;
import javax.swing.JTextField;

@SuppressWarnings("serial")
public class ItemContainer extends JPanel implements BaseModel.Listener {

    /** Tiene arreglo de itemPanel, representa los contenidos
     *  de una factura/nota
     *
     */

    private static final int DEFAULT_IVA = 12;
    private static final int VIEWABLE_ROW_COUNT = 6;

    private int current; // the current selected item
    private ArrayList<ItemPanel> items;
    private Map<ItemPanel, Integer> reverseItem;

    private JPanel content;

    private JLabel lCod;
    private JLabel lCant;
    private JLabel lNombre;
    private JLabel lPre;
    private JLabel lSub;
    private JScrollPane scroll;

    private JTextField ivaPorciento;
    private JTextField ivaValor;
    private JTextField totalValor;
    private JTextField descValor;

    private JTextField subValor;
    private JTextField subtotalValor;

    private Documento documento;
    private DocumentoUpdater totalUpdater;

    private static class DocumentoUpdater implements BaseModel.Listener {
        private Documento documento;
        DocumentoUpdater(Documento documento) {
            this.documento = documento;
        }

        @Override
        public void onDataChanged() {
            int subtotal = 0;
            for (Item item : documento.getItems()) {
                subtotal += item.getSubtotal();
            }
            documento.setSubtotal(subtotal);
            int iva = (int) Math.round(0.12 * subtotal);
            int total = subtotal + iva;
            documento.setIva(iva);
            documento.setTotal(total);
            documento.notifyListeners();
        }
    }

    //-------------------------------------------------------------------------------
    public ItemContainer(boolean fact) {
        super(new BorderLayout());

        items = new ArrayList<ItemPanel>();
        current = 0;

        reverseItem = new HashMap<ItemPanel, Integer>();
        documento = new Documento();
        documento.addListener(this);
        Item firstItem = new Item();
        totalUpdater = new DocumentoUpdater(documento);
        firstItem.addListener(totalUpdater);
        initUI(firstItem);

    }

    public void initUI(Item firstItem) {
        System.out.println("ItemContainer::initUI");
        JPanel header = new JPanel(new MigLayout("",
                "90[]10[][][][]",""));

        lCod = new JLabel();
        lCod.setText("Codigo");

        lCant = new JLabel();
        lCant.setText("Cantidad");

        lNombre = new JLabel();
        lNombre.setText("Nombre del Producto");

        lPre = new JLabel();
        lPre.setText("Precio");

        lSub = new JLabel();
        lSub.setText("Subtotal");

        header.add(lCod, "width :100:");
        header.add(lCant, "width :80:");
        header.add(lNombre, "width :200:");
        header.add(lPre, "width :80:");
        header.add(lSub, "width :100:");
        setPreferredSize(new Dimension(792, 570));

        add(header, BorderLayout.PAGE_START);

        //-----------------CONTENT--------------------------------
        content = new JPanel(new MigLayout());

        ItemPanel first = new ItemPanel(this, firstItem);
        items.add(first);
        reverseItem.put(first, 0);

        content.add(first, "wrap");
        //content.add(new ItemPanel(this), "wrap");

        scroll = new JScrollPane(content);

        add(scroll, BorderLayout.CENTER);

        //---------TOTAL---------------------------
        JPanel totales = new JPanel();

        add(totales, BorderLayout.PAGE_END);
        totales.setLayout(new MigLayout("", "400[right][30][][100]","[][][][][]"));

        JLabel ivaLabel = new JLabel("IVA: ");
        JLabel totalLabel = new JLabel("Total: ");
        JLabel porciento = new JLabel("%");
        JLabel netLabel = new JLabel("Valor Neto: ");
        JLabel descLabel = new JLabel("Descuento: ");
        JLabel subLabel = new JLabel("Valor Bruto: ");



        ivaPorciento = new JTextField("" + DEFAULT_IVA);
        ivaValor = new JTextField();
        ivaValor.setEditable(false);

        ivaPorciento.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                updateIVA();
            }
        });


        totales.add(subLabel, "cell 0 0");

        subValor = new JTextField();
        subValor.setEditable(false);


        totales.add(subValor, "cell 3 0,width :100:");

        descValor = new JTextField();
        descValor.setEditable(false);

        totales.add(descLabel, "cell 0 1");
        totales.add(descValor, "cell 3 1, width :100:");

        subtotalValor = new JTextField();
        subtotalValor.setEditable(false);

        totales.add(netLabel, "cell 0 2");
        totales.add(subtotalValor, "cell 3 2, width :100:");

        totales.add(ivaLabel, "cell 0 3");
        totales.add(ivaPorciento, "cell 1 3,width :30:");
        totales.add(porciento, "cell 2 3");
        totales.add(ivaValor, "cell 3 3,width :100:");

        totales.add(totalLabel, "cell 0 4" );
        totalValor = new JTextField();
        totalValor.setEditable(false);
        totales.add(totalValor, "cell 3 4,width :100:");
    }

    public void scrollDown() {
        JViewport vp = scroll.getViewport();
        Rectangle rect = vp.getBounds();
        rect.setLocation((int) rect.getX(),(int) rect.getY() + 100);
        vp.scrollRectToVisible(rect);
    }

    public void scrollUp() {
        JViewport vp = scroll.getViewport();
        Rectangle rect = vp.getBounds();
        //System.out.printf("%d %d", rect.getX(), rect.getY());
        rect.setLocation((int) rect.getX(),0);
        vp.scrollRectToVisible(rect);
    }


    /*
     *  Do the event when shift is updated. ie update the total
     *  and change the cursor to next line
     */
    public void shiftEvent() {
        //move the cursor to next one
        //update the total
        updateSubtotal(); //also update descuento
        getFocus();
    }

    public void getFocus() {
        int threshold = items.size() - 1;
        if (current < threshold) {
            //dont need to make new one
            System.out.println("didnt add new");
            ItemPanel next = items.get(++current);
            next.focus();
        }
        else if (current == threshold /*&& items.get(threshold).getProdCont() == null */ ) {
            items.get(threshold).focus();
        }
        else {
            //allocate new ones
        /*    Item nuevoItem = new Item();
            ItemPanel newOne = new ItemPanel(this, nuevoItem);
            nuevoItem.addListener(totalUpdater);
            documento.getItems().add(nuevoItem);
            items.add(newOne);
            content.add(newOne, "wrap");
            content.revalidate();
            current++;
            reverseItem.put(newOne, current);
            newOne.focus();
            */
        }
    }

    public void updateSubtotal() {
    }

    public void updateIVA() {
    }

    public void setCurrent(ItemPanel item) {
        current = reverseItem.get(item).intValue();
    }
    public ArrayList<ItemPanel> getItems() {
        return items;
    }


    public void clear() {
        //save the first itemPanel
        ItemPanel first = items.get(0);
        first.clear();
        //for (int i = 1; i < items.size(); i++)
        //items.get(i)first;
        //update new content
        content.removeAll();
        content.repaint();
        content.add(first, "wrap");
        //update the records
        items.clear();
        items.add(first);
        reverseItem.clear();
        reverseItem.put(first, 0);

        //update new total etc//
        current = 0;

        //ivaPorciento.setText("");
        ivaValor.setText("");
        totalValor.setText("");
        subtotalValor.setText("");
        subValor.setText("");
        descValor.setText("");

        scrollUp();
    }

    @Override
    public void onDataChanged() {

    }
}
