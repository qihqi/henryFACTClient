package henry.model;

import lombok.Getter;
import lombok.Setter;

import java.util.ArrayList;
import java.util.List;

public class Documento {
    @Getter @Setter private Cliente cliente;
    @Getter private List<Item> items;

    @Getter @Setter private int subtotal;
    @Getter @Setter private int descuentoIndividual;

    @Getter @Setter private Usuario user;

    @Getter @Setter private int ivaPorciento;
    @Getter @Setter private int descuentoGlobalPorciento;

    public Documento() {
        items = new ArrayList<Item>();
    }

    public void addItem(Item item) {
        items.add(item);
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
}
