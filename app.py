import streamlit as st
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm

st.title("PSO Petrol Pump – Combined PDF Billing System with Summary")

# --- INPUT SECTION ---
st.header("Customer & Billing Information")
customer_name = st.text_input("Customer Name")
account_number = st.text_input("Account Number")
billing_from = st.text_input("Billing From (e.g., 01-Sep-2025)")
billing_to = st.text_input("Billing To (e.g., 30-Sep-2025)")
start_invoice = st.number_input("Starting Invoice Number", min_value=1, value=1)
slip_date = st.text_input("Slip Date (e.g., Sep-2025)")

st.write("----")
st.header("Upload Vehicles & Amounts File")
uploaded_file = st.file_uploader(
    "Upload Excel/CSV with columns: Vehicle, Amount, StartSlip, Product, Rate",
    type=["xlsx","csv"]
)

styles = getSampleStyleSheet()
centered_style = ParagraphStyle(name="CenterTitle", parent=styles['Title'], alignment=TA_CENTER)
LITRES_PER_SLIP = 40

# Clean footer function — ONLY page number (no duplicate pages)
def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(200*mm, 10*mm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()

# --------------------------
# Processing
# --------------------------
if uploaded_file and customer_name and slip_date and account_number:

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.dataframe(df)

    if st.button("Generate Combined PDF Invoice"):

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=50
        )

        elements = []
        invoice_number = start_invoice

        # =======================
        # SUMMARY PAGE
        # =======================
        elements.append(Paragraph("<b>NOOR PETROLEUM SERVICES</b>", styles['Title']))
        elements.append(Spacer(1,10))
        elements.append(Paragraph("<b>Invoice Summary</b>", centered_style))
        elements.append(Spacer(1,10))

        summary_data = [["Vehicle No.", "Invoice No", "Product", "Amount (Rs)", "Total Qty (Ltr)"]]

        overall_amount = 0
        overall_liters = 0

        for i, row in df.iterrows():
            vehicle = str(row["Vehicle"])
            total_amount = float(row["Amount"])
            product = str(row["Product"])
            rate = float(row["Rate"])
            slip_no = int(row["StartSlip"])
            remaining = total_amount
            total_liters_vehicle = 0
            total_amount_vehicle = 0

            while remaining > 0:
                slip_liters = LITRES_PER_SLIP
                slip_amount = slip_liters * rate

                if slip_amount > remaining:
                    slip_liters = int(remaining / rate)
                    slip_amount = slip_liters * rate
                    if slip_liters <= 0:
                        break

                total_liters_vehicle += slip_liters
                total_amount_vehicle += slip_amount
                remaining -= slip_amount
                slip_no += 1

            summary_data.append([
                vehicle,
                f"INV-{invoice_number+i:04d}",
                product,
                f"{total_amount_vehicle:,.2f}",
                total_liters_vehicle
            ])

            overall_amount += total_amount_vehicle
            overall_liters += total_liters_vehicle

        summary_data.append(["", "Total", "", f"{overall_amount:,.2f}", overall_liters])

        summary_table = Table(summary_data, colWidths=[100, 80, 80, 100, 100])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#d9d9d9")),
            ("BOX", (0,0), (-1,-1), 1, colors.black),
            ("INNERGRID", (0,0), (-1,-1), 0.4, colors.black),
            ("ALIGN", (1,0), (-1,-1), "CENTER"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
            ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#f2f2f2")),
        ]))
        elements.append(summary_table)
        elements.append(PageBreak())

        # =======================
        # INDIVIDUAL INVOICE PAGES
        # =======================
        for idx, row in df.iterrows():
            vehicle = str(row["Vehicle"])
            total_amount = float(row["Amount"])
            slip_no = int(row["StartSlip"])
            product = str(row["Product"])
            rate = float(row["Rate"])

            # Header
            elements.append(Paragraph("<b>NOOR PETROLEUM SERVICES</b>", styles['Title']))
            elements.append(Paragraph(f"<b>INVOICE # INV-{invoice_number:04d}</b>", styles['Heading2']))
            elements.append(Spacer(1,10))

            # === FIXED: Now 2-column header (no empty column) ===
            header_data = [
                ["Customer Name:", customer_name],
                ["Account #:", account_number],
                ["Billing Period:", f"From {billing_from} To {billing_to}"]
            ]
            t = Table(header_data, colWidths=[130, 380])  # 2 columns only
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (0,-1), colors.lightgrey),
                ("BOX", (0,0), (-1,-1), 1, colors.black),
                ("INNERGRID", (0,0), (-1,-1), 0.5, colors.black),
                ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
                ("ALIGN", (0,0), (-1,-1), "LEFT"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ]))
            elements.append(t)
            elements.append(Spacer(1,15))

            elements.append(Paragraph(f"<b>Vehicle: {vehicle}</b>", styles['Heading2']))
            elements.append(Spacer(1,10))

            table_data = [["S.No","Slip Date","Slip #","Product","Qty (Ltr)","Rate","Amount (Rs)"]]
            s_no = 1
            remaining_amount = total_amount
            total_liters = 0
            subtotal = 0

            while remaining_amount > 0:
                slip_liters = LITRES_PER_SLIP
                slip_amount = slip_liters * rate

                if slip_amount > remaining_amount:
                    slip_liters = int(remaining_amount / rate)
                    slip_amount = slip_liters * rate
                    if slip_liters <= 0:
                        break

                table_data.append([s_no, slip_date, slip_no, product, slip_liters, rate, f"{slip_amount:,.2f}"])
                total_liters += slip_liters
                subtotal += slip_amount
                remaining_amount -= slip_amount
                s_no += 1
                slip_no += 1

            table_data.append(["", "", "", "Total", total_liters, "", f"{subtotal:,.2f}"])

            slip_table = Table(table_data, colWidths=[40,70,70,60,80,60,80])
            slip_table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#d9d9d9")),
                ("BOX", (0,0), (-1,-1), 1, colors.black),
                ("INNERGRID", (0,0), (-1,-1), 0.4, colors.black),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
                ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#f2f2f2")),
            ]))
            elements.append(slip_table)

            # Signature
            elements.append(Spacer(1,40))
            elements.append(Paragraph("_____________________", styles['Normal']))
            elements.append(Paragraph("<b>Signature</b>", styles['Normal']))
            elements.append(PageBreak())
            invoice_number += 1

        # ONLY CHANGE: Replaced canvasmaker with clean footer
        doc.build(
            elements,
            onFirstPage=add_page_number,
            onLaterPages=add_page_number
        )
        buffer.seek(0)

        st.download_button(
            label="Download Combined Invoice PDF",
            data=buffer,
            file_name="Combined_Invoices.pdf",
            mime="application/pdf"
        )
        st.success("PDF generated successfully!.")
