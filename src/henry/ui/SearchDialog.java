package henry.ui;

import henry.api.SearchEngine;
import java.awt.event.WindowEvent;
import java.awt.event.WindowFocusListener;
import net.miginfocom.swing.MigLayout;

import javax.swing.DefaultListModel;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextField;
import javax.swing.ListSelectionModel;
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;
import java.awt.BorderLayout;
import java.awt.Dialog;
import java.awt.Font;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.List;

@SuppressWarnings("serial")
class SearchDialog<T> extends JDialog {

    //TextArea for searching
    private JTextField searchInput;
    private JList<String> display;
    private DefaultListModel<String> listContent;

    private SearchEngine<T> engine;

    private List<T> resultList;
    private final JPanel contentPanel = new JPanel();
    private int selectedIndex;

    private class SearchAction implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            String prefix = e.getActionCommand().trim();
            resultList = engine.search(prefix);
            listContent.clear();
            if (resultList.isEmpty()) {
                String NO_ENCONTRADO = "No ha podido encontrar el cliente";
                listContent.addElement(NO_ENCONTRADO);
            }
            else {
                for (T r : resultList) {
                    listContent.addElement(r.toString());
                }
            }
        }
    }

    /**
     * Create the dialog.
     */
    public SearchDialog(SearchEngine<T> engine) {
        super(null, Dialog.ModalityType.APPLICATION_MODAL);
        this.engine = engine;
        initUI();
    }

    private void initUI() {
        setBounds(100, 100, 502, 255);

        getContentPane().setLayout(new BorderLayout());
        contentPanel.setLayout(new MigLayout());


        getContentPane().add(contentPanel, BorderLayout.CENTER);

        JLabel lblNewLabel = new JLabel(engine.toString());
        lblNewLabel.setFont(new Font("Dialog", Font.BOLD, 13));
        contentPanel.add(lblNewLabel);

        searchInput = new JTextField();
        searchInput.addActionListener(new SearchAction());
        contentPanel.add(searchInput, "wrap, width :400:");

        listContent = new DefaultListModel<>();
        display = new JList<>(listContent);
        display.setVisibleRowCount(10);
        display.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);

        display.addListSelectionListener(new ListSelectionListener() {
            @Override
            public void valueChanged(ListSelectionEvent e) {
                if (resultList.isEmpty()) {
                    return;
                }
                int index = display.getSelectedIndex();
                System.out.println("index " + selectedIndex);
                if (index != -1) {
                    selectedIndex = index;
                    display.clearSelection();
                    setVisible(false);
                }
            }
        });
        contentPanel.add(new JScrollPane(display), "span, width :456:");

        this.addWindowFocusListener(new WindowFocusListener() {
            @Override
            public void windowGainedFocus(WindowEvent e) {
                SearchDialog.this.focus();
            }

            @Override
            public void windowLostFocus(WindowEvent e) {}
        });
    }

    public T getResult() {
        return resultList.get(selectedIndex);
    }

    void focus() {
        searchInput.requestFocus();
        searchInput.selectAll();
    }
}
