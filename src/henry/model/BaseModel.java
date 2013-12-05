package henry.model;

import java.util.List;

public abstract class BaseModel {
    private List<Listener> listeners;

    public void notify_all() {
        for (Listener listener : listeners) {
            listener.onDataChanged();
        }
    }

    public interface Listener {
        void onDataChanged();
    }
}
