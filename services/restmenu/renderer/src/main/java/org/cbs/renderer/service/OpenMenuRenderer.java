package org.cbs.renderer.service;

import org.cbs.renderer.config.OpenRendererConfig;
import org.cbs.renderer.dto.Menu;
import org.commonmark.parser.Parser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import com.openhtmltopdf.pdfboxout.PdfRendererBuilder;
import com.openhtmltopdf.svgsupport.BatikSVGDrawer;
import org.commonmark.renderer.html.HtmlRenderer;

import java.io.ByteArrayOutputStream;
import java.io.IOException;


@Component
public class OpenMenuRenderer implements MenuRenderer {
    private static final Logger logger = LoggerFactory.getLogger(OpenMenuRenderer.class);
    private static final HtmlRenderer renderer = HtmlRenderer.builder()
            .escapeHtml(true)
            .sanitizeUrls(true)
            .build();
    private static final String HTML_HEADER = "<html>" +
            "<head>" +
            "<title>Menu</title>" +
            "</head>" +
            "<body>";
    private static final String HTML_FOOTER = "</body>" +
            "</html>";

    private final String baseURL;

    @Autowired
    public OpenMenuRenderer(OpenRendererConfig config) {
        this.baseURL = config.getBaseURL();
    }

    @Override
    public byte[] render(Menu menu) throws Exception {
        Parser parser = Parser.builder().build();
        var parsed = parser.parse(menu.getMarkdown());

        var html = String.format("%s%s%s", HTML_HEADER  , renderer.render(parsed), HTML_FOOTER);

        var os = new ByteArrayOutputStream();

        PdfRendererBuilder builder = new PdfRendererBuilder();
        try {
            builder.useSVGDrawer(new BatikSVGDrawer())
                    .useFastMode()
                    .withHtmlContent(html, this.baseURL).toStream(os).run();
        } catch (IOException e) {
            throw new Exception("Failed to render card", e);
        }

        return os.toByteArray();
    }
}
