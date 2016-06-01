package henry.model;

import lombok.Getter;
import lombok.Setter;

import java.util.ArrayList;
import java.util.List;

public class Documento {
    @Getter @Setter private Cliente cliente;
    @Getter private List<Item> items;

    @Getter @Setter private int subtotal = 0;
    @Getter @Setter private int descuentoIndividual = 0;

    @Getter @Setter private Usuario user;

    @Getter @Setter private int ivaPorciento = 0;
    @Getter @Setter private int descuentoGlobalPorciento = 0;

    @Getter @Setter private String formaPago;
    @Getter @Setter private int pagado = 0;
    @Getter @Setter private int cambio = 0;
    @Getter @Setter private int retension = 0;

    @Getter @Setter private int codigo;

    public Documento() {
        items = new ArrayList<>();
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
        // integer division will throw away the reminder.
        // Adding 50 makes sure that 0.005 or above get rounded up instead of down
        return (getTotalNeto() * ivaPorciento + 50) / 100;
    }

    public int getTotal() {
        return getTotalNeto() + getIva() - getRetension();
    }
}
