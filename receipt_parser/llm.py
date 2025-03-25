import base64
import hashlib
import json
from io import BytesIO
from pathlib import Path

import pdf2image
from openai import OpenAI
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()
client = OpenAI()


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


def get_prompt(img_paths: list[str]) -> dict:
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
                    total_gross_amount: number,
                    total_net_amount: number,
                    vat_amount: number,
                    company_name: string
                    description: string
                    is_credit: boolean.
                }."""
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
                        "text": "Extract: Receipt number, Date, Total gross amount, total net amount, VAT amount, company name, descriptuon and is_credit. ",
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
