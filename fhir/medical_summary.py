from textwrap import wrap

from django.apps import apps
from django.utils import timezone

from patients.models import PatientProfile


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT_MARGIN = 54
TOP_MARGIN = 740
LINE_HEIGHT = 16
BOTTOM_MARGIN = 54
WRAP_WIDTH = 88
CORE_RESOURCE_LABELS = {
    "Allergies",
    "Conditions",
    "Medications",
}
EXCLUDED_RESOURCE_MODEL_LABELS = {
    "fhir.fhirlink",
    "fhir.fhirresourcesnapshot",
}
EXCLUDED_DETAIL_FIELDS = {
    "id",
    "patient",
    "created_at",
    "updated_at",
    "raw_json",
    "validation_errors",
    "checksum",
}


def patient_resource_sections(patient):
    sections = []
    for model in apps.get_models():
        if model._meta.label_lower in EXCLUDED_RESOURCE_MODEL_LABELS:
            continue
        try:
            field = model._meta.get_field("patient")
        except Exception:
            continue
        if getattr(field, "remote_field", None) is None:
            continue
        if field.remote_field.model is not PatientProfile:
            continue
        records = list(model.objects.filter(patient=patient).order_by("pk"))
        sections.append((model._meta.verbose_name_plural.title(), records))
    return sorted(sections, key=lambda row: row[0])


def build_patient_medical_summary_pdf(patient, summary_options=None):
    lines = medical_summary_lines(patient, summary_options=summary_options)
    pages = paginate_lines(wrap_pdf_lines(lines))
    return render_simple_pdf(pages)


def medical_summary_lines(patient, summary_options=None):
    summary_options = summary_options or {}
    generated_at = (
        timezone.localtime(timezone.now())
        .strftime("%b. %d, %Y, %I:%M %p")
        .replace(" 0", " ")
    )

    address_parts = [
        patient.address_line_1,
        patient.address_line_2,
        patient.city,
        patient.state,
        patient.postal_code,
        patient.country,
    ]
    address = ", ".join(part for part in address_parts if part)

    lines = [
        f"Medical Summary: {patient}",
        f"Generated: {generated_at}",
        "",
        "Patient",
        f"Name: {patient}",
        f"Date of birth: {patient.date_of_birth or '-'}",
        f"Sex at birth: {patient.sex_at_birth or '-'}",
        f"Gender identity: {patient.gender_identity or '-'}",
        f"Phone: {patient.phone or '-'}",
        f"Email: {patient.email or '-'}",
        f"Address: {address or '-'}",
        "",
        "Medical Info",
        f"Blood type: {patient.blood_type or '-'}",
        f"Organ donor: {'Yes' if patient.organ_donor else 'No'}",
        "",
        "Emergency Contact",
        f"Name: {patient.emergency_contact_name or '-'}",
        f"Phone: {patient.emergency_contact_phone or '-'}",
        f"Relationship: {patient.emergency_contact_relationship or '-'}",
        "",
        "Selected Patient Resources",
    ]

    selected_sections, other_sections = selected_resource_sections(
        patient, summary_options
    )
    if selected_sections:
        append_resource_sections(lines, selected_sections)
    else:
        lines.append("No selected resource sections were included.")

    if summary_options.get("include_everything_else"):
        lines.extend(["", "Everything Else"])
        if other_sections:
            append_resource_sections(lines, other_sections)
        else:
            lines.append("No additional linked patient resources found.")

    lines.extend(
        [
            "",
            "Note",
            "This summary is intended for human review. It is not a complete machine-readable FHIR export.",
        ]
    )
    return lines


def selected_resource_sections(patient, summary_options):
    include_labels = set()
    if summary_options.get("include_allergies"):
        include_labels.add("Allergies")
    if summary_options.get("include_conditions"):
        include_labels.add("Conditions")
    if summary_options.get("include_medications"):
        include_labels.add("Medications")

    selected = []
    other = []
    for label, records in patient_resource_sections(patient):
        if label in include_labels:
            selected.append((label, records))
        elif label not in CORE_RESOURCE_LABELS and records:
            other.append((label, records))
    return selected, other


