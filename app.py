from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + \
    os.path.join(basedir, 'employees.db')
app.config['JWT_SECRET_KEY'] = 'dev@123'
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_USERNAME'] = 'e5072aa7fe44c0'
app.config['MAIL_PASSWORD'] = '55144b23712606'


db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('db_create')
def database_create():
    db.create_all()
    print("Database created")


@app.cli.command('db_drop')
def database_drop():
    db.drop_all()
    print("Database droppped")


@app.cli.command('db_seed')
def database_seed():
    krishna = Employee(employee_name='Krishna',
                       employee_type='permanent', employee_id=1, salary=89999,
                       address='Vaikunta 12345', tax_class='A', email_id='krishna@gmail.com'
                       )
    shiva = Employee(employee_name='Shiva',
                     employee_type='permanent', employee_id=2, salary=89999,
                     address='Kailaasa 12345', tax_class='A', email_id="shiva@gmail.com"
                     )
    bramha = Employee(employee_name='Bramha',
                      employee_type='permanent', employee_id=3, salary=89999,
                      address='Sky 12345', tax_class='A', email_id="bramha@gmail.com"
                      )
    db.session.add(krishna)
    db.session.add(shiva)
    db.session.add(bramha)

    dev_user = User(first_name='Arunachala',
                    last_name='Shiva',
                    email='ac@dev.com',
                    password='P@ssw0rd')
    db.session.add(dev_user)
    db.session.commit()
    print("Datbase seeded")


@app.route("/employees", methods=['GET'])
def employees():
    employees_list = Employee.query.all()
    result = employees_schema.dump(employees_list)
    return jsonify(result)


@app.route("/employees/<int:employee_id>", methods=['GET'])
def employee_details(employee_id: int):
    employee = Employee.query.filter_byt(employee_id=employee_id).first()
    if employee:
        result = employee_schema.dump(employee)
        return jsonify(result)
    else:
        return jsonify(message="Employee doesnot exist")


@app.route("/employees", methods=['POST'], endpoint='add_employee')
@jwt_required()
def add_employee():
    email_id = request.form['email_id']
    employee = Employee.query.filter_by(email_id=email_id).first()
    if employee:
        return "Employee already exists with the same mail id"
    else:
        employee_name = request.form['employee_name']
        employee_type = request.form['employee_type']
        tax_class = request.form['tax_class']
        salary = float(request.form['salary'])
        address = request.form['address']

        new_employee = Employee(email_id=email_id, employee_name=employee_name, employee_type=employee_type,
                                tax_class=tax_class, salary=salary, address=address)
        db.session.add(new_employee)
        db.session.commit()
        return jsonify(message="Employee added succsesfully"), 201


@app.route("/employees", methods=['PUT'], endpoint='update_employee')
@jwt_required()
def update_employee():
    employee_id = request.form['employee_id']
    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if employee:
        employee.employee_name = request.form['employee_name']
        employee.employee_type = request.form['employee_type']
        employee.salary = float(request.form['salary'])
        employee.tax_class = request.form['tax_class']
        employee.address = request.form['address']
        employee.email_id = request.form['email_id']
        db.session.commit()
        return jsonify(message="Employee updated succsesfully"), 202
    else:
        return jsonify(message="Employee doesnot exist"), 404


@app.route("/employees/<int:employee_id>", methods=['DELETE'], endpoint='delete_employee')
@jwt_required()
def delete_employee(employee_id: int):
    employee_id = int(request.form['employee_id'])
    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if employee:
        db.session.delete(employee)
        db.session.commit()
        return jsonify(message="Employee deleted succsesfully"), 202
    else:
        return jsonify(message="Employee doesnot exist"), 404


@app.route("/signup", methods=['POST'])
def signup():
    email = request.form['email']
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify(message='You signed up already with the email'), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        new_user = User(first_name=first_name, last_name=last_name,
                        email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(message="User created succesfully"), 201


@app.route("/login", methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']
    user = User.query.filter_by(email=email, password=password).first()
    if user:
        access_token = create_access_token(identity=email)
        return jsonify(message="Login succeeded", access_token=access_token)
    else:
        return jsonify(message="Wrong email or password"), 401


@app.route("/retrieve_password/<string:email>", methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message("your employee api password is" + user.password,
                      sender="admin@employee-api.com",
                      recipients=[email])
        mail.send(msg)
        return jsonify(message="Password sent to " + email)
    else:
        return jsonify(message="That email doesn't exist"), 401


# Database models:


class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Employee(db.Model):
    __tablename__ = 'employees'
    employee_id = Column(Integer, primary_key=True)
    employee_name = Column(String)
    employee_type = Column(String)
    salary = Column(Float)
    address = Column(String)
    tax_class = Column(String)
    email_id = Column(String)


# Database schema:
class UserSchema(ma.Schema):
    class Meta:
        fields = ['id', 'first_name', 'last_name', 'email', 'password']


class EmployeeSchema(ma.Schema):
    class Meta:
        fields = ['employee_id', 'employee_name',
                  'employee_type', 'salary', 'address', 'tax_class', 'email_id']


user_schema = UserSchema()
users_schema = UserSchema(many=True)

employee_schema = EmployeeSchema()
employees_schema = EmployeeSchema(many=True)

if __name__ == '__main__':
    app.run(debug=True)
