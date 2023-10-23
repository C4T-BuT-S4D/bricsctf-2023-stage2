package org.cbs.renderer;

import org.cbs.renderer.service.CachedRendererService;
import org.cbs.renderer.service.RendererService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RenderController {
    private static final Logger logger = LoggerFactory.getLogger(CachedRendererService.class);
    final RendererService service;

    @Autowired
    RenderController(@Qualifier("cached") RendererService service) {
        this.service = service;
    }

    @GetMapping("/api/render/{id}")
    public ResponseEntity<byte[]> render(@PathVariable String id) {
        try {
            var maybeRendered = service.render(id);
            return maybeRendered.map(ResponseEntity::ok).orElseGet(() -> ResponseEntity.status(HttpStatus.NOT_FOUND).body("Not found".getBytes()));
        } catch (Exception e) {
            logger.atError().log(e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error".getBytes());
        }
    }
}
