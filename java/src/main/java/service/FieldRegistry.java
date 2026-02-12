package service;

import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import config.Config;
import model.FieldDefinition;

public class FieldRegistry {

    private final Map<String, FieldDefinition> fields;
    private final Map<String, Set<String>> templates;
    private final String defaultTemplateName;
    private final boolean hasDefinitions;

    public FieldRegistry(Config config) {
        Map<String, FieldDefinition> fieldMap = new HashMap<>();
        Map<String, Set<String>> templateMap = new HashMap<>();

        JsonObject fieldDefs = config.getObjectOrNull("field_definitions");
        String defaultTemplate = null;
        if (fieldDefs != null) {
            if (fieldDefs.has("default_template")) {
                defaultTemplate = fieldDefs.get("default_template").getAsString();
            }

            JsonArray productFields = fieldDefs.has("product")
                    ? fieldDefs.getAsJsonArray("product")
                    : null;

            if (productFields != null) {
                for (JsonElement element : productFields) {
                    if (!element.isJsonObject()) {
                        continue;
                    }
                    JsonObject obj = element.getAsJsonObject();
                    String name = obj.has("name") ? obj.get("name").getAsString() : null;
                    if (name == null || name.isBlank()) {
                        continue;
                    }
                    String type = obj.has("type") ? obj.get("type").getAsString() : "string";
                    boolean enabled = !obj.has("enabled") || obj.get("enabled").getAsBoolean();
                    fieldMap.put(name, new FieldDefinition(name, type, enabled));
                }
            }
        }

        JsonObject templateDefs = config.getObjectOrNull("templates");
        if (templateDefs != null) {
            for (Map.Entry<String, JsonElement> entry : templateDefs.entrySet()) {
                if (!entry.getValue().isJsonArray()) {
                    continue;
                }
                Set<String> templateFields = new HashSet<>();
                for (JsonElement item : entry.getValue().getAsJsonArray()) {
                    if (item.isJsonPrimitive()) {
                        templateFields.add(item.getAsString());
                    }
                }
                templateMap.put(entry.getKey(), templateFields);
            }
        }

        this.fields = fieldMap;
        this.templates = templateMap;
        this.defaultTemplateName = defaultTemplate;
        this.hasDefinitions = !fieldMap.isEmpty();
    }

    public boolean isEnabled(String fieldName) {
        if (!hasDefinitions) {
            return true;
        }
        FieldDefinition def = fields.get(fieldName);
        return def != null && def.isEnabled();
    }

    public Set<String> getTemplateFields(String templateName) {
        Set<String> templateFields = templates.get(templateName);
        return templateFields == null ? Collections.emptySet() : templateFields;
    }

    public Set<String> getDefaultTemplateFields() {
        if (defaultTemplateName == null || defaultTemplateName.isBlank()) {
            return Collections.emptySet();
        }
        return getTemplateFields(defaultTemplateName);
    }

    public boolean hasDefinitions() {
        return hasDefinitions;
    }
}
