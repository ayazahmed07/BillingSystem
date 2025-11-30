import streamlit as st
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

st.title("🚛 PSO Petrol Pump – Combined PDF Billing System with Summary")

# --- INPUT SECTION FIRST ---
st.header("Customer & Billing Information")
customer_name = st.text_input("Customer Name")
account_number = st.text_input("Account Number")
billing_from = st.text_input("Billing From (e.g., 01-Sep-2025)")
billing_to = st.text_input("Billing To (e.g., 30-Sep-2025)")
rate = st.number_input("Rate per Liter", min_value=1.0, value=275.0)
slip_date = st.text_input("Slip Date (e.g., Sep-2025)")
start_invoice = st.number_input("Starting Invoice Number", min_value=1, value=1)

st.write("----")
st.header("Upload Vehicles & Amounts File")
uploaded_file = st.file_uploader("Upload Excel/CSV with columns: Vehicle, Amount, StartSlip", type=["xlsx", "csv"])

styles = getSampleStyleSheet()
centered_style = ParagraphStyle(name="Center", parent=styles['Title'], alignment=TA_CENTER)

LITRES_PER_SLIP = 40  # Updated from 25 to 40 liters

if uploaded_file and customer_name and slip_date and account_number:

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.dataframe(df)

    if st.button("Generate Combined PDF Invoice"):

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        elements = []

        invoice_number = start_invoice

        # --- SUMMARY PAGE ---
        elements.append(Paragraph("<b>NOOR PETROLEUM SERVICES</b>", styles['Title']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("<b>Invoice Summary</b>", centered_style))
        elements.append(Spacer(1, 10))

        summary_data = [["Vehicle No.", "Invoice No", "Amount (Rs)", "Total Qty (Ltr)"]]

        for i, row in df.iterrows():
            vehicle = str(row["Vehicle"])
            total_amount = float(row["Amount"])
            total_qty = round(total_amount / rate, 2)
            summary_data.append([vehicle, f"INV-{invoice_number+i:04d}", f"{total_amount:,.2f}", total_qty])

        total_amount_all = df["Amount"].sum()
        total_qty_all = round(total_amount_all / rate, 2)
        summary_data.append(["", "Total", f"{total_amount_all:,.2f}", total_qty_all])

        summary_table = Table(summary_data, colWidths=[150, 100, 100, 100])
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

        # --- INDIVIDUAL VEHICLE INVOICES ---
        for idx, row in df.iterrows():
            vehicle = str(row["Vehicle"])
            total_amount = float(row["Amount"])
            slip_no = int(row["StartSlip"])

            # Header
            elements.append(Paragraph("<b>NOOR PETROLEUM SERVICES</b>", styles['Title']))
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"<b>INVOICE # INV-{invoice_number:04d}</b>", styles['Heading2']))
            elements.append(Spacer(1, 10))

            # Vehicle / Billing Info Table (Customer Name, Account, Billing Period)
            header_data = [
                ["Customer Name:", customer_name, "", ""],
                ["Account #:", account_number, "", ""],
                ["Billing Period:", f"From: {billing_from}", "", f"To: {billing_to}"]
            ]

            t = Table(header_data, colWidths=[120, 180, 80, 100])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
                ("BOX", (0,0), (-1,-1), 1, colors.black),
                ("INNERGRID", (0,0), (-1,-1), 0.5, colors.black),
                ("SPAN", (1,0), (-1,0)),  # Customer Name spans rest of row
                ("SPAN", (1,1), (-1,1)),  # Account Number spans rest of row
                ("ALIGN", (2,2), (3,2), "CENTER"),  # Align From/To
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTNAME", (0,1), (-1,1), "Helvetica-Bold"),
                ("FONTNAME", (0,2), (-1,2), "Helvetica-Bold"),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 15))

            # Slip Table with Product column
            elements.append(Paragraph(f"<b>Vehicle: {vehicle}</b>", styles['Heading3']))
            elements.append(Spacer(1, 10))

            table_data = [["S.No", "Slip Date", "Slip #", "Product", "Quantity (Ltr)", "Rate", "Amount (Rs)"]]
            s_no = 1
            remaining_amount = total_amount
            total_liters = 0
            subtotal = 0

            while remaining_amount > 0:
                slip_liters = LITRES_PER_SLIP
                slip_amount = slip_liters * rate
                if slip_amount > remaining_amount:
                    slip_liters = remaining_amount / rate
                    slip_amount = remaining_amount

                table_data.append([s_no, slip_date, slip_no, "HSD", round(slip_liters,2), rate, f"{slip_amount:,.2f}"])
                total_liters += slip_liters
                subtotal += slip_amount
                remaining_amount -= slip_amount
                slip_no += 1
                s_no += 1

            table_data.append(["", "", "", "Total", round(total_liters,2), "", f"{subtotal:,.2f}"])

            slip_table = Table(table_data, colWidths=[40, 70, 70, 60, 80, 60, 80])
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
            elements.append(PageBreak())
            invoice_number += 1

        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        st.download_button(
            label="Download Combined Invoice PDF",
            data=buffer,
            file_name="Combined_Invoices.pdf",
            mime="application/pdf"
        )
        st.success("Combined PDF with summary, account number, billing period, and all vehicles generated successfully!")
