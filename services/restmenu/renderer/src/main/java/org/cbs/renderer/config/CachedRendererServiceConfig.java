package org.cbs.renderer.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Component;

@Configuration
@ConfigurationProperties(prefix = "cached-renderer-service")
public class CachedRendererServiceConfig {
    private String path;
    private int ttlSeconds;

    public void setPath(String path) {
        this.path = path;
    }

    public String getPath() {
        return path;
    }

    public void setTtlSeconds(int ttlSeconds) {
        this.ttlSeconds = ttlSeconds;
    }

    public int getTtlSeconds() {
        return ttlSeconds;
    }
}
