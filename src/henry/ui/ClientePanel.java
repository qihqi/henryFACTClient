package henry.ui;

import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextField;

import henry.api.FacturaInterfaceImpl;
import henry.model.BaseModel;
import henry.model.Cliente;
import net.miginfocom.swing.MigLayout;

public class ClientePanel extends JPanel implements BaseModel.Listener {

	/**
	 *
	 */
	private static final long serialVersionUID = 8993493064487143324L;
	private JButton buscar;
	private JLabel label;
	private JTextField codigo;
	private JTextField nombre;
	private JCheckBox general;

	private ItemContainer contenido;

    private Cliente cliente;

	private boolean create_client = false;

    private class LoadCliente implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            String cod = codigo.getText().trim();
            cliente = new FacturaInterfaceImpl().getClientePorCodigo(cod);
            cliente.addListener(ClientePanel.this);
            cliente.notifyListeners();
        }
    }

	private void initUI() {
		buscar = new JButton();
		buscar.setText("Bus");

		label = new JLabel();
		label.setText("Cliente");

		codigo = new JTextField();
		codigo.setText("");
		codigo.addActionListener(new LoadCliente());

		nombre = new JTextField();
		nombre.setText("");

		general = new JCheckBox();
		general.setText("Cliente General");

		setLayout(new MigLayout("", "[][][][]", "[]"));

		add(label, "cell 0 0");
		add(codigo, "cell 1 0, width 50:200:");
		add(buscar, "cell 3 0,gapx unrelated");
		add(nombre, "cell 4 0, width 100:500:");
		add(general, "cell 1 1");
	}

	public ClientePanel(ItemContainer contenido_) {
		contenido = contenido_;
		initUI();
	}

	public void search() {
        /*
		SearchDialog dialog = new SearchDialog("Cliente", "Cliente");
		dialog.setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE);
		dialog.setVisible(true);
	    */
	}

    @Override
    public void onDataChanged() {
        codigo.setText(cliente.getCodigo());
        nombre.setText(cliente.getApellidos() + " " + cliente.getNombres());
    }
}
