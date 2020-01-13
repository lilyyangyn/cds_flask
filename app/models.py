# -*- coding: UTF-8 -*-     
from datetime import datetime
from bcrypt import hashpw, gensalt, checkpw
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app
from . import db, login_manager


class Role:
	Customer = "customer"
	Moderator = "moderator"
	Admin = "admin"

class User(UserMixin, db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)	
	name = db.Column(db.String(16), unique=True, index=True, nullable=False)			# 姓名
	email = db.Column(db.String(64), unique=True, index=True, nullable=False)			# 邮箱地址
	phone = db.Column(db.String(16), unique=True, index=True, nullable=False)			# 联系电话
	password_hash = db.Column(db.String(128))												# 密码哈希
	created_at = db.Column(db.DateTime(), default=datetime.now())	# 创建时间
	updated_at = db.Column(db.DateTime(), default=datetime.now())	# 更新时间
	confirmed = db.Column(db.Boolean, default=False)								# 确认创建
	role = db.Column(db.Enum(Role.Customer, Role.Moderator, Role.Admin, name='role_enum'))							# 角色
	balance = db.Column(db.Integer, default=0)	# 余额
	gender = db.Column(db.String(8))						# 性别
	faculty = db.Column(db.String(20))					# 学院
	identity = db.Column(db.String(8))					# 在校身份
	deposits = db.relationship('Deposit', backref='user', lazy='dynamic')
	orders = db.relationship('Order', backref='user', lazy='dynamic')

	@staticmethod
	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)
		# role of user should not be explicitly set when created. 
		# If the user is determed admin (by checking the config), then set the role as 'admin', otherwise, 'customer'
		if self.role is None:
			if self.email == current_app.config['CDS_ADMIN']:
				self.role = Role.Admin
			else:
				self.role = Role.Customer

	@property
	def password(self):
		# not allow password to be read
		raise AttributeError('password is not a readable attribute!')

	@password.setter
	def password(self, password):
		# set the password
		self.password_hash = hashpw(password, gensalt(12))

	def varify_password(self, password):
		return checkpw(password.encode('utf'), self.password_hash.encode('utf'))

	def can_admin(self):
		# has admin privilege
		return self.role == Role.Admin

	def can_moderate(self):
		# has moderator/admin privilege
		return self.role == Role.Admin or self.role == Role.Moderator

	def generate_confirmation_token(self, expiration=3600):
		# generate token, which includes user_id as identifier
		# the token will be expired in {{expiration}} seconds
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		# Generates an encrypted signature, and serializes data and signature
		return s.dumps({'confirm': self.id}).decode('utf-8')

	def confirm(self, tokem):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			# will first check the signature and expiration time
			data = s.loads(token.encode('utf-8'))
		except:
			return False
		if data.get('confirm') != self.id:
			# logged-in user can only confirm the account of himself
			return False
		self.confirmed = True
		self.updated_at = datetime.now()
		db.session.add(self)
		return True

	def generate_reset_token(self, expiration=3600):
		# generate token, which includes user_id as identifier
		# the token will be expired in {{expiration}} seconds
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		# Generates an encrypted signature, and serializes data and signature
		return s.dumps({'reset': self.id}).decode('utf-8')

	@staticmethod
	def reset_password(token, new_password):
		# get user id
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token.encode('utf8'))
		except:
			return False
		user = User.query.filter_by(data.get('reset'))
		# update password
		if user is None:
			return False
		user.password = new_password
		user.updated_at = datetime.now()
		db.session.add(user)
		return True

	def generate_email_change_token(self, new_email, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'change_email': self.id, 'new_email': new_email}).decode('utf-8')

	def change_email(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token.encode('utf-8'))
		except:
			return False
		# logged-in user can only confirm the account of himself
		if data.get('change_email') != self.id:
			return False
		new_email = data.get('new_email')
		if new_email is None:
			return False
		# fail if new_email already registered
		if User.query.filter_by(email=new_email).first() is not None:
			return False
		# update email
		self.email = new_email
		self.updated_at = datetime.now()
		db.session.add(self)
		return True

	@property
	def is_VIP(self):
		return self.balance > 0


class AnonymousUser(AnonymousUserMixin):
	def can_admin(self):
		return false

	def can_moderate(self):
		return false

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



class Spiciness:
	NotSpicy = 0
	LittleSpicy = 1
	MediumSpicy = 2
	Spicy = 3
	VerySpicy = 4
	ExtraSpicy = 5

