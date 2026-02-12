package model;

public class FieldDefinition {

    private final String name;
    private final String type;
    private final boolean enabled;

    public FieldDefinition(String name, String type, boolean enabled) {
        this.name = name;
        this.type = type;
        this.enabled = enabled;
    }

    public String getName() {
        return name;
    }

    public String getType() {
        return type;
    }

    public boolean isEnabled() {
        return enabled;
    }
}
