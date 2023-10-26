package org.cbs.renderer;

import org.cbs.renderer.config.CachedRendererServiceConfig;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;


@RestController
public class IndexController {

    @GetMapping("/")
    public String index() {
        return "Greetings from Spring Boot!";
    }
}