class Dish(db.Model):
	__tablename__ = 'dishes'
	id = db.Column(db.Integer, primary_key=True)
	restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
	name = db.Column(db.String(64), unique=True)
	english_name = db.Column(db.String(64), unique=True)
	price = db.Column(db.Integer)
	original_price=db.Column(db.Integer)
	spiciness = db.Column(db.Integer)
	large_img_url = db.Column(db.String(80))
	created_at = db.Column(db.DateTime(), default=datetime.now())
	in_supply = db.Column(db.Boolean, default=False)
	stock = db.Column(db.Integer, default=0, index=True)
	Sunday = db.Column(db.Boolean, default=False)
	Monday = db.Column(db.Boolean, default=False)
	Tuesday = db.Column(db.Boolean, default=False)
	Wednesday = db.Column(db.Boolean, default=False)
	Thursday = db.Column(db.Boolean, default=False)
	Friday = db.Column(db.Boolean, default=False)
	Saturday = db.Column(db.Boolean, default=False)
	orders = db.relationship('Order', backref='dish', lazy='dynamic')

	@property
	def sold_out(self):
		return self.stock < 1

	def clear_stock(self):
		self.stock = 0

	def set_stock(self, amount):
		self.stock += amount

	def is_available(self, day, hour, is_vip=False):
		if not self.in_supply:
			return False;
		if hour < 12:
			# before 11 am
			if day == 1:
				return self.Monday
			elif day == 2:
				return self.Tuesday
			elif day == 3:
				return self.Wednesday
			elif day == 4:
				return self.Thursday
			elif day == 5:
				return self.Friday
			elif day == 6:
				return self.Saturday
			elif day == 7:
				return self.Sunday
		elif hour > 20:
			# after 9 pm
			if is_vip:
				# available only to vip
				if day == 7:
					return self.Monday
				elif day == 1:
					return self.Tuesday
				elif day == 2:
					return self.Wednesday
				elif day == 3:
					return self.Thursday
				elif day == 4:
					return self.Friday
				elif day == 5:
					return self.Saturday
				elif day == 6:
					return self.Sunday
			else:
				return False
		else:
			return False

	def add_available_day(self, day):
		if day == 1:
			self.Monday = True
		elif day == 2:
			self.Tuesday = True
		elif day == 3:
			self.Wednesday = True
		elif day == 4:
			self.Thursday = True
		elif day == 5:
			self.Friday = True
		elif day == 6:
			self.Saturday = True
		elif day == 7:
			self.Sunday = True

	def cancel_available_day(self, day):
		if day == 1:
			self.Monday = False
		elif day == 2:
			self.Tuesday = False
		elif day == 3:
			self.Wednesday = False
		elif day == 4:
			self.Thursday = False
		elif day == 5:
			self.Friday = False
		elif day == 6:
			self.Saturday = False
		elif day == 7:
			self.Sunday = False

	def stop_serving(self):
		self.stock = 0
		self.Monday = False
		self.Tuesday = False
		self.Wednesday = False
		self.Thursday = False
		self.Friday = False
		self.Saturday = False
		self.Sunday = False
		self.in_supply = False

	@staticmethod
	def clear_all_stocks():
		# set all stock to zero
		available = Dish.query.filter(Dish.stock>0)
		if available is not None:
			for dish in available:
				dish.clear_stock()
				db.session.add(dish)

	@staticmethod
	def set_all_stock(dishes, amount):
		# set all stock to amount
		for dish in dishes:
			dish.set_stock(amount)
			db.session.add(dish)

	@staticmethod
	def update_to_next_day():
		# update the menu to next day
		Dish.clear_all_stocks()
		today = datetime.now().isoweekday()
		if today == 1:
			dishes_next_day = Dish.query.filter_by(Tuesday=True)
		elif today == 2:
			dishes_next_day = Dish.query.filter_by(Wednesday=True)
		elif today == 3:
			dishes_next_day = Dish.query.filter_by(Thursday=True)
		elif today == 4:
			dishes_next_day = Dish.query.filter_by(Friday=True)
		else:
			# for Friday to Sunday, the next menu is Monday's menu
			dishes_next_day = Dish.query.filter_by(Monday=True)
		Dish.set_all_stock(dishes_next_day, 8)



class Restaurant(db.Model):
	__tablename__ = 'restaurants'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), nullable=False, unique=True)
	img_url = db.Column(db.String(80))
	info = db.Column(db.Text())
	in_cooperation = db.Column(db.Boolean, default=True)
	dishes = db.relationship('Dish', backref='restaurant', lazy='dynamic')



class Spot(db.Model):
	__tablename__ = 'spots'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), nullable=False, unique=True)
	img_url = db.Column(db.String(80))
	description = db.Column(db.Text())
	in_use = db.Column(db.Boolean, default=True)
	orders = db.relationship('Order', backref='spot', lazy='dynamic')



class Deposit(db.Model):
	__tablename__ = 'deposits'
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	amount = db.Column(db.Integer, nullable=False)
	created_at = db.Column(db.DateTime(), default=datetime.now())



class Order_Status:
	PaidOff = 0
	ToPay = 1
	Cancelled = 2

class Order(db.Model):
	__tablename__ = 'orders'
	id = db.Column(db.Integer, primary_key=True)
	dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
	spot_id = db.Column(db.Integer, db.ForeignKey('spots.id'))
	to_be_paid = db.Column(db.Integer, nullable=False)
	today_id = db.Column(db.String(16))
	status = db.Column(db.Integer, default=Order_Status.ToPay)
	price_sold = db.Column(db.Integer, nullable=False)
	original_price = db.Column(db.Integer, nullable=False)
	created_at = db.Column(db.DateTime(), default=datetime.now())

	@staticmethod
	def __init__(self, **kwargs):
		super(Order, self).__init__(**kwargs)





