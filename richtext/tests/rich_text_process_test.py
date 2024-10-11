import unittest
import tempfile
import os
from pathlib import Path
from rich_text_process import rich_text_process, process_docx, process_html, process_odt
from unittest.mock import patch, MagicMock
import zipfile

class TestRichTextProcess(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(self.temp_dir, "input.docx")
        self.output_file = os.path.join(self.temp_dir, "output.docx")
        self.command = ["echo", "processed"]

    def tearDown(self):
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    @patch('rich_text_process.process_docx')
    def test_rich_text_process_docx(self, mock_process_docx):
        Path(self.input_file).touch()
        rich_text_process(self.output_file, self.input_file, self.command)
        mock_process_docx.assert_called_once_with(self.output_file, self.input_file, self.command, False, None)

    @patch('rich_text_process.process_html')
    def test_rich_text_process_html(self, mock_process_html):
        input_file = os.path.join(self.temp_dir, "input.html")
        output_file = os.path.join(self.temp_dir, "output.html")
        Path(input_file).touch()
        rich_text_process(output_file, input_file, self.command)
        mock_process_html.assert_called_once_with(output_file, input_file, self.command, False, None)

    @patch('rich_text_process.process_odt')
    def test_rich_text_process_odt(self, mock_process_odt):
        input_file = os.path.join(self.temp_dir, "input.odt")
        output_file = os.path.join(self.temp_dir, "output.odt")
        Path(input_file).touch()
        rich_text_process(output_file, input_file, self.command)
        mock_process_odt.assert_called_once_with(output_file, input_file, self.command, False, None)

    def test_rich_text_process_unsupported_file(self):
        input_file = os.path.join(self.temp_dir, "input.txt")
        output_file = os.path.join(self.temp_dir, "output.txt")
        Path(input_file).touch()
        with self.assertRaises(ValueError):
            rich_text_process(output_file, input_file, self.command)

    def test_rich_text_process_input_not_found(self):
        with self.assertRaises(FileNotFoundError):
            rich_text_process(self.output_file, "nonexistent.docx", self.command)

    def test_rich_text_process_output_exists(self):
        # Create a minimal valid DOCX file
        with zipfile.ZipFile(self.input_file, 'w') as docx:
            docx.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Test content</w:t></w:r></w:p></w:body></w:document>')

        Path(self.output_file).touch()
        with self.assertRaises(FileExistsError):
            rich_text_process(self.output_file, self.input_file, self.command, force=False)

        # Test with force=True
        rich_text_process(self.output_file, self.input_file, self.command, force=True)
        self.assertTrue(Path(self.output_file).exists())

    @patch('rich_text_process.zipfile.ZipFile')
    @patch('rich_text_process.ET.parse')
    @patch('rich_text_process.subprocess.run')
    def test_process_docx(self, mock_subprocess_run, mock_et_parse, mock_zipfile):
        mock_subprocess_run.return_value.stdout = "processed text"
        mock_root = MagicMock()
        mock_elem = MagicMock()
        mock_elem.text = "original text"
        mock_root.iter.return_value = [mock_elem]
        mock_et_parse.return_value.getroot.return_value = mock_root

        process_docx(self.output_file, self.input_file, self.command, False)

        mock_zipfile.assert_called()
        mock_et_parse.assert_called()
        mock_subprocess_run.assert_called_with(self.command, input="original text", text=True, stdout=-1)
        self.assertEqual(mock_elem.text, "processed text")

    @patch('rich_text_process.open')
    @patch('rich_text_process.BeautifulSoup')
    @patch('rich_text_process.subprocess.run')
    def test_process_html(self, mock_subprocess_run, mock_bs, mock_open):
        mock_subprocess_run.return_value.stdout = "processed text"
        mock_soup = MagicMock()
        mock_node = MagicMock()
        mock_node.string = "original text"
        mock_node.parent.name = "p"
        mock_soup.find_all.return_value = [mock_node]
        mock_bs.return_value = mock_soup

        process_html(self.output_file, self.input_file, self.command, False)

        mock_bs.assert_called()
        mock_subprocess_run.assert_called_with(self.command, input="original text", text=True, stdout=-1)
        self.assertEqual(mock_node.string, "processed text")  # Changed this line

    @patch('rich_text_process.zipfile.ZipFile')
    @patch('rich_text_process.ET.parse')
    @patch('rich_text_process.subprocess.run')
    def test_process_odt(self, mock_subprocess_run, mock_et_parse, mock_zipfile):
        mock_subprocess_run.return_value.stdout = "processed text"
        mock_root = MagicMock()
        mock_elem = MagicMock()
        mock_elem.text = "original text"
        mock_root.iter.return_value = [mock_elem]
        mock_et_parse.return_value.getroot.return_value = mock_root

        process_odt(self.output_file, self.input_file, self.command, False)

        mock_zipfile.assert_called()
        mock_et_parse.assert_called()
        mock_subprocess_run.assert_called_with(self.command, input="original text", text=True, stdout=-1)
        self.assertEqual(mock_elem.text, "processed text")

if __name__ == '__main__':
    unittest.main()
