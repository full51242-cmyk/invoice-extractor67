import argparse
import base64
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

try:
    from langchain_mistralai import ChatMistralAI
    from langchain_core.messages import HumanMessage
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: install the required packages first.\n"
        "Example: pip install langchain-mistralai langchain-core pydantic"
    ) from exc


# 1. Output Structure Define Karein (Pydantic Model)
class LineItem(BaseModel):
    item_description: str = Field(description="The description of the item purchased")
    quantity: int = Field(description="The quantity of the item")
    price: float = Field(description="The unit price or total price of this item")


class InvoiceExtractor(BaseModel):
    vendor_name: str = Field(description="The name of the company or store issuing the invoice")
    invoice_date: Optional[str] = Field(description="The date of the invoice (YYYY-MM-DD format if possible)")
    total_amount: float = Field(description="The total amount paid or due on the invoice")
    currency: str = Field(description="The currency of the invoice (e.g., USD, INR, EUR)")
    items: List[LineItem] = Field(description="List of all items mentioned in the invoice")


# 2. Image ko Base64 mein convert karne ka function
def encode_image(image_path: Path) -> str:
    with image_path.open("rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def resolve_image_path(image_path: Optional[str] = None) -> Path:
    possible_paths: List[Path] = []

    if image_path:
        possible_paths.append(Path(image_path))
    else:
        possible_paths.append(Path("invoice.jpg"))

    search_roots = [Path.cwd(), Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent]

    if not image_path:
        for root in search_roots:
            for pattern in ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp"):
                possible_paths.extend(root.glob(pattern))

    seen = set()
    for candidate in possible_paths:
        if not candidate.is_absolute():
            for root in search_roots:
                full_candidate = (root / candidate).resolve()
                if full_candidate in seen:
                    continue
                seen.add(full_candidate)
                if full_candidate.exists() and full_candidate.is_file():
                    return full_candidate
        else:
            absolute_candidate = candidate.resolve()
            if absolute_candidate in seen:
                continue
            seen.add(absolute_candidate)
            if absolute_candidate.exists() and absolute_candidate.is_file():
                return absolute_candidate

    raise FileNotFoundError(
        "No image file found. Place an image file in the project folder or pass its path, for example:\n"
        "python .venv/nvoice.py invoice.jpg"
    )


def render_html_report(invoice: InvoiceExtractor, image_path: Path) -> str:
    items_html = ""
    for item in invoice.items:
        items_html += f"<tr><td>{item.item_description}</td><td>{item.quantity}</td><td>{item.price:.2f}</td></tr>"

    encoded_image = ""
    try:
        with image_path.open("rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    except Exception:
        encoded_image = ""

    return f"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Invoice Extraction Report</title>
        <style>
          body {{
            margin: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(180deg, #fef2f2 0%, #eff6ff 50%, #ffffff 100%);
            color: #0f172a;
          }}
          .container {{
            max-width: 980px;
            margin: 24px auto;
            padding: 24px;
          }}
          .card {{
            background: linear-gradient(180deg, #3b82f6 0%, #2563eb 50%, #1d4ed8 100%);
            color: #ffffff;
            border-radius: 24px;
            box-shadow: 0 24px 60px rgba(30, 64, 175, 0.2);
            padding: 34px;
            border: 1px solid rgba(147, 197, 253, 0.4);
          }}
          .hero {{
            margin-bottom: 24px;
          }}
          .hero h1 {{
            margin: 0 0 10px;
            font-size: 2.5rem;
            color: #dc2626;
            text-shadow: 0 2px 8px rgba(220, 38, 38, 0.18);
          }}
          .hero p {{
            margin: 0;
            color: #334155;
            font-size: 1rem;
          }}
          .summary-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 18px;
            margin-top: 24px;
          }}
          .summary-item {{
            padding: 20px;
            border-radius: 18px;
            background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
            border: 1px solid rgba(147, 197, 253, 0.35);
          }}
          .summary-item strong {{
            display: block;
            margin-bottom: 10px;
            color: #f8fafc;
          }}
          .summary-item span {{
            color: #0f172a;
            font-size: 1.05rem;
            font-weight: 600;
          }}
          table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 28px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 18px;
            overflow: hidden;
            color: #f8fafc;
          }}
          th, td {{
            text-align: left;
            padding: 16px 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.16);
          }}
          th {{
            background: #fee2e2;
            color: #1d4ed8;
          }}
          tr:nth-child(even) {{
            background: #eff6ff;
          }}
          .invoice-image {{
            margin-top: 28px;
            text-align: center;
          }}
          .invoice-image img {{
            max-width: 100%;
            border-radius: 20px;
            border: 2px solid #93c5fd;
            box-shadow: 0 18px 40px rgba(37, 99, 235, 0.12);
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="card">
            <div class="hero">
              <h1>Invoice Extraction Report</h1>
              <p>Invoice data extracted successfully with structured results and styled HTML output.</p>
            </div>
            <div class="summary-grid">
              <div class="summary-item">
                <strong>Vendor Name</strong>
                <span>{invoice.vendor_name}</span>
              </div>
              <div class="summary-item">
                <strong>Invoice Date</strong>
                <span>{invoice.invoice_date or 'Not available'}</span>
              </div>
              <div class="summary-item">
                <strong>Total Amount</strong>
                <span>{invoice.currency} {invoice.total_amount:.2f}</span>
              </div>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Description</th>
                  <th>Quantity</th>
                  <th>Price</th>
                </tr>
              </thead>
              <tbody>
                {items_html}
              </tbody>
            </table>
            {f'<div class="invoice-image"><img src="data:image/jpeg;base64,{encoded_image}" alt="Invoice image" /></div>' if encoded_image else ''}
          </div>
        </div>
      </body>
    </html>
    """


def write_html_report(html: str, output_path: Path) -> None:
    output_path.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract invoice data using a vision model")
    parser.add_argument("image_path", nargs="?", help="Path to the invoice or receipt image")
    args = parser.parse_args()

    image_path = resolve_image_path(args.image_path)
    print(f"Using image: {image_path}")

    base64_image = encode_image(image_path)

    llm = ChatMistralAI(model="pixtral-12b-latest", temperature=0)
    structured_llm = llm.with_structured_output(InvoiceExtractor)

    message = HumanMessage(
        content=[
            {"type": "text", "text": "Analyze this invoice/receipt image. Extract the vendor name, date, total amount, currency, and all individual line items accurately into the requested schema."},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            },
        ]
    )

    print("Mistral AI se data extract ho raha hai...")
    try:
        response = structured_llm.invoke([message])
        invoice = response
        html_report = render_html_report(invoice, image_path)
        report_path = Path("invoice_report.html")
        write_html_report(html_report, report_path)

        print("\n--- Extracted Data ---")
        print(invoice.model_dump_json(indent=4))
        print(f"\nHTML report generated: {report_path.resolve()}")
    except Exception as exc:
        print(f"Error occurred: {exc}")


if __name__ == "__main__":
    main()