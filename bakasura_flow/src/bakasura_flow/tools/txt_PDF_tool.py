#pdf.add_font('DejaVu', '', '/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf', uni=True)
import fpdf

class PDFConversionTool:
    name = "PDF Conversion Tool"
    description = "Converts a text file to a PDF file"

    def __init__(self, input_file_path: str, output_file_path: str):
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path

    def _run(self):
        self.text_to_pdf()
        return f"PDF created successfully: {self.output_file_path}"

    async def _arun(self):
        return self._run()

    def clean_text(self, text: str) -> str:
        replacements = {
            'â€™': "'",
            '?': "'",
            '\u00A0': ' '  # Replace non-breaking spaces with regular spaces
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove extra spaces and newlines
        text = text.strip()  # Remove leading and trailing spaces
        text = ' '.join(text.split())  # Replace multiple spaces/newlines with a single space
        return text

    def text_to_pdf(self):
        pdf = fpdf.FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Set the font to DejaVu Sans (you need the correct path to the .ttf file)
        pdf.add_font('DejaVu', '', '/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf', uni=True)
        pdf.set_font("DejaVu", size=10)  # Adjust font size to manage space

        # Set smaller margins
        pdf.set_left_margin(10)
        pdf.set_right_margin(10)
        pdf.set_top_margin(10)

        with open(self.input_file_path, "r", encoding='utf-8') as file:
            for line in file:
                clean_line = self.clean_text(line.rstrip('\n'))
                pdf.multi_cell(190, 5, txt=clean_line, align='L')  # Reduced line height to 5
                
                # Add minimal spacing between paragraphs
                if clean_line.strip() == "":
                    pdf.ln(2)

        pdf.output(self.output_file_path)
