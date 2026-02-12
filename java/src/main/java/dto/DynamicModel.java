package dto;

import java.util.HashMap;
import java.util.Map;

public class DynamicModel {

    private final Map<String, String> fields = new HashMap<>();

    public void set(String column, String value) {
        fields.put(column, value);
    }

    public String get(String column) {
        return fields.get(column);
    }

    public boolean has(String column) {
        return fields.containsKey(column);
    }

    @Override
    public String toString() {
        return fields.toString();
    }
}
