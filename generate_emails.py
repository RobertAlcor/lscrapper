import csv
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

template_dir = Path(__file__).parent / "app" / "email_templates"
env = Environment(loader=FileSystemLoader(str(template_dir)))
templates = {
    'Erstansprache': 'first_contact.txt',
    'Follow-Up':     'follow_up.txt',
    'Abschluss':     'closing.txt',
}

csv_dir  = Path(__file__).parent / "output"
csv_file = next(csv_dir.glob("leads-*.csv"), None)
if not csv_file:
    print("Keine Leads-CSV im /output-Ordner gefunden.")
    exit(1)

with open(csv_file, newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    for idx, row in enumerate(reader):
        print(f"\n=== Lead #{idx+1}: {row['Firma']} ===\n")
        for name, fname in templates.items():
            tpl = env.get_template(fname)
            email = tpl.render(
                contact_name     = row.get('Firma',''),
                company          = row.get('Firma',''),
                service          = "professionelle Webdesign- und SEO-Lösungen",
                your_name        = "Robert Alchimowicz",
                your_company     = "EliteSites | Webdesign-Alcor",
                industry         = "Webdesign & SEO",
                city             = row.get('Ort',''),
                benefit          = "Ihre Anfragen um 20 % steigern",
                booking_link     = "https://calendly.com/elitesites",
                unsubscribe_link = "mailto:office@elitesites.at",
                contact_id       = f"{csv_file.name}-{idx}"
            )
            subject = email.splitlines()[0].replace("Betreff: ","")
            print(f"--- {name} ---")
            print(f"Subject: {subject}\n{email}\n" + "-"*60 + "\n")
