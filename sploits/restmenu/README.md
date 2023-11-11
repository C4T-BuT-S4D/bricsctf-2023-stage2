## Restmenu

### SSRF via Markdown render

The `restmenu` service allows you to create a menu, the data you entered will be used to generate a markdown file.
You can also render the menu as PDF file, to do so the service will use the generated markdown, convert it to HTML and
then to PDF.

So, overall algorithm is:

1. User enters data using the API (written in Kotlin).
2. The API generates a markdown file on create and update.
3. If the user wants to render the menu as PDF, the API will call the "renderer" service (written in Java) that will
   perform:
1. Read the menu by ID.
2. Convert markdown to HTML using [commonmark-java](https://github.com/commonmark/commonmark-java).
3. Convert HTML to PDF using the [OpenHTMLtoPDF library](https://github.com/danfickle/openhtmltopdf).

The suspicious thing is that the renderer service is not checking any permissions and suppose to be internal only, so if
we would be able to call the `/api/render/<attack_data_id>` endpoint we could get the PDF file we don't have access to.

From the API (and checkers traffic) we can clearly see that the renderer can render the images.

The second suspicious thing is that the image input is the only input that has poor validation. Instead of checking
the user-input as a regex, it's checked by using Java's `URI` class.

So, if we bypass the `URI` check, we would be able to inject the markdown we want and trigger the SSRF.

Well, we won't really benefit from the blind SSRF, so we need to find a way to leak the response.
Thankfully, the "OpenHTMLtoPDF" have some weird logic
to [embed the .pdf files in the HTML "<a>" attributes](https://github.com/danfickle/openhtmltopdf/blob/780ba564839f1ad5abfa5df12e4aebb9dd6782d2/openhtmltopdf-pdfbox/src/main/java/com/openhtmltopdf/pdfboxout/PdfBoxReplacedElementFactory.java#L82)
.

Using this, the solution itself can be described as:

1. Create a markdown that will result with HTML that will have "<a>" tag with the href set
   to "http://localhost:8081/api/render/<attack_data_id>#.pdf".
2. To make this markdown, we need to bypass the `URI` check. That can be done by putting the payload in the query
   string.

Final payload: `test/?a=)![t](http://localhost:8081/api/render/{hint}#.pdf)`

Specifying this in our menu and rendering it after will result with the victim PDF embedded into our PDF, so we can read
the
flag by extracting it from the PDF.

[Full exploit](./injection_ssrf.py)


