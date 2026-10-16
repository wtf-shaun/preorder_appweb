import os
import tempfile
from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import (
    grey,
    black,
    white,
    HexColor
)
from datetime import datetime


def generate_invoice_pdf(order_id, user, order_items, total, token=None):

    # Vercel's deployed application directory is read-only.
    # Use the writable temporary directory; the download route can regenerate
    # the invoice from the persistent order record if this file is unavailable.
    invoices_dir = os.path.join(
        tempfile.gettempdir(),
        "cafeteria_invoices"
    )

    os.makedirs(invoices_dir, exist_ok=True)

    file_path = os.path.join(
        invoices_dir,
        f"invoice_{order_id}.pdf"
    )

    c = canvas.Canvas(
        file_path,
        pagesize=A4
    )

    width, height = A4

    # =========================================================
    # COLORS
    # =========================================================

    ORANGE = HexColor("#FC8019")
    ORANGE_DARK = HexColor("#E96B10")
    ORANGE_LIGHT = HexColor("#FFF3E8")

    DARK = HexColor("#282C3F")
    GREY = HexColor("#6B7280")
    LIGHT_GREY = HexColor("#F5F5F5")
    BORDER = HexColor("#E5E7EB")
    GREEN = HexColor("#2E7D32")
    GREEN_LIGHT = HexColor("#EAF7EC")


    # =========================================================
    # HELPER FUNCTIONS
    # =========================================================

    def draw_round_rect(x, y, w, h, radius, fill, stroke=None):

        c.setFillColor(fill)

        if stroke:
            c.setStrokeColor(stroke)
            c.setLineWidth(0.8)
        else:
            c.setStrokeColor(fill)

        c.roundRect(
            x,
            y,
            w,
            h,
            radius,
            fill=1,
            stroke=1 if stroke else 0
        )


    def draw_header():

        # Header background
        c.setFillColor(DARK)

        c.rect(
            0,
            height - 4.3 * cm,
            width,
            4.3 * cm,
            fill=1,
            stroke=0
        )

        # Orange accent
        c.setFillColor(ORANGE)

        c.rect(
            0,
            height - 4.3 * cm,
            width,
            0.18 * cm,
            fill=1,
            stroke=0
        )

        # Logo
        logo_path = os.path.join(
            current_app.root_path,
            "static",
            "logo.png"
        )

        if os.path.exists(logo_path):

            try:
                c.drawImage(
                    logo_path,
                    width - 5.0 * cm,
                    height - 3.65 * cm,
                    width=2.8 * cm,
                    height=2.8 * cm,
                    preserveAspectRatio=True,
                    mask="auto"
                )
            except Exception:
                pass


        # Main title
        c.setFillColor(white)

        c.setFont(
            "Helvetica-Bold",
            22
        )

        c.drawString(
            2 * cm,
            height - 1.7 * cm,
            "CAFETERIA"
        )

        c.setFillColor(ORANGE)

        c.setFont(
            "Helvetica-Bold",
            13
        )

        c.drawString(
            2 * cm,
            height - 2.35 * cm,
            "ORDER RECEIPT"
        )


        # School
        c.setFillColor(
            HexColor("#D1D5DB")
        )

        c.setFont(
            "Helvetica",
            9
        )

        c.drawString(
            2 * cm,
            height - 3.05 * cm,
            "Tagore International School"
        )

        c.drawString(
            2 * cm,
            height - 3.45 * cm,
            "Cafeteria Pre-Order System"
        )


        # Invoice information

        c.setFillColor(
            HexColor("#D1D5DB")
        )

        c.setFont(
            "Helvetica",
            8
        )

        c.drawRightString(
            width - 2 * cm,
            height - 2.0 * cm,
            "ORDER REFERENCE"
        )

        c.setFillColor(white)

        c.setFont(
            "Helvetica-Bold",
            11
        )

        c.drawRightString(
            width - 2 * cm,
            height - 2.45 * cm,
            str(order_id)
        )

        c.setFillColor(
            HexColor("#D1D5DB")
        )

        c.setFont(
            "Helvetica",
            8
        )

        c.drawRightString(
            width - 2 * cm,
            height - 3.0 * cm,
            "ISSUED"
        )

        c.setFillColor(white)

        c.setFont(
            "Helvetica",
            9
        )

        c.drawRightString(
            width - 2 * cm,
            height - 3.4 * cm,
            datetime.now().strftime(
                "%d %b %Y  •  %I:%M %p"
            )
        )


    # =========================================================
    # HEADER
    # =========================================================

    draw_header()

    y = height - 5.2 * cm


    # =========================================================
    # ORDER STATUS
    # =========================================================

    draw_round_rect(
        2 * cm,
        y - 1.0 * cm,
        width - 4 * cm,
        1.0 * cm,
        8,
        GREEN_LIGHT
    )

    c.setFillColor(GREEN)

    c.setFont(
        "Helvetica-Bold",
        10
    )

    c.drawString(
        2.5 * cm,
        y - 0.42 * cm,
        "●  ORDER CONFIRMED"
    )

    c.setFillColor(
        HexColor("#4B5563")
    )

    c.setFont(
        "Helvetica",
        8.5
    )

    c.drawRightString(
        width - 2.5 * cm,
        y - 0.42 * cm,
        "Please present your pickup token at the cafeteria"
    )

    y -= 1.45 * cm


    # =========================================================
    # PICKUP TOKEN
    # =========================================================

    if token:

        draw_round_rect(
            2 * cm,
            y - 3.15 * cm,
            width - 4 * cm,
            3.15 * cm,
            12,
            ORANGE_LIGHT
        )

        # Small heading
        c.setFillColor(ORANGE_DARK)

        c.setFont(
            "Helvetica-Bold",
            10
        )

        c.drawCentredString(
            width / 2,
            y - 0.65 * cm,
            "YOUR PICKUP TOKEN"
        )

        # Huge token
        c.setFillColor(DARK)

        c.setFont(
            "Helvetica-Bold",
            34
        )

        c.drawCentredString(
            width / 2,
            y - 1.65 * cm,
            str(token)
        )

        # Instruction
        c.setFillColor(GREY)

        c.setFont(
            "Helvetica",
            8.5
        )

        c.drawCentredString(
            width / 2,
            y - 2.45 * cm,
            "Keep this number handy when collecting your order."
        )

        y -= 3.65 * cm


    # =========================================================
    # CUSTOMER DETAILS
    # =========================================================

    c.setFillColor(DARK)

    c.setFont(
        "Helvetica-Bold",
        12
    )

    c.drawString(
        2 * cm,
        y,
        "CUSTOMER DETAILS"
    )

    y -= 0.3 * cm

    c.setStrokeColor(BORDER)

    c.setLineWidth(0.8)

    c.line(
        2 * cm,
        y,
        width - 2 * cm,
        y
    )

    y -= 0.65 * cm


    customer_box_height = 1.65 * cm

    draw_round_rect(
        2 * cm,
        y - customer_box_height,
        width - 4 * cm,
        customer_box_height,
        8,
        LIGHT_GREY,
        BORDER
    )


    # Customer name

    c.setFillColor(GREY)

    c.setFont(
        "Helvetica",
        8
    )

    c.drawString(
        2.5 * cm,
        y - 0.5 * cm,
        "CUSTOMER"
    )

    c.setFillColor(DARK)

    c.setFont(
        "Helvetica-Bold",
        10
    )

    c.drawString(
        2.5 * cm,
        y - 0.95 * cm,
        user.get(
            "username",
            "Student"
        )
    )


    # Email

    c.setFillColor(GREY)

    c.setFont(
        "Helvetica",
        8
    )

    c.drawString(
        11 * cm,
        y - 0.5 * cm,
        "EMAIL"
    )

    c.setFillColor(DARK)

    c.setFont(
        "Helvetica",
        9
    )

    c.drawString(
        11 * cm,
        y - 0.95 * cm,
        user.get(
            "email",
            ""
        )
    )

    y -= 2.2 * cm


    # =========================================================
    # ORDER DETAILS
    # =========================================================

    c.setFillColor(DARK)

    c.setFont(
        "Helvetica-Bold",
        12
    )

    c.drawString(
        2 * cm,
        y,
        "ORDER DETAILS"
    )

    y -= 0.3 * cm

    c.setStrokeColor(BORDER)

    c.line(
        2 * cm,
        y,
        width - 2 * cm,
        y
    )

    y -= 0.65 * cm


    # Table header

    table_left = 2 * cm
    table_right = width - 2 * cm

    c.setFillColor(DARK)

    c.rect(
        table_left,
        y - 0.75 * cm,
        table_right - table_left,
        0.75 * cm,
        fill=1,
        stroke=0
    )

    c.setFillColor(white)

    c.setFont(
        "Helvetica-Bold",
        8.5
    )

    c.drawString(
        table_left + 0.3 * cm,
        y - 0.47 * cm,
        "ITEM"
    )

    c.drawRightString(
        12.2 * cm,
        y - 0.47 * cm,
        "QTY"
    )

    c.drawRightString(
        15.0 * cm,
        y - 0.47 * cm,
        "PRICE"
    )

    c.drawRightString(
        table_right - 0.3 * cm,
        y - 0.47 * cm,
        "SUBTOTAL"
    )

    y -= 0.75 * cm


    # =========================================================
    # ITEMS
    # =========================================================

    c.setFont(
        "Helvetica",
        9
    )

    for index, item in enumerate(order_items):

        # Estimate row height
        row_height = 0.72 * cm

        # New page if necessary
        if y < 5 * cm:

            c.showPage()

            draw_header()

            y = height - 5.2 * cm

            c.setFillColor(DARK)

            c.setFont(
                "Helvetica-Bold",
                12
            )

            c.drawString(
                2 * cm,
                y,
                "ORDER DETAILS — CONTINUED"
            )

            y -= 0.5 * cm


        # Alternating row background

        if index % 2 == 0:

            c.setFillColor(
                HexColor("#FAFAFA")
            )

            c.rect(
                table_left,
                y - row_height,
                table_right - table_left,
                row_height,
                fill=1,
                stroke=0
            )


        # Item name

        c.setFillColor(DARK)

        c.setFont(
            "Helvetica",
            9
        )

        item_name = str(
            item.get(
                "name",
                "Item"
            )
        )

        # Prevent extremely long names
        if len(item_name) > 42:
            item_name = item_name[:39] + "..."

        c.drawString(
            table_left + 0.3 * cm,
            y - 0.45 * cm,
            item_name
        )


        # Quantity

        c.drawRightString(
            12.2 * cm,
            y - 0.45 * cm,
            str(item.get("qty", 0))
        )


        # Price

        c.drawRightString(
            15.0 * cm,
            y - 0.45 * cm,
            f"Rs {item.get('price', 0)}"
        )


        # Subtotal

        c.setFont(
            "Helvetica-Bold",
            9
        )

        c.drawRightString(
            table_right - 0.3 * cm,
            y - 0.45 * cm,
            f"Rs {item.get('subtotal', 0)}"
        )


        # Row divider

        c.setStrokeColor(
            HexColor("#EEEEEE")
        )

        c.line(
            table_left,
            y - row_height,
            table_right,
            y - row_height
        )

        y -= row_height


    # =========================================================
    # TOTAL
    # =========================================================

    y -= 0.5 * cm

    total_box_height = 1.55 * cm

    draw_round_rect(
        9.5 * cm,
        y - total_box_height,
        width - 11.5 * cm,
        total_box_height,
        9,
        ORANGE_LIGHT,
        HexColor("#FFD9B5")
    )

    c.setFillColor(
        HexColor("#704016")
    )

    c.setFont(
        "Helvetica-Bold",
        10
    )

    c.drawString(
        10 * cm,
        y - 0.58 * cm,
        "TOTAL AMOUNT"
    )

    c.setFillColor(ORANGE_DARK)

    c.setFont(
        "Helvetica-Bold",
        17
    )

    c.drawRightString(
        width - 2.5 * cm,
        y - 1.08 * cm,
        f"Rs {total}"
    )

    y -= 2.1 * cm


    # =========================================================
    # PICKUP INFORMATION
    # =========================================================

    if y < 5.5 * cm:

        c.showPage()

        draw_header()

        y = height - 5.2 * cm


    c.setFillColor(DARK)

    c.setFont(
        "Helvetica-Bold",
        11
    )

    c.drawString(
        2 * cm,
        y,
        "PICKUP INFORMATION"
    )

    y -= 0.55 * cm

    pickup_info = [
        "1. Proceed to the cafeteria pickup counter.",
        "2. Show your pickup token to the cafeteria staff.",
        "3. Verify your order before leaving the counter.",
        "4. Keep this receipt for your order reference."
    ]

    c.setFont(
        "Helvetica",
        8.5
    )

    for line in pickup_info:

        c.setFillColor(ORANGE)

        c.circle(
            2.2 * cm,
            y + 0.04 * cm,
            0.07 * cm,
            fill=1,
            stroke=0
        )

        c.setFillColor(GREY)

        c.drawString(
            2.55 * cm,
            y,
            line
        )

        y -= 0.43 * cm


    # =========================================================
    # FOOTER
    # =========================================================

    c.setStrokeColor(BORDER)

    c.line(
        2 * cm,
        2.25 * cm,
        width - 2 * cm,
        2.25 * cm
    )

    c.setFillColor(GREY)

    c.setFont(
        "Helvetica",
        8
    )

    c.drawCentredString(
        width / 2,
        1.8 * cm,
        "Thank you for using the Cafeteria Pre-Order System"
    )

    c.setFont(
        "Helvetica",
        7.5
    )

    c.drawCentredString(
        width / 2,
        1.4 * cm,
        f"Order Reference: {order_id}  •  Generated: "
        f"{datetime.now().strftime('%d %b %Y, %I:%M %p')}"
    )

    c.setFillColor(
        HexColor("#AAAAAA")
    )

    c.setFont(
        "Helvetica",
        7
    )

    c.drawCentredString(
        width / 2,
        0.95 * cm,
        "This document is an electronically generated cafeteria order receipt."
    )


    # =========================================================
    # SAVE
    # =========================================================

    c.showPage()

    c.save()

    return file_path
