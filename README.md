🛍️ Multi-Vendor E-commerce System
📌 Project Description
The Multi-Vendor E-commerce System is a full-featured online marketplace platform that enables multiple vendors to register, manage their own product listings, and process customer orders independently. The system is designed to replicate real-world e-commerce platforms like Amazon, Flipkart, or Etsy, offering a seamless shopping experience for customers and robust management tools for vendors and admins.

This project is built with a modular architecture using Django REST Framework on the backend, with optional frontend support via React or Next.js. It includes JWT-based authentication, role-based access control, dynamic product filtering, real-time order processing, and Stripe payment integration.

🎯 Key Features
👤 User Roles
Admin: Manages platform users, vendor approvals, products, and orders.

Vendor: Manages own product catalog, pricing, and order fulfillment.

Customer: Browses products, adds items to cart, places orders, and makes payments.

🛒 Product & Order Management
Vendors can create, update, and delete their products.

Customers can filter products by category, search, and view details.

Authenticated users can manage cart and place orders.

Orders notify both vendor and customer on confirmation.

💳 Payment System
Secure checkout via Stripe.

Orders update upon successful payment.

Invoice generation and email notifications supported.

📊 Dashboards
Admin Dashboard: Oversee all activity, generate reports, and view sales data.

Vendor Dashboard: View sales stats, manage inventory, and monitor orders.

🧰 Tech Stack
Backend: Django, Django REST Framework

Authentication: JWT via djangorestframework-simplejwt

Database:  SQLite 