def append_resource_sections(lines, sections):
    for label, records in sections:
        lines.extend(["", label])
        if not records:
            lines.append("No records found.")
            continue
        for index, record in enumerate(records, start=1):
            lines.append(f"{index}. {record}")
            for field_label, value in record_detail_pairs(record):
                lines.append(f"   {field_label}: {value}")


def record_detail_pairs(record):
    details = []
    for field in record._meta.fields:
        if field.name in EXCLUDED_DETAIL_FIELDS:
            continue
        value = getattr(record, field.name, None)
        if is_empty_value(value):
            continue
        details.append((field.verbose_name.title(), format_detail_value(value)))
    return details


def is_empty_value(value):
    return value is None or value == "" or value == [] or value == {}


def format_detail_value(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if hasattr(value, "pk"):
        return str(value)
    text = str(value).replace("\r\n", " ").replace("\n", " ")
    if len(text) > 240:
        return f"{text[:237]}..."
    return text


def wrap_pdf_lines(lines):
    wrapped = []
    for line in lines:
        if not line:
            wrapped.append(line)
            continue
        indent = len(line) - len(line.lstrip(" "))
        continuation = " " * indent
        wrapped.extend(
            wrap(
                line,
                width=WRAP_WIDTH,
                subsequent_indent=continuation,
                break_long_words=False,
                break_on_hyphens=False,
            )
            or [line]
        )
    return wrapped


def paginate_lines(lines):
    pages = []
    current = []
    max_lines = int((TOP_MARGIN - BOTTOM_MARGIN) / LINE_HEIGHT)
    for line in lines:
        if len(current) >= max_lines:
            pages.append(current)
            current = []
        current.append(line)
    if current:
        pages.append(current)
    return pages or [[""]]


def render_simple_pdf(pages):
    objects = []
    catalog_id = add_object(objects, "<< /Type /Catalog /Pages 2 0 R >>")
    page_tree_id = add_object(objects, "")
    font_id = add_object(
        objects, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    )
    page_ids = []

    for page_lines in pages:
        content = render_page_content(page_lines)
        stream = (
            f"<< /Length {len(content.encode('latin-1'))} >>\n"
            f"stream\n{content}\nendstream"
        )
        content_id = add_object(objects, stream)
        page_id = add_object(
            objects,
            f"<< /Type /Page /Parent {page_tree_id} 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>",
        )
        page_ids.append(page_id)

    objects[page_tree_id - 1] = (
        page_tree_id,
        f"<< /Type /Pages /Kids [{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] /Count {len(page_ids)} >>",
    )

    pdf = "%PDF-1.4\n"
    offsets = []
    for object_id, body in objects:
        offsets.append(len(pdf.encode("latin-1")))
        pdf += f"{object_id} 0 obj\n{body}\nendobj\n"
    xref_offset = len(pdf.encode("latin-1"))
    pdf += f"xref\n0 {len(objects) + 1}\n"
    pdf += "0000000000 65535 f \n"
    for offset in offsets:
        pdf += f"{offset:010d} 00000 n \n"
    pdf += (
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )
    return pdf.encode("latin-1")


def add_object(objects, body):
    object_id = len(objects) + 1
    objects.append((object_id, body))
    return object_id


def render_page_content(lines):
    commands = ["BT", "/F1 11 Tf", f"1 0 0 1 {LEFT_MARGIN} {TOP_MARGIN} Tm"]
    first = True
    for line in lines:
        if not first:
            commands.append(f"0 -{LINE_HEIGHT} Td")
        first = False
        commands.append(f"({escape_pdf_text(line)}) Tj")
    commands.append("ET")
    return "\n".join(commands)


def escape_pdf_text(value):
    return (
        str(value)
        .encode("latin-1", "replace")
        .decode("latin-1")
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )
