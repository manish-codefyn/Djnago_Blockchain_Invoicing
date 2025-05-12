# 🧾 Blockchain Invoicing System

A secure, modern, and professional invoicing system powered by Django and integrated with blockchain technology to ensure tamper-proof records and high transparency.

## 👤 Author

**Manish Sharma**

---

## 🚀 Features

- 🔐 Blockchain-powered invoice verification
- 📑 Generate PDF invoices
- 📬 Email invoices to clients
- 📊 Reporting & analytics (monthly, client-based, etc.)
- 💰 Tax & discount calculations
- 🧾 Payment status tracking
- 📥 Export reports to Excel

---

## 📂 Project Structure

Blockchain-Invoicing/
├── invoices/ # Main app
├── blockchain/ # Blockchain logic
├── templates/ # HTML templates
├── static/ # Static files (CSS, JS, images)
├── media/ # Uploaded media
├── utils/ # Reusable helpers (PDF, email, etc.)
├── manage.py
├── requirements.txt
└── README.md

yaml
Copy
Edit

---

## ⚙️ Installation Guide

### 1. 🧬 Clone the Repository

```bash
git clone https://github.com/manish-codefyn/Djnago_Blockchain_Invoicing.git
cd Djnago_Blockchain_Invoicing
2. 🐍 Create a Virtual Environment
bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
3. 📦 Install Requirements
bash
Copy
Edit
pip install -r requirements.txt
4. 🔧 Configuration
Rename .env.example to .env (if available).

Set your SECRET_KEY, EMAIL SETTINGS, etc. in .env.

5. 🛠️ Apply Migrations
bash
Copy
Edit
python manage.py migrate
6. 📇 Create Superuser
bash
Copy
Edit
python manage.py createsuperuser
7. 🌐 Run the Server
bash
Copy
Edit
python manage.py runserver
Now visit: http://127.0.0.1:8000/

📤 Deploying on Production (Basic)
Use Gunicorn + Nginx

Set DEBUG = False

Use HTTPS

Configure allowed hosts and environment variables securely

📌 License
This project is licensed under the MIT License.
Feel free to use, contribute, or suggest improvements!

🤝 Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

📧 Contact
For questions, feedback, or collaborations:
📨 manis.shr@gmail.com
📍 LinkedIn (www.linkedin.com/in/manish-sharma-codefyn)
