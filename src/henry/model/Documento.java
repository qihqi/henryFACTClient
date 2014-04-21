package henry.model;

import lombok.Getter;
import lombok.Setter;

import java.util.ArrayList;
import java.util.List;

public class Documento extends BaseModel implements BaseModel.Listener {
    @Getter @Setter private Cliente cliente;
    @Getter private List<Item> items;

    @Setter private int ivaPorciento;
    @Setter private int descuentoGlobalPorciento;

    @Getter private int subtotal;
    private int descuentoIndividual;

    public Documento() {
        items = new ArrayList<Item>();
    }

    public void addItem(Item item) {
        items.add(item);
        item.addListener(this);
    }

    public int getDescuento() {
        int descGlobalValor = (subtotal * descuentoGlobalPorciento) / 100;
        return descGlobalValor + descuentoIndividual;
    }
    public int getTotalNeto() {
        return subtotal - getDescuento();
    }

    public int getIva() {
        return (getTotalNeto() * ivaPorciento) / 100;
    }

    public int getTotal() {
        return getTotalNeto() + getIva();
    }

    @Override
    public void onDataChanged() {
        subtotal = 0;
        descuentoIndividual = 0;
        for (Item i : items) {
            subtotal += i.getSubtotal();
            descuentoIndividual += i.getDescuento();
        }
        notifyListeners();
    }
}
