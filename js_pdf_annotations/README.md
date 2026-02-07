# PDF Viewer with Annotations

A simple, server-free web application for viewing PDFs and working with annotations. Runs entirely in the browser using PDF.js for rendering and pdf-lib for modification.

## Features

- **PDF Viewing**: Load and display PDF files with page navigation
- **Annotation Detection**: Reads and logs all annotations from PDFs to the console
- **Annotation Creation**: Add various annotation types to PDFs
- **Download**: Save modified PDFs with your annotations

## Supported Annotation Types

| Type | Description | Visible | Readable Text |
|------|-------------|---------|---------------|
| **Highlight** | Yellow semi-transparent overlay | Yes | `contents` property |
| **Text (Sticky Note)** | Comment icon with popup text | Icon only | `contents` property |
| **FreeText** | Text box displayed on page | Yes | `contents` property |
| **Link** | Clickable hyperlink area | Blue outline | `url` property |
| **Stamp** | Image-based stamps (read-only) | Yes | Usually none |

## Usage

1. Open `pdf-viewer.html` directly in a modern browser (Chrome, Firefox, Safari, Edge)
2. Click "Choose PDF File" to select a PDF
3. Open browser console (F12) to see annotation details
4. Use the green buttons to add annotations
5. Click "Download Modified PDF" to save your changes

## Dependencies

All dependencies are loaded via CDN at runtime - no installation required:

- [PDF.js 3.11.174](https://mozilla.github.io/pdf.js/) - PDF rendering and annotation reading
- [pdf-lib 1.17.1](https://pdf-lib.js.org/) - PDF modification and annotation creation

## Technical Notes

### Coordinate System
- PDF coordinates have origin at bottom-left
- Canvas/viewport coordinates have origin at top-left
- The application handles coordinate transformation automatically

### Annotation Rendering
- Annotations are rendered in a separate layer on top of the PDF canvas
- Highlight annotations use CSS `mix-blend-mode: multiply` for realistic highlighting
- Link annotations are clickable and open in new tabs

### Browser Compatibility
Works in all modern browsers that support:
- ES6+ JavaScript
- Canvas API
- File API
- Fetch API

## File Structure

```
js_pdf_annotations/
├── pdf-viewer.html   # Main application (single file)
└── README.md         # This file
```

## Limitations

- Stamp annotations are typically image-based; their visible text is rendered in the image, not stored as a text property
- Some encrypted or complex PDFs may not be modifiable with pdf-lib
- FreeText annotations require an appearance stream for full rendering in external PDF readers

## License

MIT License
