package org.cbs.renderer.service;

import org.cbs.renderer.config.CachedRendererServiceConfig;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.channels.FileLock;
import java.nio.file.Files;
import java.time.Instant;
import java.util.Optional;

@Service
@Qualifier("cached")
public class CachedRendererService implements RendererService {
    private static final Logger logger = LoggerFactory.getLogger(CachedRendererService.class);

    private final CachedRendererServiceConfig config;
    private final RendererService rendererService;

    @Autowired
    public CachedRendererService(CachedRendererServiceConfig config,
                                 @Qualifier("open") RendererService rendererService) {
        this.config = config;
        this.rendererService = rendererService;
    }

    @Override
    public Optional<byte[]> render(String id) throws Exception {
        File f = getCacheFile(id);
        if (!f.exists() || f.length() == 0) {
            logger.atInfo().log(String.format("Cache not found for %s", id));
            return renderAndCache(id);
        }

        if ((Instant.now().toEpochMilli() - f.lastModified()) > config.getTtlSeconds() * 1000L) {
            // Cache expired.
            logger.atInfo().log(String.format("Cache expired for %s", id));
            return renderAndCache(id);
        }

        return Optional.of(Files.readAllBytes(f.toPath()));
    }

    private Optional<byte[]> renderAndCache(String id) throws Exception {
        File file = getCacheFile(id);
        try (RandomAccessFile writer = new RandomAccessFile(file, "rw")) {
            try (FileLock lock = writer.getChannel().lock()) {
                var rendered = this.rendererService.render(id);
                rendered.ifPresent(s -> {
                    try {
                        writer.write(s);
                    } catch (IOException e) {
                        throw new RuntimeException(e);
                    }
                });
                return rendered;
            }
        }
    }

    private File getCacheFile(String id) {
        return new File(config.getPath() + "/" + id + ".cache");
    }
}
