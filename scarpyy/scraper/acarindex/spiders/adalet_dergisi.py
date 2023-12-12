import re
import os
import io
import scrapy
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()

SEARCH_URL = os.getenv('ADALET.DERGISI.SEARCH_URL')


class AdaletDergisiSpider(scrapy.Spider):
    name = "adalet-dergisi"
    start_urls = [SEARCH_URL]
    count = 0

    def parse(self, response):
        # Sayfadaki tüm linklere git
        magazines = response.css('div.panel-body a::attr(href)').getall()
        for index, link in enumerate(magazines):
            full_url = response.urljoin(link)
            self.logger.info(f'{index+1}/{len(magazines)} url:{full_url}')
            yield scrapy.Request(full_url, callback=self.parse_article)

    def parse_article(self, response):
        self.logger.info(f'Text extracting starting...')
        # PDF linklerini doğrudan sayfadan çek
        pdf_links = response.css('a[href$=".pdf"]::attr(href)').getall()
        for pdf_link in pdf_links:
            full_pdf_url = response.urljoin(pdf_link)
            yield scrapy.Request(full_pdf_url, callback=self.parse_pdf)
        


    def parse_pdf(self, response):
        # PDF içeriğini çek ve metin olarak işle
        pdf_content = response.body
        pdf_text = self.extract_pdf_text(pdf_content)
        if pdf_text:
            self.logger.info(f"Text extracted from PDF: {response.url}")
            self.count += 1
            yield {
                'service': 'ADALETDERGISI',
                'url': response.url,
                'text': pdf_text,
                'pdf-no': self.count
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