from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import json

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here' # Change this in production

DATABASE = 'database/finance.db'

def get_db():
    db = getattr(get_db, '_db', None)
    if db is None:
        db = get_db._db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # Return rows as dictionary-like objects
    return db

@app.teardown_appcontext
def close_db(error):
    db = getattr(get_db, '_db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Create schema.sql if it doesn't exist
try:
    with open('backend/schema.sql', 'x') as f:
        f.write("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    salary REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    date TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS savings_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    goal_name TEXT NOT NULL,
    target_amount REAL NOT NULL,
    months INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
""")
except FileExistsError:
    pass

# Initialize the database on first run if it doesn't exist
with app.app_context():
    if not __import__('os').path.exists(DATABASE):
        print("Initializing database...")
        init_db()
        print("Database initialized.")


# --- Authentication Routes ---

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('fullName')
    email = data.get('email')
    password = data.get('password')
    salary = data.get('monthlySalary', 0.0) # Default to 0.0 if not provided

    if not all([name, email, password]):
        return jsonify({'message': 'All fields are required'}), 400

    hashed_password = generate_password_hash(password)
    db = get_db()
    try:
        db.execute('INSERT INTO users (name, email, password, salary) VALUES (?, ?, ?, ?)',
                   (name, email, hashed_password, salary))
        db.commit()
        return jsonify({'message': 'User created successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Email already exists'}), 409
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'message': 'An error occurred during signup'}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'message': 'Email and password are required'}), 400

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['user_salary'] = user['salary']
        return jsonify({'message': 'Login successful', 'user': {'id': user['id'], 'name': user['name'], 'email': user['email'], 'salary': user['salary']}})
    else:
        return jsonify({'message': 'Invalid email or password'}), 401

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful'})

# --- Expense Routes ---

@app.route('/expenses', methods=['GET', 'POST'])
def handle_expenses():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    user_id = session['user_id']
    db = get_db()

    if request.method == 'POST':
        data = request.get_json()
        description = data.get('description')
        category = data.get('category')
        amount = data.get('amount')
        date = data.get('date') # Expecting YYYY-MM-DD format

        if not all([description, category, amount, date]):
            return jsonify({'message': 'All expense fields are required'}), 400

        try:
            amount = float(amount)
            datetime.datetime.strptime(date, '%Y-%m-%d') # Validate date format
            db.execute('INSERT INTO expenses (user_id, description, category, amount, date) VALUES (?, ?, ?, ?, ?)',
                       (user_id, description, category, amount, date))
            db.commit()
            return jsonify({'message': 'Expense added successfully'}), 201
        except ValueError:
            return jsonify({'message': 'Invalid amount or date format'}), 400
        except Exception as e:
            print(f"Add expense error: {e}")
            return jsonify({'message': 'An error occurred while adding expense'}), 500

    else: # GET request
        try:
            expenses = db.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC', (user_id,)).fetchall()
            # Convert Row objects to dictionaries
            expenses_list = [dict(row) for row in expenses]
            return jsonify(expenses_list), 200
        except Exception as e:
            print(f"Get expenses error: {e}")
            return jsonify({'message': 'An error occurred while fetching expenses'}), 500

# --- Dashboard Data Route ---
@app.route('/dashboard_data')
def dashboard_data():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    user_id = session['user_id']
    db = get_db()

    try:
        # User data
        user = db.execute('SELECT salary FROM users WHERE id = ?', (user_id,)).fetchone()
        monthly_salary = user['salary'] if user else 0.0

        # Total Expenses
        total_expenses_row = db.execute('SELECT SUM(amount) as total FROM expenses WHERE user_id = ?', (user_id,)).fetchone()
        total_expenses = float(total_expenses_row['total']) if total_expenses_row and total_expenses_row['total'] is not None else 0.0

        # Net Savings
        net_savings = monthly_salary - total_expenses

        # Savings Rate
        savings_rate = (net_savings / monthly_salary) * 100 if monthly_salary > 0 else 0.0

        # Recent Expenses
        recent_expenses = db.execute('SELECT description, category, amount, date FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT 5', (user_id,)).fetchall()
        recent_expenses_list = [dict(row) for row in recent_expenses]

        # Spending Breakdown (by category)
        spending_breakdown_rows = db.execute('SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category', (user_id,)).fetchall()
        spending_breakdown = {row['category']: float(row['total']) for row in spending_breakdown_rows}

        return jsonify({
            'monthlyIncome': round(monthly_salary, 2),
            'totalExpenses': round(total_expenses, 2),
            'netSavings': round(net_savings, 2),
            'savingsRate': round(savings_rate, 2),
            'recentExpenses': recent_expenses_list,
            'spendingBreakdown': spending_breakdown
        })

    except Exception as e:
        print(f"Dashboard data error: {e}")
        return jsonify({'message': 'An error occurred while fetching dashboard data'}), 500

# --- Savings Goals Routes ---
@app.route('/savings_goals', methods=['GET', 'POST'])
def handle_savings_goals():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    user_id = session['user_id']
    db = get_db()

    if request.method == 'POST':
        data = request.get_json()
        goal_name = data.get('goal_name')
        target_amount = data.get('target_amount')
        months = data.get('months')

        if not all([goal_name, target_amount, months]):
            return jsonify({'message': 'All savings goal fields are required'}), 400

        try:
            target_amount = float(target_amount)
            months = int(months)
            if target_amount <= 0 or months <= 0:
                return jsonify({'message': 'Target amount and months must be positive'}), 400

            db.execute('INSERT INTO savings_goals (user_id, goal_name, target_amount, months) VALUES (?, ?, ?, ?)',
                       (user_id, goal_name, target_amount, months))
            db.commit()
            return jsonify({'message': 'Savings goal added successfully'}), 201
        except ValueError:
            return jsonify({'message': 'Invalid amount or months format'}), 400
        except Exception as e:
            print(f"Add savings goal error: {e}")
            return jsonify({'message': 'An error occurred while adding savings goal'}), 500

    else: # GET request
        try:
            goals = db.execute('SELECT * FROM savings_goals WHERE user_id = ?', (user_id,)).fetchall()
            goals_list = [dict(row) for row in goals]
            return jsonify(goals_list), 200
        except Exception as e:
            print(f"Get savings goals error: {e}")
            return jsonify({'message': 'An error occurred while fetching savings goals'}), 500

# --- Profile Routes ---
@app.route('/profile_data')
def get_profile_data():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    user_id = session['user_id']
    db = get_db()
    try:
        user = db.execute('SELECT name, email, salary FROM users WHERE id = ?', (user_id,)).fetchone()
        if user:
            return jsonify({
                'userName': user['name'],
                'email': user['email'],
                'monthlySalary': round(user['salary'], 2)
            })
        else:
            return jsonify({'message': 'User not found'}), 404
    except Exception as e:
        print(f"Get profile data error: {e}")
        return jsonify({'message': 'An error occurred fetching profile data'}), 500

@app.route('/salary', methods=['PUT'])
def update_salary():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    user_id = session['user_id']
    data = request.get_json()
    new_salary = data.get('monthlySalary')

    if new_salary is None:
        return jsonify({'message': 'Monthly salary is required'}), 400

    try:
        new_salary = float(new_salary)
        if new_salary < 0:
            return jsonify({'message': 'Salary cannot be negative'}), 400

        db = get_db()
        db.execute('UPDATE users SET salary = ? WHERE id = ?', (new_salary, user_id))
        db.commit()

        # Update session as well
        session['user_salary'] = new_salary

        return jsonify({'message': 'Salary updated successfully', 'newSalary': round(new_salary, 2)})
    except ValueError:
        return jsonify({'message': 'Invalid salary format'}), 400
    except Exception as e:
        print(f"Update salary error: {e}")
        return jsonify({'message': 'An error occurred updating salary'}), 500

# --- AI Advisory Placeholder (Not fully implemented as per strict requirement for simple suggestions) ---
# For this version, we'll just return a static message or very basic logic.
# A real AI integration would require external libraries or APIs.
@app.route('/get_financial_advice', methods=['POST'])
def get_financial_advice():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.get_json()
    total_savings = data.get('totalSavings')
    financial_goals = data.get('financialGoals')
    risk_tolerance = data.get('riskTolerance')
    investment_horizon = data.get('investmentTimeHorizon')

    advice_message = "Your plan will appear here once you fill out your profile." # Default message

    if total_savings is not None and financial_goals and risk_tolerance and investment_horizon:
        # Simple suggestion logic
        suggestions = []
        total_savings = float(total_savings)

        # Based on savings and goals
        if total_savings < 1000 and financial_goals: # Very basic check
            suggestions.append("Consider increasing your savings to meet your financial goals faster.")

        # Based on risk tolerance and horizon
        if risk_tolerance == 'Low':
            suggestions.append("For low risk tolerance, consider diversifying with bonds or stable dividend stocks.")
            if investment_horizon == 'Long-term':
                suggestions.append("Even with low risk, long-term investment can benefit from compounding.")
        elif risk_tolerance == 'Medium':
            suggestions.append("A balanced portfolio with a mix of stocks and bonds is often suitable for medium risk.")
            if investment_horizon == 'Short-term':
                suggestions.append("For short-term goals with medium risk, focus on less volatile assets.")
        elif risk_tolerance == 'High':
            suggestions.append("High risk tolerance allows for potentially higher growth investments like growth stocks or emerging market funds.")
            if investment_horizon == 'Short-term':
                suggestions.append("Be mindful of volatility for short-term horizons, even with high risk tolerance.")

        if not suggestions:
            advice_message = "Review your inputs. Based on your profile, we recommend consulting a financial advisor for a detailed plan."
        else:
            advice_message = "Here's a personalized plan based on your input:\n\n" + "\n".join([f"- {s}" for s in suggestions]) + "\n\nRemember, this is a simplified suggestion. Consult a financial professional for tailored advice."
    else:
         advice_message = "Please fill out your financial profile to get a personalized plan."


    return jsonify({'personalizedPlan': advice_message})

# --- Serve HTML Files ---
# Catch-all for HTML pages that will be served statically
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('dashboard.html')

@app.route('/expenses')
def expenses_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('expenses.html')

@app.route('/savings')
def savings_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('savings.html')

@app.route('/advisory')
def advisory_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('advisory.html')

@app.route('/profile')
def profile_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('profile.html')

if __name__ == '__main__':
    # Ensure the database directory exists
    import os
    if not os.path.exists('database'):
        os.makedirs('database')
    app.run(debug=True)
