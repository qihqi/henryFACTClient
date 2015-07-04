package henry.ui;

import henry.model.Item;
import henry.api.FacturaInterface;
import henry.model.Producto;

class ItemPanelFactory {
    private FacturaInterface api;
    private SearchDialog<Producto> dialog;

    public ItemPanelFactory(FacturaInterface api, SearchDialog<Producto> dialog) {
        this.api = api;
        this.dialog = dialog;
    }

    public ItemPanel make(ItemContainer container, Item item) {
        return new ItemPanel(container, item, api, dialog);
    }
}
