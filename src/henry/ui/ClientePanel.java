package henry.ui;

import lombok.Getter;
import lombok.Setter;
import henry.api.FacturaInterface;
import henry.api.SearchEngine;
import henry.model.BaseModel;
import henry.model.Cliente;
import net.miginfocom.swing.MigLayout;

import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextField;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

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

    @Getter @Setter
    private Cliente cliente;

    private class LoadCliente implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            String cod = codigo.getText().trim();
            loadCliente(cod);
        }
    }

    private class LoadGeneral implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            loadCliente("NA");
        }
    }

	private void initUI() {
		buscar = new JButton();
		buscar.setText("Bus");
        buscar.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                SearchDialog<Cliente> dialog = new SearchDialog<>(SearchEngine.CLIENTE);
                dialog.setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE);
                dialog.setVisible(true);
                Cliente result = dialog.getResult();
                bindCliente(result);
            }
        });

		label = new JLabel();
		label.setText("Cliente");

		codigo = new JTextField();
		codigo.setText("");
		codigo.addActionListener(new LoadCliente());

		nombre = new JTextField();
		nombre.setText("");

		general = new JCheckBox();
		general.setText("Cliente General");
        general.addActionListener(new LoadGeneral());

		setLayout(new MigLayout("", "[][][][]", "[]"));

		add(label, "cell 0 0");
		add(codigo, "cell 1 0, width 50:200:");
		add(buscar, "cell 3 0,gapx unrelated");
		add(nombre, "cell 4 0, width 100:500:");
		add(general, "cell 1 1");
	}

	public ClientePanel(Cliente cliente) {
        this.cliente = cliente;
        cliente.addListener(this);
		initUI();
	}

    @Override
    public void onDataChanged() {
        codigo.setText(cliente.getCodigo());
        nombre.setText(cliente.toString());
    }

    private void loadCliente(String cod) {
        bindCliente(FacturaInterface.INSTANCE.getClientePorCodigo(cod));
    }

    private void bindCliente(Cliente newCliente) {
        if (newCliente == null) {
            return;
        }
        cliente.setApellidos(newCliente.getApellidos());
        cliente.setCodigo(newCliente.getCodigo());
        cliente.setNombres(newCliente.getNombres());
        cliente.setDireccion(newCliente.getDireccion());
        cliente.setTipo(newCliente.getTipo());
        cliente.setTelefono(newCliente.getTelefono());
        cliente.setCiudad(newCliente.getCiudad());
        cliente.notifyListeners();
    }

}
