package henry.model;

import java.util.ArrayList;
import java.util.List;
import java.lang.ref.WeakReference;

public abstract class BaseModel {
    private List<WeakReference<Listener>> listeners;

    public BaseModel() {
        listeners = new ArrayList<WeakReference<Listener>>();
    }

    public void notifyListeners() {
        for (WeakReference<Listener> wr : listeners) {
            Listener listener = wr.get();
            if (listener != null) {
                listener.onDataChanged();
            }
        }
    }

    public void addListener(Listener listener) {
        listeners.add(new WeakReference(listener));
    }

    public interface Listener {
        void onDataChanged();
    }
}
