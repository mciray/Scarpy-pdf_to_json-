import os
import io
import re
import scrapy
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()
SEARCH_URL = os.getenv('ACARINDEX.SEARCH_URL')
SCRAP_START_INDEX = int(os.getenv('ACARINDEX.SCRAP_START_INDEX'))
SCRAP_END_INDEX = int(os.getenv('ACARINDEX.SCRAP_END_INDEX'))
SCRAP_INTERRUPTED_INDEX = int(os.getenv('ACARINDEX.SCRAP_INTERRUPTED_INDEX'))
# SCRAP_START_INDEX = 526495
# SCRAP_END_INDEX = 750000


class PdfSpider(scrapy.Spider):
    name = "pdf_spider"
    start_urls = [f'{SEARCH_URL}{i}' for i in range(SCRAP_START_INDEX + SCRAP_INTERRUPTED_INDEX, SCRAP_END_INDEX)]
    counter = SCRAP_START_INDEX
    
    def parse(self, response):
        # iframe'i bul ve src URL'sini elde et
        iframe_src = response.xpath('//iframe/@src').get()
        if iframe_src:
            yield scrapy.Request(iframe_src, callback=self.parse_pdf)
        else:
            # iframe src'si bulunamadıysa, bilgi mesajı günlüğe kaydedilir
            self.logger.info(f"No iframe src found in {response.url}")


    def parse_pdf(self, response):
        pdf_content = response.body
        pdf_text = self.extract_pdf_text(pdf_content)

        # Eğer pdf_text boş ise, bu PDF'i es geç
        if pdf_text:
            self.logger.info(f"Text extracted from PDF: {response.url}")
            self.counter += 1
            yield {
                'service': 'ACARINDEX',
                'pdf-no':SCRAP_INTERRUPTED_INDEX + self.counter,
                'url': response.url,
                'text': pdf_text,
            }
        else:
            self.logger.info(f"No text extracted from PDF: {response.url}")

    def extract_pdf_text(self, pdf_content):
        text = ""
        try:
            with io.BytesIO(pdf_content) as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    # clear \n with
                    text += self.clean_text(page.extract_text())
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {e}")
            return ""
        return text
    
    def clean_text(self, text):
        # İki veya daha fazla boşluğu tek boşlukla değiştir
        text = re.sub(r'\s{2,}', ' ', text)
        # '\n' karakterlerini sil
        text = text.replace('\n', '')
        return text
    