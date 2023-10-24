package org.cbs.renderer.dto;


import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.MongoId;

@Document(collection = "menu")
public class Menu {
    @Id
    @MongoId
    public String id;
    public String name;
    public String markdown;

    public Menu(String id, String name, String markdown) {
        this.id = id;
        this.name = name;
        this.markdown = markdown;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getMarkdown() {
        return markdown;
    }

    public void setMarkdown(String markdown) {
        this.markdown = markdown;
    }
}
