# 🍽️ Cafeteria Pre-Order System

A web-based application that allows students to pre-order meals from the school cafeteria, reducing waiting time, improving efficiency, and enabling better food management.

---

## 🚀 Features

* 🔐 **Secure User Authentication**

  * Login & registration using hashed passwords (Scrypt/Werkzeug)

* 🛒 **Smart Cart System**

  * Add, remove, increase, or decrease item quantities
  * Real-time total calculation

* 🧾 **Automated PDF Invoice Generation**

  * Generates e-bill with order details
  * Downloadable receipt after checkout

* 🆔 **Order Management**

  * Unique Order ID and Token Number for each order
  * Used for food collection

* 🧑‍🍳 **Cafeteria Dashboard**

  * Staff can view and manage orders
  * Mark orders as delivered

* ☁️ **Persistent Database (MongoDB)**

  * No data loss on restart
  * Supports multiple users and scalability

---

## 🏗️ Tech Stack

### Frontend

* HTML
* CSS
* Jinja2 Templates

### Backend

* Python
* Flask

### Database

* MongoDB (via PyMongo)

### Other Libraries

* ReportLab (for PDF generation)
* Werkzeug (for authentication security)

---

## 📁 Project Structure

```
preorder_app/
│
├── run.py
├── requirements.txt
├── wsgi.py
│
├── app/
│   ├── __init__.py
│   ├── db.py
│   ├── routes/
│   ├── services/
│   └── utils/
│
├── templates/
├── static/
└── data/ (legacy - no longer used)
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/preorder-app.git
cd preorder-app
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables

```bash
export MONGO_URI=your_mongodb_connection_string
export DB_NAME=cafeteria_app
export SECRET_KEY=your_secret_key
```

(For Windows, use `set` instead of `export`)

### 4. Run the Application

```bash
python run.py
```

---

## 🌐 Deployment

The app can be deployed using platforms like:

* Render
* Railway
* Heroku (with MongoDB Atlas)

---

## 🧠 How It Works

1. Users register/login securely
2. Browse menu and add items to cart
3. Checkout generates:

   * Order ID
   * Token Number
   * PDF Invoice
4. Order is stored in MongoDB
5. Cafeteria staff processes the order
6. Student collects food using token/invoice

---

## 🔮 Future Enhancements

* 💳 Online Payment Integration (UPI, Cards)
* 📱 Mobile App (Android/iOS)
* 🤖 AI-Based Meal Recommendations
* 📡 RFID / QR Code Pickup System
* 📊 Admin Analytics Dashboard
* 📩 Email Invoice Delivery

---

## 📌 Key Advantages

* Eliminates long queues
* Reduces food wastage
* Improves efficiency
* Enables digital record keeping
* Scalable and reliable system

---

## ⚠️ Limitations

* Requires internet connection
* Dependent on digital access for users

---

## 👨‍💻 Author

**Shaunak Mohotra**
Class XI – C

---

## 📄 License

This project is developed for educational purposes.

---

## 🙌 Acknowledgements

* Flask Documentation
* MongoDB Documentation
* ReportLab Library
* Open-source community resources

---

## ⭐ Final Note

This project demonstrates how technology can streamline everyday processes like cafeteria management by combining secure authentication, real-time ordering, and persistent cloud storage.

---
