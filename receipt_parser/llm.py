import base64
import hashlib
import json
from enum import Enum
from io import BytesIO
from pathlib import Path

import pdf2image
from openai import OpenAI
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()
client = OpenAI()


class Prompt(Enum):
    DEFAULT = "Standard"
    WOCHENMARKT = "Wochenmarkt"
    KEMMTS_EINA = "Kemmts Eina"
    CUSTOM = "Manuelle Eingabe"


def encode_image(img):
    img = ImageOps.exif_transpose(img)
    img.thumbnail((1920, 1080))
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    base64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return base64_img


def encode_pdf(pdf_path):
    images = pdf2image.convert_from_path(pdf_path)
    base64_images = [encode_image(img) for img in images]
    return base64_images


def get_prompt_text(prompt_type, custom_prompt=None):
    if prompt_type == Prompt.CUSTOM:
        return custom_prompt
    product_examples = """
Each receipt may have a list of products. Each product has:
- name: string (required)
- is_bio: boolean (required)
- bio_category: enum (optional, only if is_bio is true)
- amount: float (required)
- unit: string (required, e.g. 'KILO', 'LITER', 'PIECE')

BioCategory possible values:
- Vermarktung/Verarbeitung: e.g. Olivenöl, Lab, Kulturen, Salz, Kräuter, Honig, Essig, usw.
- Pflanzenbau/Saatgut: e.g. Jungpflanzen, Weizensaat, Grünlandmischung usw.
- Tierhaltung- Dünger/Einstreu/Futter: e.g. Sägespäne, Euterwolle, Euterpflege, Mineralfutter, Alpenkorn, Gerste, Stroh usw.

If bio_category is set, is_bio must be true.
"""
    if prompt_type == Prompt.WOCHENMARKT:
        return (
            "Extract: Receipt number, Date, Total gross amount, total net amount, VAT amount, company name, description, is_credit, and a list of products. "
            + product_examples
            + " Note: Here we have a receipt from the weekly market. The weekly market is done by two framers and only one of them is relevant for us. Extract the text from the small sheet with the title 'Verkäufe pro Warengruppe'. Then number '1' with Warengruppe 'HIASN' is relevant and should be extracted as the GROSS amount. The VAT always is 10% from the GROSS amount. The NET amount is the GROSS amount minus the VAT. The company name should be 'Marktwagen'. The description should be 'Marktwagen' as well. The 'is_credit' should be 'True' as it is a credit note."
        )
    if prompt_type == Prompt.KEMMTS_EINA:
        return (
            "Extract: Receipt number, Date, Total gross amount, total net amount, VAT amount, company name, description, is_credit, and a list of products. "
            + product_examples
            + " Note: This is a receipt from our local market, hence is_credit is true. The company name is 'Kemmts Eina'. The VAT is 10% from the GROSS amount."
        )
    return (
        "Extract: Receipt number, Date, Total gross amount, total net amount, VAT amount, company name, description, is_credit, and a list of products. "
        + product_examples
    )


def get_prompt(
    img_paths: list[str], prompt_type: Prompt, custom_prompt: str | None
) -> dict:
    base64_images = [
        encode_image(Image.open(img_path))
        for img_path in img_paths
        if not img_path.endswith(".pdf")
    ]
    base64_images += [
        base64_image
        for pdf_path in img_paths
        if pdf_path.endswith(".pdf")
        for base64_image in encode_pdf(pdf_path)
    ]
    print(get_prompt_text(prompt_type, custom_prompt))
    return {
        "model": "chatgpt-4o-latest",
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "You are an expert receipt extraction algorithm. "
                "Only extract relevant information from the text. "
                "If you do not know the value of an attribute asked to extract, "
                "return null for the attribute's value. The language is German and the most receipts are from Austria. Your clients are Austrian farmers that you help with digitalizing their receipts. "
                "You always respond in JSON format with the following schema:"
                """{
                    receipt_number: string, 
                    date: string (format: YYYY-MM-DD),
                    total_gross_amount: float,
                    total_net_amount: float,
                    vat_amount: float,
                    company_name: string
                    description: string
                    is_bio: boolean,
                    is_credit: boolean.
                    products: Product[]
                }."""
                """
                Product is defined as:
                product = {
                    name: string
                    amount: float,
                    unit: ProductUnit,
                    price: float
                    bio_category: BioCategory (optional, only if is_bio is true)
                }."""
                "ProductUnit is an enum with the following values: 'KILO', 'LITER', 'PIECE'."
                "BioCategory is an enum with the following values: 'Vermarktung/Verarbeitung', 'Pflanzenbau', 'Tierhaltung'."
                "null is allowed for any attribute. (Do not use 'null', but null as a value.)"
                "The description should also be in German and should briefly describe the products or services bought."
                "The 'is_credit' flag determines if it is a receipt (false) or a credit note (true). E.g. for milk, cheese or wood it often is a credit note, as we earn money from that. Mostly, thouugh it is a receipt."
                "Some receipt include handwritten text. This text is more important than the printed text."
                "If some of the articles are crossed out, ignore them and adapt the total amounts.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": get_prompt_text(prompt_type, custom_prompt),
                    },
                    *[
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        }
                        for base64_image in base64_images
                    ],
                ],
            },
        ],
        "max_tokens": 300,
    }


def query_openai(query_dict: dict):
    if not Path("cache.json").exists():
        empty_dict = {}
        Path("cache.json").write_text(json.dumps(empty_dict))

    cache = json.loads(Path("cache.json").read_text())
    hashed = hashlib.md5(json.dumps(query_dict).encode()).hexdigest()
    if hashed in cache:
        print("Cache hit!")
        return cache[hashed]
    else:
        response = client.chat.completions.create(**query_dict)
        response_string = response.choices[0].message.content
        cache[hashed] = response_string
        Path("cache.json").write_text(json.dumps(cache))
        return response_string
