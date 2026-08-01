import base64
import os
from pathlib import Path
from typing import List, Optional

import streamlit as st
from pydantic import BaseModel, Field

try:
    from langchain_mistralai import ChatMistralAI
    from langchain_core.messages import HumanMessage
except ImportError as exc:
    st.error(
        "Missing dependency: install the required packages first.\n"
        "Example: pip install langchain-mistralai langchain-core pydantic streamlit"
    )
    st.stop()


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


def encode_image_bytes(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def render_html_report(invoice: InvoiceExtractor, encoded_image: str) -> str:
    items_html = ""
    for item in invoice.items:
        items_html += f"<tr><td>{item.item_description}</td><td>{item.quantity}</td><td>{item.price:.2f}</td></tr>"

    return f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(180deg, #3b82f6 0%, #2563eb 50%, #1d4ed8 100%);
                color: #ffffff; border-radius: 24px; padding: 34px;
                border: 1px solid rgba(147, 197, 253, 0.4);">
      <h1 style="color:#fee2e2;">Invoice Extraction Report</h1>
      <div style="display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:18px; margin-top:24px;">
        <div style="padding:20px; border-radius:18px; background:linear-gradient(135deg,#1e3a8a,#2563eb);">
          <strong>Vendor Name</strong><br><span>{invoice.vendor_name}</span>
        </div>
        <div style="padding:20px; border-radius:18px; background:linear-gradient(135deg,#1e3a8a,#2563eb);">
          <strong>Invoice Date</strong><br><span>{invoice.invoice_date or 'Not available'}</span>
        </div>
        <div style="padding:20px; border-radius:18px; background:linear-gradient(135deg,#1e3a8a,#2563eb);">
          <strong>Total Amount</strong><br><span>{invoice.currency} {invoice.total_amount:.2f}</span>
        </div>
      </div>
      <table style="width:100%; border-collapse:collapse; margin-top:28px; background:rgba(255,255,255,0.08); border-radius:18px; overflow:hidden;">
        <thead>
          <tr style="background:#fee2e2; color:#1d4ed8;">
            <th style="text-align:left; padding:16px 14px;">Description</th>
            <th style="text-align:left; padding:16px 14px;">Quantity</th>
            <th style="text-align:left; padding:16px 14px;">Price</th>
          </tr>
        </thead>
        <tbody>{items_html}</tbody>
      </table>
    </div>
    """


def main() -> None:
    st.set_page_config(page_title="AI Invoice Extractor", page_icon="🧾", layout="centered")
    st.title("🧾 AI Invoice Extractor")
    st.write("Apna invoice ya receipt image upload karein, AI usse structured data mein extract kar dega.")

    # Mistral API key: Streamlit Secrets se leke environment variable set karein
    if "MISTRAL_API_KEY" in st.secrets:
        os.environ["MISTRAL_API_KEY"] = st.secrets["MISTRAL_API_KEY"]

    uploaded_file = st.file_uploader("Invoice image upload karein", type=["jpg", "jpeg", "png", "webp", "bmp"])

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Invoice", use_container_width=True)

        if st.button("Extract Data"):
            with st.spinner("Mistral AI se data extract ho raha hai..."):
                try:
                    image_bytes = uploaded_file.read()
                    base64_image = encode_image_bytes(image_bytes)

                    llm = ChatMistralAI(model="pixtral-12b-latest", temperature=0)
                    structured_llm = llm.with_structured_output(InvoiceExtractor)

                    message = HumanMessage(
                        content=[
                            {"type": "text", "text": "Analyze this invoice/receipt image. Extract the vendor name, date, total amount, currency, and all individual line items accurately into the requested schema."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        ]
                    )

                    response = structured_llm.invoke([message])
                    invoice = response

                    st.success("Data extract ho gaya!")
                    html_report = render_html_report(invoice, base64_image)
                    st.markdown(html_report, unsafe_allow_html=True)

                    with st.expander("Raw JSON dekhein"):
                        st.json(invoice.model_dump())

                except Exception as exc:
                    st.error(f"Error occurred: {exc}")


if __name__ == "__main__":
    main()